"""Test for bash.py

Test for the utility for bash operations.
"""
from typing import Dict
from unittest.mock import patch, call, mock_open
from io import BytesIO, StringIO, TextIOWrapper

from ploigos_step_runner.exceptions import StepRunnerException
from tests.helpers.base_test_case import BaseTestCase
from ploigos_step_runner.utils.bash import run_bash
from tests.helpers.test_utils import Any
from pytest import raises
from sh import ErrorReturnCode


class TestBashUtils(BaseTestCase):

    @patch('sh.bash', create=True)  # Given a shell command, 'bash'
    # Given a callback that redirects stdio/stderr
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')
    # Given that I can open files
    @patch("builtins.open", new_callable=mock_open)
    def test_run_script_shell_argument(self, mock_open, redirect_callback_mock, bash_shell_command_mock):

        # When I use run_bash() to run 'command with:args'
        run_bash('/my/output/file', 'mycommand')

        # Then it should run a shell command, `bash command `
        bash_shell_command_mock.assert_any_call(
            '-c',
            'mycommand',
            _out=Any(StringIO),
            _err=Any(StringIO)
        )

    @patch('sh.bash', create=True)  # Given a shell command, 'bash'
    # Given a callback that redirects stdio/stderr
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')
    # Given that I can open files
    @patch("builtins.open", new_callable=mock_open)
    def test_run_script_nonzero_exit_code(self, mock_open, redirect_callback_mock, bash_shell_command_mock):

        # Given the shell command exits with an error code
        bash_shell_command_mock.side_effect = ErrorReturnCode(
            'bash', b'mock stdout', b'mock error')

        # When I use run_bash() to run 'mycommand'
        with raises(StepRunnerException):  # Then it should raise an exception
            run_bash('/my/output/file', 'mycommand')
