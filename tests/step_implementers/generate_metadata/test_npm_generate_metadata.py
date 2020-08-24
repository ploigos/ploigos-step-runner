import os

import unittest
from testfixtures import TempDirectory

from tssc import TSSCFactory
from tssc.step_implementers.generate_metadata import Npm

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.test_utils import run_step_test_with_result_validation

from test_utils import *

class TestStepImplementerGenerateMetadataNpm(BaseTSSCTestCase):
    def test_package_file(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('package.json',b'''{
              "name": "my-awesome-package",
              "version": "1.0.0"
            }''')
            package_file_path = os.path.join(temp_dir.path, 'package.json')
            results_dir_path = os.path.join(temp_dir.path, 'tssc-resutls')
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
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': '1.0.0'}}}

            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results)


    def test_package_file_missing_version(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('package.json',b'''{
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

            expected_step_results = {}

            with self.assertRaisesRegex(
                    ValueError,
                    r"Given npm package file: " + package_file_path + " does not contain a \"version\" key"):
                run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path), 'build': '1234'})

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

            expected_step_results = {}

            with self.assertRaisesRegex(
                    ValueError,
                    r"Given npm package file does not exist: does_not_exist.json"):
                run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path), 'build': '1234'})

    def test_config_file_package_file_none_value(self):
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
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                AssertionError,
                r"The runtime step configuration \(\{'package-file': None\}\) is missing the required configuration keys \(\['package-file'\]\)"):
            factory.run_step('generate-metadata')
