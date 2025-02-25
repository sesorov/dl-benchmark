import abc


class IOModelWrapper:
    @abc.abstractmethod
    def get_input_layer_names(self, model):
        pass

    @abc.abstractmethod
    def get_input_layer_shape(self, model, layer_name):
        pass

    @abc.abstractmethod
    def get_input_layer_dtype(self, model, layer_name):
        pass


class OpenVINOIOModelWrapper(IOModelWrapper):
    def get_input_layer_names(self, model):
        names = []
        for input_ in model.inputs:
            names.append(input_.get_any_name())
        return names

    def get_input_layer_shape(self, model, node_name):
        for input_ in model.inputs:
            if node_name == input_.get_any_name():
                return input_.get_shape()
        return None

    def get_input_layer_dtype(self, model, node_name):
        from openvino.runtime.utils.types import get_dtype
        for input_ in model.inputs:
            if node_name == input_.get_any_name():
                return get_dtype(input_.get_element_type())


class IntelCaffeIOModelWrapper(IOModelWrapper):
    def get_input_layer_names(self, model):
        return model.inputs

    def get_input_layer_shape(self, model, layer_name):
        return model.blobs[layer_name].data.shape

    def get_input_layer_dtype(self, model, layer_name):
        return model.blobs[layer_name].data.dtype


class TensorFlowIOModelWrapper(IOModelWrapper):
    def __init__(self, args):
        self._shape = args.input_shape
        self._batch = args.batch_size
        self._input_name = args.input_name

    def _create_list_with_input_shape(self):
        return [self._batch, self._shape[0], self._shape[1], self._shape[2]]

    def get_input_layer_names(self, graph):
        if self._input_name:
            return self._input_name
        inputs = [x for x in graph.get_operations() if x.type == 'Placeholder']
        input_names = []
        for input_ in inputs:
            for output in input_.outputs:
                input_names.append(output.name)
        return input_names

    def get_input_layer_shape(self, graph, layer_name):
        if self._shape is None:
            try:
                shape = graph.get_tensor_by_name(layer_name).shape.as_list()
            except Exception:
                raise ValueError('Could not get the correct shape. '
                                 'Try setting the "input_shape" parameter manually.')
        else:
            shape = self._create_list_with_input_shape()
        if shape[0] is None:
            shape[0] = self._batch
        if None in shape[1:]:
            raise ValueError(f'Invalid shape {shape}. Try setting the "input_shape" parameter manually.')
        return shape

    @staticmethod
    def get_outputs_layer_names(graph, outputs_names=None):
        if outputs_names:
            return outputs_names
        nodes_map = {}
        for node in graph.as_graph_def().node:
            for parent in node.input:
                nodes_map.update({parent: nodes_map.get(parent, []) + [node.name]})
        not_outputs_types = {'Const', 'Assign', 'NoOp', 'Placeholder', 'Assert'}
        names = [
            x.name.split('import/')[-1] for x in graph.as_graph_def().node
            if x.name not in nodes_map and x.op not in not_outputs_types
        ]
        if not names:
            raise ValueError('Output blobs in the graph cannot be found')
        return names

    def get_input_layer_dtype(self, graph, layer_name):
        return graph.get_tensor_by_name(layer_name).dtype.as_numpy_dtype


class TensorFlowLiteIOModelWrapper(IOModelWrapper):
    def __init__(self, args):
        self._shape = args.input_shape
        self._batch = args.batch_size
        self._input_name = args.input_name
        self._input_info = None
        if self._shape is not None and self._input_name is not None:
            self._input_info = dict(zip(self._input_name, self._shape))
        elif self._shape is not None and self._input_name is None:
            raise ValueError('Please set both input_names and input_shapes arguments')

    def _create_list_with_input_shape(self, layer_name):
        if self._input_info is not None:
            shape = self._input_info[layer_name]
            return [self._batch, *shape]
        else:
            return [self._batch, *self._shape]

    def get_input_layer_names(self, interpreter):
        if self._input_name:
            return self._input_name
        inputs = interpreter.get_input_details()
        input_names = []
        for input_ in inputs:
            input_names.append(input_['name'])
        return input_names

    def get_input_layer_shape(self, interpreter, layer_name):
        if self._shape is None:
            try:
                inputs = interpreter.get_input_details()
                for input_ in inputs:
                    if layer_name == input_['name']:
                        shape = input_['shape']
                        break
            except Exception:
                raise ValueError('Could not get the correct shape. '
                                 'Try setting the "input_shape" parameter manually.')
        else:
            shape = self._create_list_with_input_shape(layer_name)
        shape[0] = self._batch
        if None in shape[1:]:
            raise ValueError(f'Invalid shape {shape}. Try setting the "input_shape" parameter manually.')
        return shape

    @staticmethod
    def get_outputs_layer_names(interpreter, outputs_names=None):
        if outputs_names:
            return outputs_names
        outputs = interpreter.get_output_details()
        output_names = []
        for output_ in outputs:
            output_names.append(output_['name'])
        if not output_names:
            raise ValueError('Output blobs in the graph cannot be found')
        return output_names

    def get_input_layer_dtype(self, interpreter, layer_name):
        inputs = interpreter.get_input_details()
        for input_ in inputs:
            if layer_name == input_['name']:
                return input_['dtype']
