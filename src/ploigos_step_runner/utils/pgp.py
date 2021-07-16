"""Shared utils for dealing with PGP keys.

Note that these functions use the "gpg" program to interact with PGP keys, but as PGP is the
standard and GPG is an implementation of that standard, we universally refer to anything having
to do with PGP keys as "PGP" rather then "GPG".
"""

import re
import sys
from io import StringIO
import sh

from ploigos_step_runner.utils.io import create_sh_redirect_to_multiple_streams_fn_callback

def detach_sign_with_pgp_key(file_to_sign_path, pgp_private_key_fingerprint, output_signature_path):
    """Does a detached sign of a given file using a given users private key.

    Parameters
    ----------
    file_to_sign_path : str
        Path to file to create a detached PGP signature for.

    pgp_private_key_fingerprint : str
        PGP private key fingerprint to sign the given file with.

    output_signature_path : str
        File path to put the detached signature in.

    Raises
    ------
    RuntimeError
        If error signing given file with given key.
    """
    try:
        sh.gpg( # pylint: disable=no-member
            '--armor',
            '--local-user',
            pgp_private_key_fingerprint,
            '--output',
            output_signature_path,
            '--detach-sign',
            file_to_sign_path
        )
    except sh.ErrorReturnCode as error:
        raise RuntimeError(
            f"Error performing detached signature of file ({file_to_sign_path})" \
            f" with PGP key ({pgp_private_key_fingerprint}): {error}"
        ) from error

def import_pgp_key(pgp_private_key):
    """Imports a PGP key.

    Parameters
    ----------
    pgp_private_key : str
        PGP key to import.

    Returns
    -------
    str
        Fingerprint of the imported PGP key.

    Raises
    ------
    RuntimeError
        If error getting PGP fingerprint for imported PGP key
        If error importing PGP key.
    """
    # Example input to match on:
    #   sec:-:3072:1:CF4AC14A3D109637:1601483310:1664555310::-:::scESC::::::23::0:
    #   fpr:::::::::DD7208BA0A6359F65B906B29CF4AC14A3D109637:
    #   grp:::::::::A483EE079EC1D58A954E3AAF3BCC61EDD7596BF0:
    gpg_regex = re.compile(r"^fpr:+([^:]+):$", re.MULTILINE)

    print("Import PGP private key to sign artifacts with")
    try:
        # import the key

        # NOTE: GPG is weird in that it sends "none error" output to stderr even on success...
        #       so merge the stderr into stdout
        gpg_import_stdout_result = StringIO()
        gpg_import_stdout_callback = create_sh_redirect_to_multiple_streams_fn_callback([
            sys.stdout,
            gpg_import_stdout_result
        ])
        sh.gpg( # pylint: disable=no-member
            '--import',
            '--fingerprint',
            '--with-colons',
            '--import-options=import-show',
            _in=pgp_private_key,
            _out=gpg_import_stdout_callback,
            _err_to_out=True,
            _tee='out'
        )

        # get the fingerprint of the imported key
        #
        # NOTE: if more then one match just using first one...
        gpg_imported_pgp_private_key_fingerprints = re.findall(
            gpg_regex,
            gpg_import_stdout_result.getvalue()
        )
        if len(gpg_imported_pgp_private_key_fingerprints) < 1:
            raise RuntimeError(
                "Error getting PGP fingerprint for PGP key"
                " to sign container image(s) with. See stdout and stderr for more info."
            )
        pgp_private_key_fingerprint = gpg_imported_pgp_private_key_fingerprints[0]

        print(
            "Imported PGP private key to sign artifacts with: "
            f"fingerprint='{pgp_private_key_fingerprint}'"
        )
    except sh.ErrorReturnCode as error:
        raise RuntimeError(
            f"Error importing pgp private key: {error}"
        ) from error

    return pgp_private_key_fingerprint

def export_pgp_public_key(pgp_private_key_fingerprint):
    """Exports a PGP public key given a private key fingerprint.

    Parameters
    ----------
    pgp_private_key_fingerprint : str
        PGP fingerprint.

    Returns
    -------
    str
        Public key from the private key fingerprint.

    Raises
    ------
    RuntimeError
        If error getting exported PGP public key
    """
    try:
        gpg_export_stdout_result = StringIO()

        sh.gpg( # pylint: disable=no-member
            '--armor',
            '--export',
            pgp_private_key_fingerprint,
            _out=gpg_export_stdout_result,
            _err_to_out=False,
            _tee='out'
        )

        gpg_public_key = gpg_export_stdout_result.getvalue()
    except sh.ErrorReturnCode as error:
        raise RuntimeError(
            f"Error exporting pgp public key: {error}"
        ) from error

    return gpg_public_key
