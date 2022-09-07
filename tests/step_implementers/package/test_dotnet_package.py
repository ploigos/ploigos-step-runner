import os
from unittest.mock import patch
from ploigos_step_runner.results import WorkflowResult
from ploigos_step_runner.step_implementers.package import DotnetPackage
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase

class TestStepImplementerDotnetPackage(BaseStepImplementerTestCase):

    @patch('sh.dotnet', create=True) # GIVEN a shell command, 'dotnet'
    def test_package_command(self, dotnet_shell_command_mock):

        # GIVEN a DotNetStepImplementer
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
            }
            workflow_result = WorkflowResult()
            step_implementer = self.create_given_step_implementer(
                step_implementer=DotnetPackage,
                step_config=step_config,
                step_name='package',
                implementer='DotnetPackage',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

        # WHEN I run the step
        actual_step_result = step_implementer._run_step()

        # THEN it should run a shell command, 'dotnet build'
        dotnet_shell_command_mock.assert_any_call(
            'build'
        )

    @patch('sh.dotnet', create=True) # GIVEN a shell command, 'dotnet'
    def test_package_with_csproj_command(self, dotnet_shell_command_mock):

        # GIVEN a config that specifies a csproj file named app.csproj
        step_config = {
            'csproj-file': 'app.csproj'
        }

        # GIVEN a DotNetStepImplementer
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            workflow_result = WorkflowResult()
            step_implementer = self.create_given_step_implementer(
                step_implementer=DotnetPackage,
                step_config=step_config,
                step_name='package',
                implementer='DotnetPackage',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

        # WHEN I run the step
        actual_step_result = step_implementer._run_step()

        # THEN it should run a shell command like 'dotnet build app.csproj'
        dotnet_shell_command_mock.assert_any_call(
            'build',
            'app.csproj'
        )

    @patch('sh.dotnet', create=True) # GIVEN a shell command, 'dotnet'
    def test_package_with_configuration_flag(self, dotnet_shell_command_mock):

        # GIVEN a config that specifies a configuration flag value named 'Release'
        step_config = {
            'csproj-file': 'app.csproj',
            'configuration': 'Release'
        }

        # GIVEN a DotNetStepImplementer
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            workflow_result = WorkflowResult()
            step_implementer = self.create_given_step_implementer(
                step_implementer=DotnetPackage,
                step_config=step_config,
                step_name='package',
                implementer='DotnetPackage',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

        # WHEN I run the step
        actual_step_result = step_implementer._run_step()

        # THEN it should run a shell command like 'dotnet build app.csproj -c Release'
        dotnet_shell_command_mock.assert_any_call(
            'build',
            'app.csproj',
            '-c', 'Release'
        )
