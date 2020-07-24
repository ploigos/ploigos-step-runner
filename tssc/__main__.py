# pylint: disable=W0614,W0401

"""
TSSC entry point.
"""

import sys
import argparse
import os.path
import json
import yaml

from .factory import TSSCFactory
from .exceptions import TSSCException
from .step_implementers import *

def print_error(msg):
    """
    Prints message to STDERR.

    Parameters
    ----------
    msg : string
        Message to print as an error.
    """
    print(msg, file=sys.stderr)

def parse_yaml_or_json_file(yaml_or_json_file):
    """
    Parse YAML or JSON config file.

    Parameters
    ----------
    yaml_or_json_file : string
        Path to YAML or JSON file to load as a dictionary.

    Returns
    -------
    dict
        Dictionary parsed from given YAML or JSON file

    Raises
    ------
    ValueError
        If the given file can not be parsed as YAML or JSON.
    """
    file_contents = None
    parsed_file = None
    json_parse_error = None
    yaml_parse_error = None

    with open(yaml_or_json_file, 'r') as open_yaml_or_json_file:
        file_contents = open_yaml_or_json_file.read()

    try:
        parsed_file = json.loads(file_contents)
    except ValueError as err:
        json_parse_error = err

    if not parsed_file:
        try:
            parsed_file = yaml.safe_load(file_contents)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError, ValueError) as err:
            yaml_parse_error = err

    if json_parse_error and yaml_parse_error:
        raise ValueError('Error parsing file (' + yaml_or_json_file + ') as YAML or JSON: '
                         + "\n  JSON error: " + str(json_parse_error)
                         + "\n  YAML error: " + str(yaml_parse_error))

    return parsed_file

class ParseKeyValueArge(argparse.Action): # pylint: disable=too-few-public-methods
    """
    https://gist.github.com/fralau/061a4f6c13251367ef1d9a9a99fb3e8d
    """
    def __call__(self, parser, namespace, values, option_string=None):
        key_value_dict = {}

        if values:
            for item in values:
                split_items = item.split("=", 1)
                key = split_items[
                    0
                ].strip()  # we remove blanks around keys, as is logical
                value = split_items[1]

                key_value_dict[key] = value

        setattr(namespace, self.dest, key_value_dict)

def main(argv=None):
    """
    Main entry point for TSSC.
    """
    parser = argparse.ArgumentParser(description='Trusted Software Supply Chain (TSSC)')
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
        '--results-dir',
        default='tssc-results',
        help='TSSC workflow results file in yml or json'
    )
    parser.add_argument(
        '--step-config',
        metavar='STEP_CONFIG_KEY=STEP_CONFIG_VALUE',
        nargs='+',
        help='Override step config provided by the given TSSC config-file with these arguments.',
        action=ParseKeyValueArge
    )
    args = parser.parse_args(argv)

    # validate args
    if not os.path.exists(args.config_file) or os.stat(args.config_file).st_size == 0:
        print_error('specified -c/--config-file must exist and not be empty')
        sys.exit(101)

    # parse and validate config file
    try:
        tssc_config = parse_yaml_or_json_file(args.config_file)
    except ValueError as err:
        print_error(str(err))
        sys.exit(102)

    if not 'tssc-config' in tssc_config:
        print_error("specified -c/--config-file must have a 'tssc-config' attribute")
        sys.exit(103)

    tssc_factory = TSSCFactory(tssc_config, args.results_dir)

    try:
        tssc_factory.run_step(args.step, args.step_config)
    except (ValueError, TSSCException) as err:
        print_error('Error calling step (' + args.step + '): ' + str(err))
        sys.exit(200)

def init():
    """
    Notes
    -----
    See https://medium.com/opsops/how-to-test-if-name-main-1928367290cb
    """
    if __name__ == "__main__":
        sys.exit(main())

init()
