"""
Shared utils for npm operations.
"""
import sys
import sh
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback


def run_npm(npm_output_file_path, npm_run_scripts):
    """
    Use npm command to run a script in package.json

    Parameters
    ----------
    npm_output_file_path:
        String
    npm_run_scripts:
        List of scripts in package.json 
    """
    try:
        with open(npm_output_file_path, 'w') as npm_output_file:
            out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stdout,
                npm_output_file
            ])
            err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stderr,
                npm_output_file
            ])

            for script in npm_run_scripts:
                sh.npm(
                    'run',
                    script,
                    _out=out_callback,
                    _err=err_callback
                )
    except sh.ErrorReturnCode as error:
        raise StepRunnerException(
            f"Error running npm. {error}"
        ) from error
