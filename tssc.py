# pylint: disable=W0614,W0401

"""
TSSC entry point.

Notes
-----
Required pip modules
* pyyaml
"""

import sys
import argparse
import os.path
import json
import yaml

from com.redhat.tssc import TSSCFactory, TSSCException
from com.redhat.tssc.step_implementers import *

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
        except (yaml.scanner.ScannerError, ValueError) as err:
            yaml_parse_error = err

    if json_parse_error and yaml_parse_error:
        raise ValueError('Error parsing file (' + yaml_or_json_file + ') as YAML or JSON: '
                         + "\n  JSON error: " + str(json_parse_error)
                         + "\n  YAML error: " + str(yaml_parse_error))

    return parsed_file

def main():
    """
    Main entry point for TSSC.
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
    if not os.path.exists(args.config_file) or os.stat(args.config_file).st_size == 0:
        print_error('specifed -c/--config-file must exist and not be empty')
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

    tssc_factory = TSSCFactory(tssc_config)

    try:
        tssc_factory.run_step(args.step)
    except TSSCException as err:
        print_error('Error calling step (' + args.step + '): ' + str(err))
        sys.exit(200)

if __name__ == '__main__':
    main()
