"""Test for npm.py

Test for the utility for npm operations.
"""
from typing import Dict
from unittest.mock import patch, call, mock_open
from io import BytesIO, StringIO, TextIOWrapper

from ploigos_step_runner.exceptions import StepRunnerException
from tests.helpers.base_test_case import BaseTestCase
from ploigos_step_runner.utils.npm import run_npm
from tests.helpers.test_utils import Any
from pytest import raises
from sh import ErrorReturnCode


class TestNpmUtils(BaseTestCase):

    @patch('sh.npm', create=True)  # Given a shell command, 'npm'
    # Given a callback that redirects stdio/stderr
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')
    # Given that I can open files
    @patch("builtins.open", new_callable=mock_open)
    def test_run_script_shell_argument(self, mock_open, redirect_callback_mock, npm_shell_command_mock):

        # When I use run_npm() to run 'command with:args'
        run_npm('/my/output/file', 'mycommand')

        # Then it should run a shell command, `npm command with:args`
        npm_shell_command_mock.assert_any_call(
            'mycommand',
            _out=Any(StringIO),
            _err=Any(StringIO)
        )

    @patch('sh.npm', create=True)  # Given a shell command, 'npm'
    # Given a callback that redirects stdio/stderr
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')
    # Given that I can open files
    @patch("builtins.open", new_callable=mock_open)
    def test_run_script_shell_argument_env_vars(self, mock_open, redirect_callback_mock, npm_shell_command_mock):

        # When I use run_npm() to run 'command with:args with:envs'
        run_npm('/my/output/file',
                'mycommand',
                {"KEY1": "VALUE1", "KEY2": "VALUE2"})

        # Then it should run a shell command, `npm command with:args`
        npm_shell_command_mock.assert_any_call(
            'mycommand',
            _out=Any(StringIO),
            _err=Any(StringIO),
            _env=Any(Dict)
        )

    @patch('sh.npm', create=True)  # Given a shell command, 'npm'
    # Given a callback that redirects stdio/stderr
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')
    # Given that I can open files
    @patch("builtins.open", new_callable=mock_open)
    def test_run_script_nonzero_exit_code(self, mock_open, redirect_callback_mock, npm_shell_command_mock):

        # Given the shell command exits with an error code
        npm_shell_command_mock.side_effect = ErrorReturnCode(
            'npm', b'mock stdout', b'mock error')

        # When I use run_npm() to run 'mycommand'
        with raises(StepRunnerException):  # Then it should raise an exception
            run_npm('/my/output/file', 'mycommand')
