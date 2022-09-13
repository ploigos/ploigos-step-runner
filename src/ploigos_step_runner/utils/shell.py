"""
Use this module to run shell commands with a simplified interface that is
easier to user test than the 'sh' module.
"""
import os
import sys
import sh
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback


class Shell:
    """
    Provides access to a command-line shell. Use run() to run commands.
    """

    def run(self, command, output_file_path=None, args=None, envs=None):
        """
        Run a shell command

        Parameters
        ----------
        command:
            String
        output_file_path:
            String
        args:
            Commandline arguments
        envs:
            Dictionary representing additional environment variables
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

                new_env = None
                if envs:
                    new_env = os.environ.copy()
                    new_env.update(envs)

                # Run the command
                shell_command = sh.Command(  # pylint: disable=unexpected-keyword-arg
                    command
                )
                shell_command(
                    args,
                    _env=new_env,
                    _out=out_callback,
                    _err=err_callback
                )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error running shell command. {error}"
            ) from error
