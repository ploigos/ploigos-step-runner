import os
from io import StringIO
from unittest.mock import patch

from ploigos_step_runner.results import StepResultArtifact
from ploigos_step_runner.step_implementers.package import NpmPackage
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.exceptions import StepRunnerException


class TestNpmPackage__run_step(BaseStepImplementerTestCase):

    @patch('ploigos_step_runner.step_implementers.shared.npm_generic.Shell.run') # Given a shell
    @patch('os.path.exists', side_effect = lambda filename: filename == 'package.json') # Given that a file named package.json exists
    def test_run_shell_command(self, os_path_exists_mock, mock_shell_run):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            # Given an NpmPackage step implementer
            npm_test = self.create_given_step_implementer(NpmPackage, parent_work_dir_path=working_dir_path)

            # When I run the step
            npm_test.run_step()

            # Then it should run a shell command, 'npm install'
            expected_output_file_path = os.path.join(working_dir_path, 'npm_package_output.txt')
            mock_shell_run.assert_any_call(
                'npm',
                output_file_path=expected_output_file_path,
                args='install',
                envs=None
            )

    @patch('ploigos_step_runner.step_implementers.shared.npm_generic.Shell.run') # Given a shell
    @patch('os.path.exists', side_effect = lambda filename: filename == 'package.json') # Given that a file named package.json exists
    def test_success_false_when_shell_command_fails(self, os_path_exists_mock, mock_shell_run):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            # Given the 'npm' shell command exits with an error code
            mock_shell_run.side_effect = StepRunnerException()

            # Given an NpmPackage step implementer
            npm_test = self.create_given_step_implementer(NpmPackage, parent_work_dir_path=working_dir_path)

            # When I run the step
            step_result = npm_test.run_step()

            # Then the StepResult should have success = False
            self.assertEqual(step_result.success, False)

    @patch('ploigos_step_runner.step_implementers.shared.npm_generic.Shell.run') # Given a shell
    @patch('os.path.exists', side_effect = lambda filename: filename == 'package.json') # Given that a file named package.json exists
    def test_add_artifact_with_npm_output(self, os_path_exists_mock, mock_shell_run):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            # Given an NpmPackage step implementer
            npm_test = self.create_given_step_implementer(NpmPackage, parent_work_dir_path=working_dir_path)

            # When I run the step
            step_result = npm_test.run_step()

            # Then the StepResult should have an artifact with the npm output:
            artifact = step_result.get_artifact('npm-output')
            output_file_path = os.path.join(working_dir_path, 'npm_package_output.txt')
            self.assertEqual(artifact, StepResultArtifact(
                name='npm-output',
                value=output_file_path,
                description="Standard out and standard error from 'npm install'."
            ))
