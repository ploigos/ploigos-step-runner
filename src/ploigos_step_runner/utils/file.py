"""Shared utils for dealing with files.
"""

import base64
import bz2
import hashlib
import json
import locale
import os
import re
import shutil
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import yaml

SUPPORTED_COMPRESSION_EXTENSIONS = ['.bz2']

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
        Dictionary parsed from given YAML or JSON file.

    Raises
    ------
    ValueError
        If the given file can not be parsed as YAML or JSON.
    """
    parsed_file = None
    json_parse_error = None
    yaml_parse_error = None

    with open(yaml_or_json_file, 'r', encoding='utf-8') as open_yaml_or_json_file:
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

    # depending on the protocol type, get the source_file into the working dir
    if is_local_file_path(source_uri):
        # get the destination dir path
        source_uri_abs_path = normalize_file_path(source_uri)

        # copy the file to the working dir
        source_file_name = os.path.basename(source_uri_abs_path)
        destination_path = os.path.join(destination_dir, source_file_name)
        shutil.copyfile(
            src=source_uri_abs_path,
            dst=destination_path
        )
    elif is_remote_http_path(source_uri):
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
        #   Defensive coding; this case should NEVER happen, given the logic in
        #   _validate_required_config_or_previous_step_result_artifact_keys; should this
        #   case somehow be reached, raise an error instead of failing silently.
        raise ValueError(
            "Unexpected error, should have been caught by step validation."
            f" Source ({source_uri}) must start with known protocol (/|file://|http://|https://)."
        )

    return destination_path

def download_and_decompress_source_to_destination(
    source_uri,
    destination_dir
):
    """Given a source url using a known protocol, downloads the file to a given destination.
    The file is also decompressed if the compression method is known; see `is_compressed` and
    `decompress_file` methods for additional information.

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

    if is_compressed(destination_path):
        destination_path = decompress_file(destination_path)

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
    # Get preferred encoding; see https://www.python.org/dev/peps/pep-0597/
    encoding = locale.getpreferredencoding(False)

    encoded_text = Path(file_path).read_text(encoding=encoding).encode(encoding=encoding)
    return base64.b64encode(encoded_text).decode(encoding)

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

def upload_file(
    file_path,
    destination_uri,
    username=None,
    password=None
): # pylint: disable=too-many-locals
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

    if is_local_file_path(destination_uri):
        upload_result = copy_file(file_path, destination_uri)
    elif is_remote_http_path(destination_uri):
        upload_result = upload_file_to_http_target(
            file_path,
            destination_uri,
            username,
            password
        )
    else:
        # NOTE:
        #   Defensive coding; this case should NEVER happen, given the logic in
        #   _validate_required_config_or_previous_step_result_artifact_keys; should this
        #   case somehow be reached, raise an error instead of failing silently.
        raise ValueError(
            "Unexpected error, should have been caught by step validation."
            f" Destination ({destination_uri}) must start with known protocol"
            " (/|file://|http://|https://)."
        )

    return upload_result

def copy_file(
    file_path,
    destination_uri
):
    """Copies a given file to a destination on the local filesystem.

    Notes
    -----
    Known source protocols
    * /        - local file path
    * file://  - local file path

    Parameters
    ----------
    file_path : str
        Path to file to upload.
    destination_uri : str
        URI to copy file to.

    Returns
    -------
    str
        The full path of the destination file.

    Raises
    ------
    ValueError
        If file_path does not exist.
    """

    # get the destination dir path
    destination_dir_path = normalize_file_path(destination_uri)

    # create the destination dir
    os.makedirs(destination_dir_path, exist_ok=True)

    # copy the file to the destination dir
    destination_file_name = os.path.basename(file_path)
    destination_path = os.path.join(destination_dir_path, destination_file_name)
    shutil.copyfile(
        src=file_path,
        dst=destination_path
    )

    return destination_path

def upload_file_to_http_target(
    file_path,
    destination_uri,
    username=None,
    password=None
): # pylint: disable=too-many-locals
    """Uploads a given file to a remote destination, using http.

    Notes
    -----
    Known source protocols
    * http://  - remote upload
    * https:// - remote upload

    Parameters
    ----------
    file_path : str
        Path to file to upload.
    destination_uri : str
        URI to upload file to using http.
    username : str, optional
        Optional user name for http destination.
    password : str, optional
        Optional password for http destination.

    Returns
    -------
    str
        The response body.

    Raises
    ------
    ValueError
        If file_path does not exist.
        If destination_uri does not start with /|file://|http://|https://
    RuntimeError
        If error uploading file.
    """
    upload_result = None

    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

    if username:
        # create opener http basic authentication
        top_level_uri = urlparse(destination_uri).netloc
        password_mgr.add_password(None, top_level_uri, username, password)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)
    else:
        # create a default opener
        opener = urllib.request.build_opener()

    with open(file_path, 'rb') as file:
        request = urllib.request.Request(
            url=destination_uri,
            data=file.read(),
            method='PUT',
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

    return upload_result

def get_file_extension(file_uri):
    """Given a file path, return only the extension of the file

    Parameters
    ----------
    file_uri : string
        File name (including full path) to a file

    Returns
    -------
    str
        The file extension (e.g., '.bz2' for '/tmp/data.xml.bz2').
    """
    _, file_extension = os.path.splitext(file_uri)

    return file_extension

def is_compressed(file_uri):
    """Given a file path, determine if it the file is compressed using an algorithm that this class
    recognizes and can handle; see `decompress_file` method for additional information.

    Notes
    -----
    Known compression types
    * bz2

    Parameters
    ----------
    file_uri : string
        File to check whether or not is in a supported compression format

    Returns
    -------
    bool
        True, if the file extension matches a support compression algorithm.
    """
    compressed = False

    if get_file_extension(file_uri) in SUPPORTED_COMPRESSION_EXTENSIONS:
        compressed = True

    return compressed

def decompress_file(file_uri):
    """Decompresses a file; see `is_compressed` for additional information. This method
    assumes that only a single file will reside inside the compressed archive (currently
    a moot point, since the only supported algorithm at the moment, bz2, only allows
    single files to be compressed).

    Notes
    -----
    Known compression types
    * bz2

    Parameters
    ----------
    file_uri : path
        Path to the file to decompress.

    Returns
    -------
    str
        Path to the decompressed file.
    """

    # file_path is the filename without the extension
    file_path, file_extension = os.path.splitext(file_uri)

    if file_extension == '.bz2':
        with \
                bz2.BZ2File(file_uri) as decompressed_source, \
                open(file_path, "wb") as decompressed_destination:
            shutil.copyfileobj(decompressed_source, decompressed_destination)

            # NOTE: the compressed file was decompressed to file_path,
            #       therefore that is now the actual file we want
            file_uri = file_path

    return file_uri

def normalize_file_path(uri):
    """Normalizes the file path, if necessary.

    Parameters
    ----------
    uri : string
        File path that may need to be normalized (e.g., removal of 'file://')

    Returns
    -------
    str
        The source_uri, normalized
    """
    if re.match(r'^file://', uri):
        # remove file:// and turn into an absolute path
        uri = os.path.abspath(
            re.sub('^file://', '', uri)
        )

    return uri

def is_local_file_path(uri):
    """Determines whether or a not a given uri refers to a file on the local file system

    Parameters
    ----------
    uri : string
        File path to inspect

    Returns
    -------
    bool
        True, if source-uri is a local file (e.g., file:///path/to/file.xml)
    """
    return re.match(r'^file://|/', uri)

def is_remote_http_path(uri):
    """Determines whether or a not a given uri refers to a file location accessible via
    the Hypertext Transfer Protocol

    Parameters
    ----------
    uri : string
        File path to inspect

    Returns
    -------
    bool
        True, if this is an http file (e.g., https://example.org/example.zip)
    """
    return re.match(r'^http://|^https://', uri)
