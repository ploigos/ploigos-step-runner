"""Shared utils for dealing with files.
"""

import bz2
import json
import os
import re
import shutil
import urllib.request

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

def download_and_decompress_source_to_destination(
    source_url,
    destination_dir
):
    """Given a source url using a known protocol downloads the file to a given destination
    and decompresses it if known compression method.

    Notes
    -----
    Known source protocols
    * file://
    * http://
    * https://

    Known compression types
    * bz2

    Parameters
    ----------
    source_url : url
        URL to a source file using a known protocol to download to destination folder
        and decompress if necessary.
    destination_dir : path
        Path to directory to download and decompress if necessary the source url to.

    Returns
    -------
    str
        Path to the downloaded and decompressed (if needed) file from given source.

    Raises
    ------
    RuntimeError
        If error downloading file.
    AssertionError
        If source_url does not start with file://|http://|https://
    """

    # depending on the protocol type get the source_file into the working dir
    if re.match(r'^file://', source_url):
        # remove file:// and turn into an absolute path
        source_url_abs_path = os.path.abspath(
            re.sub('^file://', '', source_url)
        )

        # copy the file to the working dir
        source_file_name = os.path.basename(source_url_abs_path)
        destination_path = os.path.join(destination_dir, source_file_name)
        shutil.copyfile(
            src=source_url_abs_path,
            dst=destination_path
        )
    elif re.match(r'^http://|^https://', source_url):
        # download the file to the working dir
        source_file_name = os.path.basename(source_url)
        destination_path = os.path.join(destination_dir, source_file_name)

        try:
            urllib.request.urlretrieve(
                url=source_url,
                filename=destination_path
            )
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Error downloading file ({source_url}): {error}") from error
    else:
        # NOTE:
        #   this should NEVER happen because of the logic in
        #   _validate_required_config_or_previous_step_result_artifact_keys
        #   but rather then failing silently need to do something.
        raise AssertionError(
            "Unexpected error, should have been caught by step validation."
            f" Source ({source_url}) must start with known protocol (file://|http://|https://)."
        )

    # if extension is .bz2, decompress, else assume file is fine as as is
    file_path, file_extension = os.path.splitext(destination_path)
    if file_extension == '.bz2':
        # NOTE: file_path is whats left after removeing .bz2 from the end
        with \
                bz2.BZ2File(destination_path) as decompressed_source, \
                open(file_path,"wb") as decompressed_destination:

            shutil.copyfileobj(decompressed_source, decompressed_destination)

            # NOTE: the compressed file was decompressed to file_path
            #       therefor that is now the actual file we want
            destination_path = file_path

    return destination_path

def create_parent_dir(file_path):
    """Helper method to create parent folder of given file if it does not exist.

    Parameters
    ----------
    file_path: str
        Absolute name of a file to create the parent folders for
    """
    parent_dir_path = os.path.dirname(file_path)
    if parent_dir_path:
        os.makedirs(parent_dir_path, exist_ok=True)
