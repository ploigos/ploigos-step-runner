"""
Shared utils for npm operations.
"""
import os
import sys
import sh
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback


def run_npm(npm_output_file_path, npm_args, npm_envs=None):
    """
    Run an npm command

    Parameters
    ----------
    npm_output_file_path:
        String
    npm_args:
        Commandline arguments to npm
    npm_envs:
        Dictionary representing additional environment variables
    """
    try:
        with open(npm_output_file_path, 'w', encoding='utf-8') as npm_output_file:
            out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stdout,
                npm_output_file
            ])
            err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stderr,
                npm_output_file
            ])

            if npm_envs:
                new_env = os.environ.copy()
                new_env.update(npm_envs)

                sh.npm(  # pylint: disable=no-member
                    npm_args,
                    _env=new_env,
                    _out=out_callback,
                    _err=err_callback
                )
            else:
                sh.npm(  # pylint: disable=no-member
                    npm_args,
                    _out=out_callback,
                    _err=err_callback
                )
    except sh.ErrorReturnCode as error:
        raise StepRunnerException(
            f"Error running npm. {error}"
        ) from error
