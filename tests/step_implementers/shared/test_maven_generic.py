import os
from pathlib import Path
from shutil import copyfile
from unittest.mock import patch

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.step_implementers.shared.maven_generic import MavenGeneric
from ploigos_step_runner.step_result import StepResult
from ploigos_step_runner.utils.file import create_parent_dir


class SampleMavenStepImplementer(MavenGeneric):
    @staticmethod
    def step_implementer_config_defaults():
        return {}

    @staticmethod
    def _required_config_or_result_keys():
        return []

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        return step_result

class TestStepImplementerSharedMavenGeneric(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=SampleMavenStepImplementer,
            step_config=step_config,
            step_name='foo',
            implementer='SampleMavenStepImplementer',
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.generate_maven_settings')
    def test__generate_maven_settings(self, utils_generate_maven_settings_mock):
        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')
            maven_servers = {
                "internal-mirror": {
                    "id": "internal-server",
                    "username": "ploigos"
                }
            }
            maven_repositories = {
                'internal-mirror-1': {
                    'id': 'internal-server',
                    'url': 'https://foo.example.xyz',
                    'snapshots': 'true',
                    'releases': 'false'
                }
            }
            maven_mirrors = {
                "internal-mirror": {
                    "id": "internal-mirror",
                    "url": "https://artifacts.example.xyz/artifactory/release/",
                    "mirror-of": "*"
                }
            }
            step_config = {
                'maven-servers' : maven_servers,
                'maven-repositories' : maven_repositories,
                'maven-mirrors': maven_mirrors
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            expected_settings_xml_path = '/does/not/matter/settings.xml'
            def utils_generate_maven_settings_mock_side_effect(
                working_dir,
                maven_servers,
                maven_repositories,
                maven_mirrors
            ):
                return expected_settings_xml_path
            utils_generate_maven_settings_mock.side_effect = \
                utils_generate_maven_settings_mock_side_effect

            actual_settings_xml_path = step_implementer._generate_maven_settings()
            self.assertEqual(expected_settings_xml_path, actual_settings_xml_path)

            utils_generate_maven_settings_mock.assert_called_once_with(
                working_dir=work_dir_path,
                maven_servers=maven_servers,
                maven_repositories=maven_repositories,
                maven_mirrors=maven_mirrors
            )

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'fail-on-no-tests': True,
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            Path(pom_file_path).touch()
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_pom_file_does_not_exist(self):
        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'fail-on-no-tests': True,
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            with self.assertRaisesRegex(
                AssertionError,
                rf'Given maven pom file \(pom-file\) does not exist: {pom_file_path}'
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
    def test__get_effective_pom_call_once(self, write_effective_pom_mock):
        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            # mock effective pom
            Path(pom_file_path).touch()
            def write_effective_pom_mock_side_effect(pom_file_path, output_path):
                create_parent_dir(pom_file_path)
                copyfile(pom_file_path, output_path)
            write_effective_pom_mock.side_effect = write_effective_pom_mock_side_effect

            # first call
            expected_effective_pom_path = os.path.join(work_dir_path, 'effective-pom.xml')
            actual_effective_pom_path = step_implementer._get_effective_pom()
            self.assertEqual(actual_effective_pom_path, expected_effective_pom_path)
            write_effective_pom_mock.assert_called_once_with(
                pom_file_path=pom_file_path,
                output_path=expected_effective_pom_path
            )

    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
    def test__get_effective_pom_call_twice(self, write_effective_pom_mock):
        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            # mock effective pom
            Path(pom_file_path).touch()
            def write_effective_pom_mock_side_effect(pom_file_path, output_path):
                create_parent_dir(pom_file_path)
                copyfile(pom_file_path, output_path)
            write_effective_pom_mock.side_effect = write_effective_pom_mock_side_effect

            # first call
            expected_effective_pom_path = os.path.join(work_dir_path, 'effective-pom.xml')
            actual_effective_pom_path = step_implementer._get_effective_pom()
            self.assertEqual(actual_effective_pom_path, expected_effective_pom_path)
            write_effective_pom_mock.assert_called_once_with(
                pom_file_path=pom_file_path,
                output_path=expected_effective_pom_path
            )

            # second call
            write_effective_pom_mock.reset_mock()
            expected_effective_pom_path = os.path.join(work_dir_path, 'effective-pom.xml')
            actual_effective_pom_path = step_implementer._get_effective_pom()
            self.assertEqual(actual_effective_pom_path, expected_effective_pom_path)
            write_effective_pom_mock.assert_not_called()

    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.get_xml_element_by_path')
    @patch.object(MavenGeneric, '_get_effective_pom')
    def test__get_effective_pom_element(self, get_effective_pom_mock, get_xml_element_by_path_mock):
        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_effective_pom_side_effect():
                return '/does/not/matter/pom.xml'
            get_effective_pom_mock.side_effect = get_effective_pom_side_effect

            step_implementer._get_effective_pom_element('foo')
            get_effective_pom_mock.assert_called_once_with()
            get_xml_element_by_path_mock.assert_called_once_with(
                '/does/not/matter/pom.xml',
                'foo',
                default_namespace='mvn'
            )
