import os

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.step_implementers.generate_metadata import Npm
from ploigos_step_runner.results import StepResult


class TestStepImplementerGenerateMetadataNpm(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Npm,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = Npm.step_implementer_config_defaults()
        expected_defaults = {
            'package-file': 'package.json'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Npm._required_config_or_result_keys()
        expected_required_keys = [
            'package-file'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('package.json', b'''{
              "name": "my-awesome-package",
              "version": "42.1"
            }''')
            package_file_path = os.path.join(temp_dir.path, 'package.json')

            step_config = {
                'package-file': package_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='Npm',
                parent_work_dir_path=parent_work_dir_path
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_package_file_does_not_exist(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            package_file_path = os.path.join(temp_dir.path, 'package.json')
            step_config = {
                'package-file': package_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='Npm',
                parent_work_dir_path=parent_work_dir_path
            )

            with self.assertRaisesRegex(
                AssertionError,
                rf"Given npm package file \(package-file\) does not exist: {package_file_path}"
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_run_step_pass(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('package.json', b'''{
              "name": "my-awesome-package",
              "version": "42.1"
            }''')
            package_file_path = os.path.join(temp_dir.path, 'package.json')

            step_config = {'package-file': package_file_path}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Npm',
                parent_work_dir_path=parent_work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Npm',
                sub_step_implementer_name='Npm'
            )
            expected_step_result.add_artifact(name='app-version', value='42.1')

            self.assertEqual(result, expected_step_result)


    def test_run_step_fail_missing_version_in_package_file(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('package.json', b'''{
              "name": "my-awesome-package"
            }''')
            package_file_path = os.path.join(temp_dir.path, 'package.json')

            step_config = {'package-file': package_file_path}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Npm',
                parent_work_dir_path=parent_work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Npm',
                sub_step_implementer_name='Npm',
            )
            expected_step_result.success = False
            expected_step_result.message = f"Given npm package file ({package_file_path})" + \
                ' does not contain a \"version\" key.'

            self.assertEqual(result, expected_step_result)