import os
from io import StringIO
from unittest.mock import patch
from ploigos_step_runner import config

import sh
from ploigos_step_runner.results import StepResultArtifact
from ploigos_step_runner.step_implementers.shared import AdHoc, ad_hoc
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any


class TestAdHocPackage__run_step(BaseStepImplementerTestCase):
    # Given a shell command, 'bash'
    @patch('sh.bash', create=True)
    def test_run_shell_command(self, bash_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            config = {
                'command': 'echo "Hello World!"'
            }

            # Given an AdHoc step implementer
            ad_hoc_test = self.create_given_step_implementer(
                AdHoc,
                step_config=config,
                parent_work_dir_path=working_dir_path
            )

            # When I run the step
            ad_hoc_test.run_step()

            # Then it should run a shell command, 'echo "Hello World!"'
            bash_shell_command_mock.assert_any_call(
                '-c',
                'echo "Hello World!"',
                _out=Any(StringIO),
                _err=Any(StringIO)
            )

    # Given a shell command, 'bash'
    @patch('sh.bash', create=True)
    def test_success_false_when_shell_command_fails(self, bash_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            config = {
                'command': 'echooo "Hello World!"'
            }

            # Given an NpmPackage step implementer
            ad_hoc_test = self.create_given_step_implementer(
                AdHoc,
                parent_work_dir_path=working_dir_path,
                step_config=config
            )

            # Given the 'echooo Hello World!' shell command exits with an error code
            bash_shell_command_mock.side_effect = sh.ErrorReturnCode('bash', b'mock stdout', b'mock error')

            # When I run the step
            step_result = ad_hoc_test.run_step()

            # Then the StepResult should have success = False
            self.assertEqual(step_result.success, False)

    # Given a shell command, 'bash'
    @patch('sh.bash', create=True)
    def test_add_artifact_with_command_output(self, bash_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:

            # Given an AdHoc step implementer
            working_dir_path = os.path.join(temp_dir.path, 'working')
            config = {
                'command': 'echo "Hello World!"'
            }
            ad_hoc_test = self.create_given_step_implementer(
                AdHoc,
                parent_work_dir_path=working_dir_path,
                step_config=config
            )

            # When I run the step
            step_result = ad_hoc_test.run_step()

            # Then the StepResult should have an artifact with the npm output:
            artifact = step_result.get_artifact('command-output')
            output_file_path = os.path.join(working_dir_path, 'ad_hoc_output.txt')
            self.assertEqual(artifact, StepResultArtifact(
                name='command-output',
                value=output_file_path,
                description="Standard out and standard error from ad-hoc command run."
            ))
