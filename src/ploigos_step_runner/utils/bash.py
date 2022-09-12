"""
Shared utils for bash operations.
"""

import sys

import sh
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback

def run_bash(output_file_path, command):
    """Run a bash command.
    """
    try:
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stdout,
                output_file
            ])
            err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stderr,
                output_file
            ])

            sh.bash(  # pylint: disable=no-member
                '-c',
                command,
                _out=out_callback,
                _err=err_callback
            )
    except sh.ErrorReturnCode as error:
        raise StepRunnerException(
            f"Error running command. {error}"
        ) from error
