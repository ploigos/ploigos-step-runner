"""Test for tox.py

Test for the utility for tox operations.
"""
from unittest.mock import patch, call, mock_open
from io import StringIO

from ploigos_step_runner import StepRunnerException
from tests.helpers.base_test_case import BaseTestCase
from ploigos_step_runner.utils.tox import run_tox
from tests.helpers.test_utils import Any
from pytest import raises
from sh import ErrorReturnCode

class TestToxUtils(BaseTestCase):

    @patch('sh.tox', create=True) # Given a shell command, 'tox'
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')  # Given a callback that redirects stdio/stderr
    @patch("builtins.open", new_callable=mock_open) # Given that I can open files
    def test_run_script_shell_argument(self, mock_open, redirect_callback_mock, tox_shell_command_mock):

        # When I use run_tox() to run 'command with:args'
        run_tox('/my/output/file', 'mycommand')

        # Then it should run a shell command, `tox command with:args`
        tox_shell_command_mock.assert_any_call(
            'mycommand',
            _out=Any(StringIO),
            _err=Any(StringIO)
        )

    @patch('sh.tox', create=True) # Given a shell command, 'tox'
    @patch('ploigos_step_runner.utils.io.create_sh_redirect_to_multiple_streams_fn_callback')  # Given a callback that redirects stdio/stderr
    @patch("builtins.open", new_callable=mock_open) # Given that I can open files
    def test_run_script_nonzero_exit_code(self, mock_open, redirect_callback_mock, tox_shell_command_mock):

        # Given the shell command exits with an error code
        tox_shell_command_mock.side_effect = ErrorReturnCode('tox', b'mock stdout', b'mock error')

        # When I use run_tox() to run 'mycommand'
        with raises(StepRunnerException): # Then it should raise an exception
            run_tox('/my/output/file', 'mycommand')
