"""Shared utils for dealing with files.
"""

import base64
import bz2
import hashlib
import json
import os
import re
import shutil
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

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

def download_source_to_destination(
    source_uri,
    destination_dir
):
    """Given a source url using a known protocol downloads the file to a given destination.

    Notes
    -----
    Known source protocols
    * file://
    * http://
    * https://

    Parameters
    ----------
    source_uri : url
        URL to a source file using a known protocol to download to destination folder
        and decompress if necessary.
    destination_dir : path
        Path to directory to download and decompress if necessary the source url to.

    Returns
    -------
    str
        Path to the downloaded file from given source.

    Raises
    ------
    RuntimeError
        If error downloading file.
    ValueError
        If source_uri does not start with file://|http://|https://
    """

    # depending on the protocol type get the source_file into the working dir
    if re.match(r'^file://|/', source_uri):
        # get the destination dir path
        if re.match(r'^file://', source_uri):
            # remove file:// and turn into an absolute path
            source_uri_abs_path = os.path.abspath(
                re.sub('^file://', '', source_uri)
            )
        else:
            source_uri_abs_path = source_uri

        # copy the file to the working dir
        source_file_name = os.path.basename(source_uri_abs_path)
        destination_path = os.path.join(destination_dir, source_file_name)
        shutil.copyfile(
            src=source_uri_abs_path,
            dst=destination_path
        )
    elif re.match(r'^http://|^https://', source_uri):
        # download the file to the working dir
        source_file_name = os.path.basename(source_uri)
        destination_path = os.path.join(destination_dir, source_file_name)

        try:
            urllib.request.urlretrieve(
                url=source_uri,
                filename=destination_path
            )
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Error downloading file ({source_uri}): {error}") from error
    else:
        # NOTE:
        #   this should NEVER happen because of the logic in
        #   _validate_required_config_or_previous_step_result_artifact_keys
        #   but rather then failing silently need to do something.
        raise ValueError(
            "Unexpected error, should have been caught by step validation."
            f" Source ({source_uri}) must start with known protocol (/|file://|http://|https://)."
        )
    return destination_path

def download_and_decompress_source_to_destination(
    source_uri,
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
    source_uri : url
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
    ValueError
        If source_uri does not start with file://|http://|https://
    """

    destination_path = download_source_to_destination(source_uri, destination_dir)

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

def base64_encode(file_path):
    """Given a file_path, read and encode the contents in base64
    Returns
    -------
    Base64Contents
        base64 encoded string of file contents
    """
    encoding = Path(file_path).read_text().encode('utf-8')
    return base64.b64encode(encoding).decode('utf-8')

def get_file_hash(file_path):
    """Returns file hash of given file.

    Returns
    -------
    StepResult
        Object containing the dictionary results of this step.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as the_file:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: the_file.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def upload_file(file_path, destination_uri, username=None, password=None): # pylint: disable=too-many-locals
    """Uploads a given file to a given destination.

    Notes
    -----
    Known source protocols
    * /        - local file path
    * file://  - local file path
    * http://  - remote upload
    * https:// - remote upload

    Parameters
    ----------
    file_path : str
        Path to file to upload.
    destination_uri : str
        URI to upload file to using known protocol.
    username : str, optional
        Optional user name to use when uploading the file to an http(s) destination.
    password : str, optional
        Optional password to use when upload the file to an http(s) destination.

    Returns
    -------
    str
        If given destination is a local file path,
        then return the full path of the destination file.
        If given destination is a remote upload, return the response body as a string.

    Raises
    ------
    ValueError
        If file_path does not exist.
        If destination_uri does not start with /|file://|http://|https://
    RuntimeError
        If error uploading file.
    """
    if not os.path.exists(file_path):
        raise ValueError(f"Given file path ({file_path}) to upload does not exist.")

    upload_result = None

    if re.match(r'^file://|/', destination_uri):
        # get the destination dir path
        if re.match(r'^file://', destination_uri):
            # remove file:// and turn into an absolute path
            destination_dir_path = os.path.abspath(
                re.sub('^file://', '', destination_uri)
            )
        else:
            destination_dir_path = destination_uri

        # create the destination dir
        os.makedirs(destination_dir_path, exist_ok=True)

        # copy the file to the destination dir
        destination_file_name = os.path.basename(file_path)
        destination_path = os.path.join(destination_dir_path, destination_file_name)
        shutil.copyfile(
            src=file_path,
            dst=destination_path
        )

        upload_result = destination_path
    elif re.match(r'^http://|^https://', destination_uri):
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

        if username:
            top_level_uri = urlparse(destination_uri).netloc
            password_mgr.add_password(None, top_level_uri, username, password)
            handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
            opener = urllib.request.build_opener(handler)
        else:
            opener = urllib.request.build_opener()

        with open(file_path, 'rb') as file:
            request = urllib.request.Request(url=destination_uri, data=file.read(), method='PUT',
                                             headers={'Content-Type': 'application/octet-stream'})

            try:
                result = opener.open(request)
                response_reason = result.reason
                response_body = str(result.read(), encoding='utf8')
                response_code = result.status
                upload_result = f"status={response_code}, " \
                                f"reason={response_reason}, " \
                                f"body={response_body}"
            except urllib.error.HTTPError as error:
                raise RuntimeError(
                    f"Error uploading file ({file_path}) to destination ({destination_uri})"
                    f" with user name ({username}) and password ({password}): {error}"
                ) from error

    else:
        # NOTE:
        #   this should NEVER happen because of the logic in
        #   _validate_required_config_or_previous_step_result_artifact_keys
        #   but rather then failing silently need to do something.
        raise ValueError(
            "Unexpected error, should have been caught by step validation."
            f" Destination ({destination_uri}) must start with known protocol"
            " (/|file://|http://|https://)."
        )

    return upload_result
