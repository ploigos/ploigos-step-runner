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
            'auto-increment-all-module-versions': True,
            'auto-increment-version-segment': None,
            'csproj-file': 'dotnet-app.csproj',
            'tls-verify': True
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Dotnet._required_config_or_result_keys()
        expected_required_keys = ['csproj-file']
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('dotnet-app.csproj', b'''<Project Sdk="Microsoft.NET.Sdk">
                <PropertyGroup>
                <OutputType>Exe</OutputType>
                <TargetFramework>net6.0</TargetFramework>
                <RootNamespace>dotnet-app</RootNamespace>
                <ImplicitUsings>enable</ImplicitUsings>
                <Nullable>enable</Nullable>
                </PropertyGroup>
            </Project>''')
            csproj_file_path = os.path.join(temp_dir.path, 'dotnet-app.csproj')

            step_config = {
                'csproj-file': csproj_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Dotnet',
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_package_file_does_not_exist(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            csproj_file_path = os.path.join(temp_dir.path, 'dotnet-app.csproj')

            step_config = {
                'csproj-file': csproj_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Dotnet',
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                AssertionError,
                rf"Given csproj file \(csproj-file\) does not exist: {csproj_file_path}"
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_bad_auto_increment_version_string(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('dotnet-app.csproj', b'''<Project Sdk="Microsoft.NET.Sdk">
                <PropertyGroup>
                <OutputType>Exe</OutputType>
                <TargetFramework>net6.0</TargetFramework>
                <RootNamespace>dotnet-app</RootNamespace>
                <ImplicitUsings>enable</ImplicitUsings>
                <Nullable>enable</Nullable>
                <Version>1.2.0</Version>
                </PropertyGroup>
            </Project>''')

            csproj_file_path = os.path.join(temp_dir.path, 'dotnet-app.csproj')
            auto_increment_version_segment = 'build-number'

            step_config = {
                'csproj-file': csproj_file_path,
                'auto-increment-version-segment': auto_increment_version_segment
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Dotnet',
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesMessage(
                AssertionError,
                rf'Given auto increment version segment (auto-increment-version-segment)'
                rf' must be one of [major, minor, patch]: {auto_increment_version_segment}'
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_run_step_pass(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('dotnet-app.csproj', b'''<Project Sdk="Microsoft.NET.Sdk">
                <PropertyGroup>
                <OutputType>Exe</OutputType>
                <TargetFramework>net6.0</TargetFramework>
                <RootNamespace>dotnet-app</RootNamespace>
                <ImplicitUsings>enable</ImplicitUsings>
                <Nullable>enable</Nullable>
                </PropertyGroup>
            </Project>''')
            csproj_file_path = os.path.join(temp_dir.path, 'dotnet-app.csproj')

            step_config = {
                'csproj-file': csproj_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Dotnet',
                parent_work_dir_path=parent_work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Dotnet',
                sub_step_implementer_name='Dotnet'
            )
            expected_step_result.add_artifact(name='framework-version', value='net6.0')

            self.assertEqual(result, expected_step_result)


    @patch('ploigos_step_runner.step_implementers.generate_metadata.maven.run_maven')
    def test_run_step_pass_increment_major_version(
            self,
            mock_run_maven,
            mock_maven_settings
    ):
        with TempDirectory() as temp_dir:
            # Test setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('pom.xml', b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>41.1.12</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {
                'pom-file': pom_file_path,
                'auto-increment-version-segment': 'major'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Maven',
                parent_work_dir_path=parent_work_dir_path,
            )

            mock_run_maven.return_value = '42.0.0'

            # Invoke method under test
            result = step_implementer._run_step()

            # Assertions / Validations
            mock_run_maven.assert_has_calls([
                call(
                    mvn_output_file_path=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt',
                    settings_file='/fake/settings.xml',
                    pom_file=pom_file_path,
                    phases_and_goals=[
                        'build-helper:parse-version',
                        'versions:set',
                        'versions:commit'
                    ],
                    additional_arguments=[
                        r'-DnewVersion=${parsedVersion.nextMajorVersion}.0.0',
                        '-DprocessAllModules'
                    ]
                ),
                call(
                    mvn_output_file_path=f'{parent_work_dir_path}/generate-metadata/mvn_evaluate_project_version.txt',
                    settings_file='/fake/settings.xml',
                    pom_file=pom_file_path,
                    phases_and_goals=[
                        'help:evaluate'
                    ],
                    additional_arguments=[
                        '-Dexpression=project.version',
                        '--batch-mode',
                        '-q',
                        '-DforceStdout'
                    ]
                )
            ])

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven"
                            " to auto increment version.",
                name='maven-auto-increment-version-output',
                value=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt'
            )
            expected_step_result.add_artifact(name='app-version', value='42.0.0')

            self.assertEqual(result, expected_step_result)

    @patch.object(
        Maven,
        'maven_settings_file',
        new_callable=PropertyMock,
        return_value='/fake/settings.xml'
    )
    @patch('ploigos_step_runner.step_implementers.generate_metadata.maven.run_maven')
    def test_run_step_pass_increment_minor_version(
            self,
            mock_run_maven,
            mock_maven_settings
    ):
        with TempDirectory() as temp_dir:
            # Test setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('pom.xml', b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>41.1.12</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {
                'pom-file': pom_file_path,
                'auto-increment-version-segment': 'minor'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Maven',
                parent_work_dir_path=parent_work_dir_path,
            )

            mock_run_maven.return_value = '41.2.0'

            # Invoke method under test
            result = step_implementer._run_step()

            # Assertions / Validations
            mock_run_maven.assert_has_calls([
                call(
                    mvn_output_file_path=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt',
                    settings_file='/fake/settings.xml',
                    pom_file=pom_file_path,
                    phases_and_goals=[
                        'build-helper:parse-version',
                        'versions:set',
                        'versions:commit'
                    ],
                    additional_arguments=[
                        r'-DnewVersion=${parsedVersion.majorVersion}.${parsedVersion.nextMinorVersion}.0',
                        '-DprocessAllModules'
                    ]
                ),
                call(
                    mvn_output_file_path=f'{parent_work_dir_path}/generate-metadata/mvn_evaluate_project_version.txt',
                    settings_file='/fake/settings.xml',
                    pom_file=pom_file_path,
                    phases_and_goals=[
                        'help:evaluate'
                    ],
                    additional_arguments=[
                        '-Dexpression=project.version',
                        '--batch-mode',
                        '-q',
                        '-DforceStdout'
                    ]
                )
            ])

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven"
                            " to auto increment version.",
                name='maven-auto-increment-version-output',
                value=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt'
            )
            expected_step_result.add_artifact(name='app-version', value='41.2.0')

            self.assertEqual(result, expected_step_result)


    def test_run_step_pass_increment_patch_version(
            self,
            mock_run_maven,
            mock_maven_settings
    ):
        with TempDirectory() as temp_dir:
            # Test setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('dotnet-app.csproj', b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>41.1.12</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {
                'pom-file': pom_file_path,
                'auto-increment-version-segment': 'patch'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Dotnet',
                parent_work_dir_path=parent_work_dir_path,
            )

            mock_run_maven.return_value = '41.1.13'

            # Invoke method under test
            result = step_implementer._run_step()

            # Assertions / Validations
            mock_run_maven.assert_has_calls([
                call(
                    mvn_output_file_path=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt',
                    settings_file='/fake/settings.xml',
                    pom_file=pom_file_path,
                    phases_and_goals=[
                        'build-helper:parse-version',
                        'versions:set',
                        'versions:commit'
                    ],
                    additional_arguments=[
                        r'-DnewVersion=${parsedVersion.majorVersion}'
                        r'.${parsedVersion.minorVersion}'
                        r'.${parsedVersion.nextIncrementalVersion}',
                        '-DprocessAllModules'
                    ]
                ),
                call(
                    mvn_output_file_path=f'{parent_work_dir_path}/generate-metadata/mvn_evaluate_project_version.txt',
                    settings_file='/fake/settings.xml',
                    pom_file=pom_file_path,
                    phases_and_goals=[
                        'help:evaluate'
                    ],
                    additional_arguments=[
                        '-Dexpression=project.version',
                        '--batch-mode',
                        '-q',
                        '-DforceStdout'
                    ]
                )
            ])

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven"
                            " to auto increment version.",
                name='maven-auto-increment-version-output',
                value=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt'
            )
            expected_step_result.add_artifact(name='app-version', value='41.1.13')

            self.assertEqual(result, expected_step_result)

    @patch.object(
        Maven,
        'maven_settings_file',
        new_callable=PropertyMock,
        return_value='/fake/settings.xml'
    )
    @patch('ploigos_step_runner.step_implementers.generate_metadata.maven.run_maven')
    def test_run_step_pass_increment_patch_version_do_not_increment_all_modules(
            self,
            mock_run_maven,
            mock_maven_settings
    ):
        with TempDirectory() as temp_dir:
            # Test setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('pom.xml', b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>41.1.12</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {
                'pom-file': pom_file_path,
                'auto-increment-version-segment': 'patch',
                'auto-increment-all-module-versions': False
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Maven',
                parent_work_dir_path=parent_work_dir_path,
            )

            mock_run_maven.return_value = '41.1.13'

            # Invoke method under test
            result = step_implementer._run_step()

            # Assertions / Validations
            mock_run_maven.assert_has_calls([
                call(
                    mvn_output_file_path=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt',
                    settings_file='/fake/settings.xml',
                    pom_file=pom_file_path,
                    phases_and_goals=[
                        'build-helper:parse-version',
                        'versions:set',
                        'versions:commit'
                    ],
                    additional_arguments=[
                        r'-DnewVersion=${parsedVersion.majorVersion}'
                        r'.${parsedVersion.minorVersion}'
                        r'.${parsedVersion.nextIncrementalVersion}'
                    ]
                ),
                call(
                    mvn_output_file_path=f'{parent_work_dir_path}/generate-metadata/mvn_evaluate_project_version.txt',
                    settings_file='/fake/settings.xml',
                    pom_file=pom_file_path,
                    phases_and_goals=[
                        'help:evaluate'
                    ],
                    additional_arguments=[
                        '-Dexpression=project.version',
                        '--batch-mode',
                        '-q',
                        '-DforceStdout'
                    ]
                )
            ])

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven"
                            " to auto increment version.",
                name='maven-auto-increment-version-output',
                value=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt'
            )
            expected_step_result.add_artifact(name='app-version', value='41.1.13')

            self.assertEqual(result, expected_step_result)

    @patch.object(
        Maven,
        'maven_settings_file',
        new_callable=PropertyMock,
        return_value='/fake/settings.xml'
    )
    @patch('ploigos_step_runner.step_implementers.generate_metadata.maven.run_maven')
    def test_run_step_fail_increment_version(
            self,
            mock_run_maven,
            mock_maven_settings
    ):
        with TempDirectory() as temp_dir:
            # Test setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('pom.xml', b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>41.1.12</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {
                'pom-file': pom_file_path,
                'auto-increment-version-segment': 'patch'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Maven',
                parent_work_dir_path=parent_work_dir_path,
            )

            mock_run_maven.side_effect = StepRunnerException('Whoops!')

            # Invoke method under test
            result = step_implementer._run_step()

            # Assertions / Validations
            mock_run_maven.assert_called_once_with(
                mvn_output_file_path=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt',
                settings_file='/fake/settings.xml',
                pom_file=pom_file_path,
                phases_and_goals=[
                    'build-helper:parse-version',
                    'versions:set',
                    'versions:commit'
                ],
                additional_arguments=[
                    r'-DnewVersion=${parsedVersion.majorVersion}'
                    r'.${parsedVersion.minorVersion}'
                    r'.${parsedVersion.nextIncrementalVersion}',
                    '-DprocessAllModules'
                ]
            )

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.success = False
            expected_step_result.message = f"Error running maven to auto increment version segment" \
                f" (patch)." \
                f" More details maybe found in 'maven-auto-increment-version-output'" \
                f" report artifact: Whoops!"
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven"
                            " to auto increment version.",
                name='maven-auto-increment-version-output',
                value=f'{parent_work_dir_path}/generate-metadata/mvn_versions_set_output.txt'
            )

            self.assertEqual(result, expected_step_result)

    @patch('ploigos_step_runner.step_implementers.generate_metadata.maven.run_maven')
    def test_run_step_fail_missing_version_in_csproj_file(
            self,
            mock_run_maven
    ):
        mock_run_maven.side_effect = StepRunnerException("no version found")

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('pom.xml', b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {
                'pom-file': pom_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Maven',
                parent_work_dir_path=parent_work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.success = False
            expected_step_result.message = f'Error running maven to get the project version: ' \
                    f'no version found' \
                    f'Could not get project version from given pom file' \
                    f' ({pom_file_path})'

            self.assertEqual(result, expected_step_result)
