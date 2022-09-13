import os
from unittest.mock import patch
from ploigos_step_runner.results import WorkflowResult
from ploigos_step_runner.step_implementers.package import DotnetPackage
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


@patch('ploigos_step_runner.step_implementers.shared.npm_generic.Shell.run')  # Given a shell
class TestStepImplementerDotnetPackage(BaseStepImplementerTestCase):

    def test_run_step_executes_dotnet(self, mock_shell):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured like:
            step_implementer = self.create_step_implementer(test_dir, {
                'csproj-file': 'app.csproj'
            })

            # WHEN I run the step
            actual_step_result = step_implementer._run_step()

            # THEN it should run a shell command like `dotnet publish app.csproj`
            expected_output_file_path = os.path.join(test_dir.path, 'working', 'package', 'dotnet_publish_output.txt')
            mock_shell.assert_any_call(
                'dotnet',
                args=['publish', 'app.csproj'],
                output_file_path=expected_output_file_path
            )

    def test_run_step_returns_result(self, dotnet_shell_command_mock):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured like:
            step_implementer = self.create_step_implementer(test_dir, {
                'csproj-file': 'app.csproj'
            })

            # WHEN I run the step
            actual_step_result = step_implementer._run_step()

            # THEN it should return a StepResult
            self.assertIsNotNone(actual_step_result)

    def test_package_command_required_config(self, dotnet_shell_command_mock):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer
            step_implementer = self.create_step_implementer(test_dir, {})

            # WHEN I check the required configuration properties
            required_keys = step_implementer._required_config_or_result_keys()

            # THEN they should look like:
            self.assertCountEqual(required_keys, ['csproj-file']) # "assertCountEqual" is really unordered list comparison

    def test_package_with_configuration_flag(self, mock_shell):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured to use a dotnet configuration called 'Release'
            step_implementer = self.create_step_implementer(test_dir, {
                'csproj-file': 'app.csproj',
                'configuration': 'Release'
            })

            # WHEN I run the step
            actual_step_result = step_implementer._run_step()

            # THEN it should run a shell command like 'dotnet publish app.csproj -c Release'
            expected_output_file_path = os.path.join(test_dir.path, 'working', 'package', 'dotnet_publish_output.txt')
            mock_shell.assert_any_call(
                'dotnet',
                args=['-c', 'Release', 'publish', 'app.csproj'],
                output_file_path=expected_output_file_path
            )

    def create_step_implementer(self, test_dir, step_config):
        parent_work_dir_path = os.path.join(test_dir.path, 'working')
        return self.create_given_step_implementer(
            step_implementer=DotnetPackage,
            step_config=step_config,
            step_name='package',
            implementer='DotnetPackage',
            workflow_result=WorkflowResult(),
            parent_work_dir_path=parent_work_dir_path
        )
