"""Test for shell.py

Test for the utility for npm operations.
"""
from unittest.mock import patch, mock_open
from io import StringIO

from ploigos_step_runner.exceptions import StepRunnerException
from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from ploigos_step_runner.utils.shell import Shell
from tests.helpers.test_utils import Any
from pytest import raises
from sh import ErrorReturnCode


class TestShellUtils(BaseStepImplementerTestCase):

    @patch('sh.Command', create=True)  # Given a shell
    # Given a callback that redirects stdio/stderr
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')
    # Given that I can open files
    @patch("builtins.open", new_callable=mock_open)
    def test_run_script_shell_argument(self, my_mock_open, redirect_callback_mock, mock_shell):

        # When I use run 'npm myarg' with an output file
        run_command('npm', '/my/output/file', 'myarg')

        # Then it should run the npm shell command
        mock_shell.assert_any_call('npm')

        # And the argument should be 'myarg'
        mock_shell.return_value.assert_any_call(
            'myarg',
            _env=None,
            _out=Any(StringIO),
            _err=Any(StringIO)
        )

    @patch('sh.Command', create=True)  # Given a shell
    @patch('os.environ.copy', create=True) # Given the ability to create shell environments
    # Given a callback that redirects stdio/stderr
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')
    # Given that I can open files
    @patch("builtins.open", new_callable=mock_open)
    def test_run_script_shell_argument_env_vars(self, my_mock_open, redirect_callback_mock, mock_environ_copy, mock_shell):

        # When I run the npm command and specify environment variables
        run_command(
                'npm',
                '/my/output/file',
                'myarg',
                {"ENV_VAR_1": "VALUE1", "ENV_VAR_2": "VALUE2"})

        # Then it should create a new shell environment
        mock_environ_copy.assert_called()

        # And it should set the environment variables
        mock_environ_copy.return_value.update.assert_any_call({"ENV_VAR_1": "VALUE1", "ENV_VAR_2": "VALUE2"})

        # And it should use the new environment for the shell command
        mock_shell.assert_any_call(
            'npm',
        )
        mock_shell.return_value.assert_any_call(
            'myarg',
            _env=mock_environ_copy.return_value,
            _out=Any(StringIO),
            _err=Any(StringIO)
        )

    @patch('sh.Command', create=True)  # Given a shell
    # Given a callback that redirects stdio/stderr
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')
    # Given that I can open files
    @patch("builtins.open", new_callable=mock_open)
    def test_run_nonzero_exit_code(self, my_mock_open, redirect_callback_mock, mock_shell):

        # Given the shell command exits with an error code
        mock_shell.return_value.side_effect = ErrorReturnCode(
            'npm', b'mock stdout', b'mock error')

        # When I run the npm command
        with raises(StepRunnerException):  # Then it should raise an exception
            run_command('npm', '/my/output/file', 'mycommand')

def run_command(command, output_file, args, env=None):
    Shell().run(command, output_file, args, env)
