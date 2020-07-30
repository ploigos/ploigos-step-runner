# pylint: disable=W0614,W0401

"""
TSSC entry point.
"""

import sys
import glob
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
    Parse YAML or JSON config files.

    Parameters
    ----------
    yaml_or_json_files : string
        List of paths to YAML or JSON files to load as a dictionary.

    Returns
    -------
    dict
        Dictionary parsed from given YAML or JSON file

    Raises
    ------
    ValueError
        If the given file can not be parsed as YAML or JSON.
    """
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

def parse_config_files(files):
    """Parses and merges a list of TSSC configuration files.

    Given a list of files and directories parses all of the child files
    as TSSC configuration files merges them together.

    Notes
    -----
    If any files have duplicate (deep) keys then will throw an error.

    Parameters
    ----------
    files : array
       Array of files and/or directories that should be parsed as TSSC configuration files
       and merged into one configuration object.

    Returns
    -------
    dict
        TSSC configuration created by merging all of the given files.

    Raises
    ------
    ValueError
        If any of the given file can not be parsed as YAML or JSON.
        If any of the given files have duplicate (deep) keys.
    """
    tssc_config = {}
    merged_files = []
    for file in files:
        # if file is a dir add all of the recursive files under that dir to the list of files
        # to merge and parse
        if os.path.isdir(file):
            dir_files = glob.glob(file + '/**', recursive=True)
            for dir_file in dir_files:
                if os.path.isfile(dir_file):
                    files.append(dir_file)
        else:
            parsed_file = parse_yaml_or_json_file(file)

            if not 'tssc-config' in parsed_file:
                print_error("specified -c/--config must have a 'tssc-config' attribute")
                sys.exit(103)

            try:
                deep_merge(tssc_config, parsed_file)
                merged_files.append(file)
            except Exception as error:
                raise ValueError(
                    "Duplicate keys when merging file ({file}) into ".format(file=file) +
                    "other configuration files ({merged_files}): {error}".format(
                        merged_files=merged_files, error=error)
                    ) from error

    return tssc_config

def deep_merge(dest, source, path=None):
    """"deep merges dest into source

    Notes
    ------
    Modifies destination.

    Source is https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries/7205107#7205107 # pylint: disable=line-too-long
    """
    if path is None:
        path = []

    for key in source:
        if key in dest:
            if isinstance(dest[key], dict) and isinstance(source[key], dict):
                deep_merge(dest[key], source[key], path + [str(key)])
            elif dest[key] == source[key]:
                pass # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            dest[key] = source[key]
    return dest


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
        '-e',
        '--environment',
        required=False,
        help='The environment to run this step against.'
    )
    parser.add_argument(
        '-c',
        '--config',
        required=True,
        nargs='+',
        help='TSSC workflow configuration files, or directories containing files, in yml or json'
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
    for config_file in args.config:
        if not os.path.exists(config_file) or os.stat(config_file).st_size == 0:
            print_error('specified -c/--config must exist and not be empty')
            sys.exit(101)

    # parse and validate config file
    try:
        tssc_config = parse_config_files(args.config)
    except ValueError as err:
        print_error(str(err))
        sys.exit(102)

    tssc_factory = TSSCFactory(tssc_config, args.results_dir)

    try:
        tssc_factory.run_step(args.step, args.step_config, args.environment)
    except (ValueError, AssertionError, TSSCException) as err:
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
