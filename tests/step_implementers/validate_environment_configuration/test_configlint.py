import os
import unittest
from unittest.mock import patch

import sh
from testfixtures import TempDirectory

from tests.helpers.test_utils import run_step_test_with_result_validation

from tssc.step_implementers.validate_environment_configuration import Configlint


class TestStepImplementerConfiglint(unittest.TestCase):
    @patch('sh.config_lint', create=True)
    def test_configlint_missing_options_and_runtime(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'file.yml'))
            tssc_results = '''tssc-results:
                validate-environment-configuration:
                        'badoptions':
                            {
                                'yml_path':''' + yml_path + '''
                            }
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = ''
            temp_dir.write('config-lint.rules', configlint_rules.encode())
            rules = os.path.join(temp_dir.path, 'config-lint.rules')
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'Configlint',
                        'config': {
                            'rules': rules
                        }
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        },
                        'report-artifacts': [
                        ]
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError,
                    r'yml_path not specified in runtime args or in options'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)
    @patch('sh.config_lint', create=True)
    def test_configlint_missing_options_and_runtime_and_steps(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'file.yml'))
            tssc_results = '''tssc-results:
                validate-environment-configuration:
                    'badoptions':
                            {
                                'yml_path':''' + yml_path + '''
                            }
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = ''
            temp_dir.write('config-lint.rules', configlint_rules.encode())
            rules = os.path.join(temp_dir.path, 'config-lint.rules')
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'Configlint',
                        'config': {
                            'rules': rules
                        }
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        },
                        'report-artifacts': [
                        ]
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError,
                    r'yml_path not specified in runtime args or in options'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)
    @patch('sh.config_lint', create=True)
    def test_configlint_using_runtime(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path: str = os.path.join(temp_dir.path, 'file.yml')
            tssc_results = '''tssc-results:
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = ''
            temp_dir.write('config-lint.rules', configlint_rules.encode())
            rules = os.path.join(temp_dir.path, 'config-lint.rules')
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'Configlint',
                        'config': {
                            'rules': rules
                        }
                    }
                }
            }
            runtime_args = {
                'yml_path': yml_path
            }
            expected_step_results = {
                'tssc-results': {
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint step completed'
                        },
                        'report-artifacts': [
                        ]
                    }
                }
            }

            with self.assertRaisesRegex(
                    AttributeError,
                    r'.*.'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)
    @patch('sh.config_lint', create=True)
    def test_configlint_ok(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'file.yml'))
            tssc_results = '''tssc-results:
                validate-environment-configuration:
                        'options':
                            {
                                'yml_path':''' + yml_path + '''
                            }
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = ''
            temp_dir.write('config-lint.rules', configlint_rules.encode())
            rules = os.path.join(temp_dir.path, 'config-lint.rules')
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'Configlint',
                        'config': {
                            'rules': rules
                        }
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        },
                        'report-artifacts': [
                            {
                                'name' : 'configlint-result-set',
                                'path': f'file://{temp_dir.path}/tssc-working/validate-environment-configuration/configlint_results_file.txt'
                            }
                        ]
                    }
                }
            }
            run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                 config, expected_step_results, runtime_args)
    @patch('sh.config_lint', create=True)
    def test_configlint_missing_rule(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'file.yml'))
            tssc_results = '''tssc-results:
                validate-environment-configuration:
                        'options':
                            {
                                'yml_path':''' + yml_path + '''
                            }
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = ''
            temp_dir.write('config-lint.rules', configlint_rules.encode())
            rules = os.path.join(temp_dir.path, 'badconfig-lint.rules')
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'Configlint',
                        'config': {
                            'missingrules': rules
                        }
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        },
                        'report-artifacts': [
                        ]
                    }
                }
            }
            with self.assertRaisesRegex(
                    ValueError,
                    r'Rules file specified in tssc config not found: ./config-lint.rules'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)

    @patch('sh.config_lint', create=True)
    def test_configlint_bad_sh_call(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('file.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'file.yml'))
            tssc_results = '''tssc-results:
                validate-environment-configuration:
                        'options':
                            {
                                'yml_path':''' + yml_path + '''
                            }
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = ''
            temp_dir.write('config-lint.rules', configlint_rules.encode())
            rules = os.path.join(temp_dir.path, 'config-lint.rules')
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'Configlint',
                        'config': {
                            'rules': rules
                        }
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        },
                        'report-artifacts': [
                        ]
                    }
                }
            }
            sh.config_lint.side_effect = sh.ErrorReturnCode('config_lint',
                                                            b'mock stdout', b'mock error')
            with self.assertRaisesRegex(
                    RuntimeError,
                    r'Error invoking config-lint: .*'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)

    @patch('sh.config_lint', create=True)
    def test_configlint_missing_yml_file(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('badfile.yml', yml_file.encode())
            yml_path = str(os.path.join(temp_dir.path, 'file.yml'))
            tssc_results = '''tssc-results:
                validate-environment-configuration:
                        'options':
                            {
                                'yml_path':''' + yml_path + '''
                            }
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = ''
            temp_dir.write('config-lint.rules', configlint_rules.encode())
            rules = os.path.join(temp_dir.path, 'config-lint.rules')
            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'Configlint',
                        'config': {
                            'rules': rules
                        }
                    }
                }
            }
            runtime_args = {
            }
            expected_step_results = {
                'tssc-results': {
                    'validate-environment-configuration': {
                        'result': {
                            'success': True,
                            'message': 'configlint step completed'
                        },
                        'options': {
                            'yml_path': yml_path
                        },
                        'report-artifacts': [
                        ]
                    }
                }
            }
            with self.assertRaisesRegex(
                    ValueError,
                    r'Specified file in yml_path not found: ' + yml_path):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)
