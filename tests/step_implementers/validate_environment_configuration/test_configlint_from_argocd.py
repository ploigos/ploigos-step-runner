import os
import unittest
from unittest.mock import patch

from testfixtures import TempDirectory

from tests.helpers.test_utils import run_step_test_with_result_validation

from tssc.step_implementers.validate_environment_configuration import ConfiglintFromArgocd

class TestStepImplementerConfiglintFromArgo(unittest.TestCase):
    @patch('sh.config_lint', create=True)
    def test_configlint_from_argocd_missing_artifacts(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = '''
               empty file
            '''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'file.yml'))
            file_yml_path = f'file://{yml_path}'
            tssc_results = '''tssc-results:
                deploy:
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'ConfiglintFromArgocd',
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'deploy': {
                        'report-artifacts': [
                            {'name': 'argocd-result-set',
                             'path': file_yml_path
                             }
                        ]
                    },
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint prep step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        }
                    }
                }
            }
            with self.assertRaisesRegex(
                    ValueError,
                    r'Deploy results is missing report-artifacts'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)
    @patch('sh.config_lint', create=True)
    def test_configlint_from_argocd_missing_name(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = '''
               empty file
            '''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'file.yml'))
            file_yml_path = f'file://{yml_path}'
            tssc_results = '''tssc-results:
                deploy:
                   'report-artifacts': [
                       {
                           'name': 'badargocd-result-set',
                           'path':''' + file_yml_path + '''
                       }
                   ]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'ConfiglintFromArgocd',
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'deploy': {
                        'report-artifacts': [
                            {'name': 'argocd-result-set',
                             'path': file_yml_path
                             }
                        ]
                    },
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint prep step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        }
                    }
                }
            }
            with self.assertRaisesRegex(
                    ValueError,
                    r'Deploy results missing yml element name=argocd-result-set'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)
    @patch('sh.config_lint', create=True)
    def test_configlint_from_argocd_missing_yml(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = '''
               empty file
            '''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'badfile.yml'))
            file_yml_path = f'file://{yml_path}'
            tssc_results = '''tssc-results:
                deploy:
                   'report-artifacts': [
                       {
                           'name': 'argocd-result-set',
                           'path':''' + file_yml_path + '''
                       }
                   ]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'ConfiglintFromArgocd',
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'deploy': {
                        'report-artifacts': [
                            {'name': 'argocd-result-set',
                             'path': file_yml_path
                             }
                        ]
                    },
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint prep step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        }
                    }
                }
            }
            with self.assertRaisesRegex(
                    ValueError,
                    r'File not found .*'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)

    @patch('sh.config_lint', create=True)
    def test_configlint_from_argocd_ok(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = '''
               empty file
            '''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'file.yml'))
            file_yml_path = f'file://{yml_path}'
            tssc_results = '''tssc-results:
                deploy:
                   'report-artifacts': [
                       {
                           'name': 'argocd-result-set',
                           'path':''' + file_yml_path + '''
                       }
                   ]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'ConfiglintFromArgocd',
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'deploy': {
                        'report-artifacts': [
                            {'name': 'argocd-result-set',
                             'path': file_yml_path
                             }
                        ]
                    },
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint prep step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        }
                    }
                }
            }
            run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                 config, expected_step_results, runtime_args)
