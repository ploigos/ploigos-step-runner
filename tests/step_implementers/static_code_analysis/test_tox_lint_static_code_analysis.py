import os
import sh

from io import StringIO
from unittest.mock import patch

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import StepResultArtifact
from ploigos_step_runner.step_implementers.static_code_analysis import \
    ToxLint
from testfixtures import TempDirectory
from tests.helpers.test_utils import Any
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestToxLint__run_step(BaseStepImplementerTestCase):
    @patch('sh.tox', create=True) # Given a shell command, 'tox'
    @patch('os.path.exists', side_effect = lambda filename: filename == 'tox.ini') # Given that a file named tox.ini exists
    def test_run_shell_command(self, os_path_exists_mock, tox_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            # Given an ToxLint step implementer
            tox_test = self.create_given_step_implementer(ToxLint, parent_work_dir_path=working_dir_path)

            # When I run the step
            tox_test.run_step()

            # Then it should run a shell command, 'tox lint'
            tox_shell_command_mock.assert_any_call(
                ('-q', '-e', 'lint',),
                _out=Any(StringIO),
                _err=Any(StringIO)
            )

    @patch('sh.tox', create=True) # Given a shell command, 'tox'
    @patch('os.path.exists', side_effect = lambda filename: filename == 'tox.ini') # Given that a file named tox.ini exists
    def test_success_false_when_shell_command_fails(self, os_path_exists_mock, tox_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            # Given the 'tox' shell command exits with an error code
            tox_shell_command_mock.side_effect = sh.ErrorReturnCode('tox', b'mock stdout', b'mock error')

            # Given an ToxLint step implementer
            tox_test = self.create_given_step_implementer(ToxLint, parent_work_dir_path=working_dir_path)

            # When I run the step
            step_result = tox_test.run_step()

            # Then the StepResult should have success = False
            self.assertEqual(step_result.success, False)

    @patch('sh.tox', create=True) # Given a shell command, 'tox'
    @patch('os.path.exists', side_effect = lambda filename: filename == 'tox.ini') # Given that a file named tox.ini exists
    def test_add_artifact_with_tox_output(self, os_path_exists_mock, tox_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            # Given an ToxLint step implementer
            tox_test = self.create_given_step_implementer(ToxLint, parent_work_dir_path=working_dir_path)

            # When I run the step
            step_result = tox_test.run_step()

            # Then the StepResult should have an artifact with the tox output:
            artifact = step_result.get_artifact('tox-output')
            output_file_path = os.path.join(working_dir_path, 'tox_lint_output.txt')
            self.assertEqual(artifact, StepResultArtifact(
                name='tox-output',
                value=output_file_path,
                description="Standard out and standard error from 'tox lint'."
            ))
