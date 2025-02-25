import sys
import argparse
import logging
from importlib import reload

from benchmark_table_creator import XlsxBenchmarkTable
from accuracy_table_creator import XlsxAccuracyTable


def cli_argument_parser():
    logging.info('START: build_parser()')

    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--tables',
                        type=str,
                        help='Paths to the inference tables in csv format.',
                        nargs='+',
                        required=True)

    parser.add_argument('-r', '--result_table',
                        type=str,
                        help='Full name of the resulting file',
                        required=True)

    parser.add_argument('-k', '--table_kind',
                        type=str, help='Kind of table: ',
                        choices=['benchmark', 'accuracy_checker'],
                        default='benchmark')

    paths_table_csv = parser.parse_args().tables
    path_table_xlsx = parser.parse_args().result_table
    table_kind = parser.parse_args().table_kind

    logging.info(f'FINISH: build_parser(). Output: {paths_table_csv}, {path_table_xlsx}, {table_kind}')
    return paths_table_csv, path_table_xlsx, table_kind


def convert_csv_table_to_xlsx(paths_table_csv, path_table_xlsx, table_type):
    logging.info('START: convert_csv_table_to_xlsx()')

    if table_type == 'benchmark':
        table_xlsx = XlsxBenchmarkTable(paths_table_csv, path_table_xlsx)
    elif table_type == 'accuracy_checker':
        table_xlsx = XlsxAccuracyTable(paths_table_csv, path_table_xlsx)
    else:
        raise ValueError(f'Incorrect value of the table type "{table_type}"')

    table_xlsx.read_csv_table()
    table_xlsx.create_table_header()
    table_xlsx.create_table_rows()
    table_xlsx.write_test_results()
    table_xlsx.beautify_table()
    table_xlsx.close_table()

    logging.info('FINISH: convert_csv_table_to_xlsx()')


def main():
    reload(logging)
    logging.basicConfig(stream=sys.stdout,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)

    paths_table_csv, path_table_xlsx, table_type = cli_argument_parser()

    try:
        convert_csv_table_to_xlsx(paths_table_csv, path_table_xlsx, table_type)
    except ValueError as ex:
        logging.error(f'{ex}')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
