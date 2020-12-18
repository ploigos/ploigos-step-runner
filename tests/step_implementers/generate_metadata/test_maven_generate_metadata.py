# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.step_implementers.generate_metadata import Maven
from ploigos_step_runner.step_result import StepResult


class TestStepImplementerMavenGenerateMetadata(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Maven,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = Maven.step_implementer_config_defaults()
        expected_defaults = {
            'pom-file': 'pom.xml'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Maven._required_config_or_result_keys()
        expected_required_keys = ['pom-file']
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('pom.xml', b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>42.1</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {
                'pom-file': pom_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_package_file_does_not_exist(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {
                'pom-file': pom_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            with self.assertRaisesRegex(
                AssertionError,
                rf"Given pom file \(pom-file\) does not exist: {pom_file_path}"
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_run_step_pass(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('pom.xml', b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>42.1</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {
                'pom-file': pom_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.add_artifact(name='app-version', value='42.1')

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    def test_run_step_fail_missing_version_in_pom_file(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

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
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.success = False
            expected_step_result.message = f"Given pom file ({pom_file_path}) does not contain " + \
                "a \"version\" key."

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())
