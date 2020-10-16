# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os

from testfixtures import TempDirectory

from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase


class TestStepImplementerGenerateMetadataNpm(BaseStepImplementerTestCase):
    def test_package_file(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('package.json', b'''{
              "name": "my-awesome-package",
              "version": "1.0.0"
            }''')
            package_file_path = os.path.join(temp_dir.path, 'package.json')
            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Npm',
                        'config': {
                            'package-file': str(package_file_path)
                        }
                    }
                }
            }
            expected_step_results = {
                'generate-metadata': {
                    'Npm': {
                        'sub-step-implementer-name': 'Npm',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version':
                                {'value': '1.0.0', 'type': 'str', 'description': ''},
                        }
                    }
                }
            }
            runtime_args = {}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_package_file_missing_version(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('package.json', b'''{
              "name": "my-awesome-package"
            }''')
            package_file_path = os.path.join(temp_dir.path, 'package.json')
            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Npm',
                        'config': {
                            'package-file': str(package_file_path)
                        }
                    }
                }
            }

            expected_step_results = {
                'generate-metadata': {
                    'Npm': {
                        'sub-step-implementer-name': 'Npm',
                        'success': False,
                        'message': f'Given npm package file: {temp_dir.path}/package.json '
                                   f'does not contain a "version" key',
                        'artifacts': {}
                    }
                }
            }
            runtime_args = {'repo-root': str(temp_dir.path), 'build': '1234'}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                expected_step_results=expected_step_results,
                config=config,
                runtime_args=runtime_args
            )

    def test_package_file_missing(self):
        with TempDirectory() as temp_dir:
            package_file_path = 'does_not_exist.json'
            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Npm',
                        'config': {
                            'package-file': str(package_file_path)
                        }
                    }
                }
            }

            expected_step_results = {
                'generate-metadata': {
                    'Npm': {
                        'sub-step-implementer-name': 'Npm',
                        'success': False,
                        'message': 'Given npm package file does not exist: does_not_exist.json',
                        'artifacts': {}
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path), 'build': '1234'}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                expected_step_results=expected_step_results,
                config=config,
                runtime_args=runtime_args
            )

    def test_config_file_package_file_none_value(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Npm',
                        'config': {
                            'package-file': None
                        }
                    }
                }
            }

            # todo: refactor the assert?
            expected_step_results = {
                'generate-metadata': {
                    'Npm': {
                        'sub-step-implementer-name': 'Npm',
                        'success': False,
                        'message': "The runtime step configuration ({'package-file': None}) "
                                   "is missing the required configuration keys (['package-file'])",
                        'artifacts': {}
                    }
                }
            }

            runtime_args = {}

            with self.assertRaisesRegex(
                    AssertionError,
                    r"The runtime step configuration \(\{'package-file': None\}\) "
                    r"is missing the required configuration keys \(\['package-file'\]\)"):
                self.run_step_test_with_result_validation(
                    temp_dir=temp_dir,
                    step_name='generate-metadata',
                    config=config,
                    expected_step_results=expected_step_results,
                    runtime_args=runtime_args
                )
