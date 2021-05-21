"""Shared utils for dealing with gpg keys.
"""

import re
import sys
from io import StringIO
import sh

from ploigos_step_runner.utils.io import create_sh_redirect_to_multiple_streams_fn_callback
from ploigos_step_runner.exceptions import StepRunnerException

def import_gpg_key(sig_file, extra_data_file, gpg_user):
    """Runs the step implemented by this StepImplementer.

    Returns
    -------
    StepResult
        Object containing the dictionary results of this step.
    """
    gpg_stdout_result = StringIO()
    gpg_stdout_callback = create_sh_redirect_to_multiple_streams_fn_callback([
        sys.stdout,
        gpg_stdout_result
    ])
    sh.gpg( # pylint: disable=no-member
        '--armor',
        '-u',
        gpg_user,
        '--output',
        sig_file,
        '--detach-sign',
        extra_data_file,
        _out=gpg_stdout_callback,
        # _in=extra_data,
        _err_to_out=True,
        _tee='out'
    )
    return gpg_stdout_result

def import_pgp_key(pgp_private_key):
    """Runs the step implemented by this StepImplementer.

    Returns
    -------
    StepResult
        Object containing the dictionary results of this step.
    """
    # Example input to match on:
    #   sec:-:3072:1:CF4AC14A3D109637:1601483310:1664555310::-:::scESC::::::23::0:
    #   fpr:::::::::DD7208BA0A6359F65B906B29CF4AC14A3D109637:
    #   grp:::::::::A483EE079EC1D58A954E3AAF3BCC61EDD7596BF0:
    gpg_regex = re.compile(r"^fpr:+([^:]+):$", re.MULTILINE)

    print("Import PGP private key to sign container image(s) with")
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
            raise StepRunnerException(
                "Error getting PGP fingerprint for PGP key"
                " to sign container image(s) with. See stdout and stderr for more info."
            )
        pgp_private_key_fingerprint = gpg_imported_pgp_private_key_fingerprints[0]

        print(
            "Imported PGP private key to sign container image(s) with: "
            f"fingerprint='{pgp_private_key_fingerprint}'"
        )
    except sh.ErrorReturnCode as error:
        raise StepRunnerException(
            f"Error importing pgp private key: {error}"
        ) from error

    return pgp_private_key_fingerprint
