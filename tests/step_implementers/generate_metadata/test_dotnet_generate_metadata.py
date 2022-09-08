# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
from unittest.mock import patch, call, PropertyMock

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.step_implementers.generate_metadata import Dotnet
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException


class TestStepImplementerDotnetGenerateMetadata(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Dotnet,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = Dotnet.step_implementer_config_defaults()
        expected_defaults = {
            'csproj-file': 'dotnet-app.csproj'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Dotnet._required_config_or_result_keys()
        expected_required_keys = ['csproj-file']
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_package_file_does_not_exist(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            csproj_file_path = os.path.join(temp_dir.path, 'dotnet-app.csproj')
            step_config = {
                'csproj-file': csproj_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='Dotnet',
                parent_work_dir_path=parent_work_dir_path
            )

            with self.assertRaisesRegex(
                    AssertionError,
                    rf"Given csproj file \(csproj-file\) does not exist: {csproj_file_path}"
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_run_step_pass(self):

        # GIVEN an XML file with a Version element
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            csproj_file_name = 'dotnet-app.csproj'
            temp_dir.write(csproj_file_name, b'''<Project Sdk="Microsoft.NET.Sdk">
                <PropertyGroup>
                <OutputType>Exe</OutputType>
                <TargetFramework>net6.0</TargetFramework>
                <RootNamespace>dotnet-app</RootNamespace>
                <ImplicitUsings>enable</ImplicitUsings>
                <Nullable>enable</Nullable>
                <Version>1.2.0</Version>
                </PropertyGroup>
            </Project>''')

            csproj_file_path = os.path.join(temp_dir.path, csproj_file_name)

            step_config = {'csproj-file': csproj_file_path}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Dotnet',
                parent_work_dir_path=parent_work_dir_path,
            )
            # WHEN I run the step
            result = step_implementer._run_step()

            print("result: " + str(result))

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Dotnet',
                sub_step_implementer_name='Dotnet'
            )
            expected_step_result.add_artifact(name='app-version', value='1.2.0')

            # THEN the method should correctly find the Version element
            self.assertEqual(result, expected_step_result)

    def test_run_step_fail_missing_version_in_csproj_file(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            csproj_file_name = 'dotnet-app.csproj'
            temp_dir.write(csproj_file_name, b'''<Project Sdk="Microsoft.NET.Sdk">
                                                  <PropertyGroup>
                                                  <OutputType>Exe</OutputType>
                                                  <TargetFramework>net6.0</TargetFramework>
                                                  <RootNamespace>dotnet-app</RootNamespace>
                                                  <ImplicitUsings>enable</ImplicitUsings>
                                                  <Nullable>enable</Nullable>
                                                  </PropertyGroup>
                                                 </Project>''')
            csproj_file_path = os.path.join(temp_dir.path, csproj_file_name)

            step_config = {'csproj-file': csproj_file_path}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Dotnet',
                parent_work_dir_path=parent_work_dir_path,
            )

            result = step_implementer._run_step()

            print(result)

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Dotnet',
                sub_step_implementer_name='Dotnet',
            )
            expected_step_result.success = False
            expected_step_result.message = f"Could not get project version from given csproj file: ({csproj_file_path})"

            self.assertEqual(result, expected_step_result)
