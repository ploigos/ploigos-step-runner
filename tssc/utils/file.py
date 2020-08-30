"""
Shared utils for dealing with files.
"""

import json
import yaml

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
        raise ValueError(
            f"Error parsing file ({yaml_or_json_file}) as YAML or JSON: " +
            f"\n  JSON error: {str(json_parse_error)}" +
            f"\n  YAML error: {str(yaml_parse_error)}")

    return parsed_file
