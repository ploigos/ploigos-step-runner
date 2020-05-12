"""
TSS entry point.
TODO
"""
import sys
import argparse
import os.path

def print_error(msg):
    """
    Prints message to STDERR.
    """

    print(msg, file=sys.stderr)

def main():
    """
    TODO
    """

    parser = argparse.ArgumentParser(description='TSSC test')
    parser.add_argument(
        '-s',
        '--step',
        required=True,
        help='TSSC workflow step to run'
    )
    parser.add_argument(
        '-c',
        '--config-file',
        required=True,
        help='TSSC workflow configuration file in yml or json'
    )
    parser.add_argument(
        '-r',
        '--results-file',
        required=True,
        help='TSSC workflow results file in yml or json'
    )

    args = parser.parse_args()

    # validate args
    if not os.path.exists(args.config_file):
        print_error('specifed -c/--config-file must exist')
        sys.exit(1)

if __name__ == '__main__':
    main()
