"""Shared utils for tox operations.
"""
import sys
import sh

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback

def run_tox(tox_output_file_path, tox_args):
    """
    Run a tox command

    Paramters
    ---------
    tox_output_file_path:
        String
    tox_args:
        Commandline arguments to tox
    """

    try:
        with open(tox_output_file_path, 'w', encoding='utf-8') as tox_output_file:
            out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stdout,
                tox_output_file
            ])
            err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stderr,
                tox_output_file
            ])

            sh.tox( # pylint: disable=no-member
                tox_args,
                _out=out_callback,
                _err=err_callback
            )
    except sh.ErrorReturnCode as error:
        raise StepRunnerException(
            f"Error running tox. {error}"
        ) from error
