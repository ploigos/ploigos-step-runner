
import os
import unittest
from unittest.mock import MagicMock, patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from tssc.step_implementers.validate_environment_configuration import \
    Configlint


class TestStepImplementerConfiglint(BaseStepImplementerTestCase):
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
                self.run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
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
                self.run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
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
                self.run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
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

            config_lint_stdout = 'success'
            config_lint_result_mock = MagicMock()
            config_lint_result_mock.stdout = config_lint_stdout

            configlint_mock.side_effect = config_lint_stdout

            expected_stdout = config_lint_stdout
            expected_stderr = ""

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='validate-environment-configuration',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args,
                expected_stdout=expected_stdout,
                expected_stderr=expected_stderr
            )

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
                self.run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
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
                self.run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
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
                self.run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                     config, expected_step_results, runtime_args)
