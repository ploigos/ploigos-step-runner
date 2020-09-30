
import os
import re
import unittest
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tssc import TSSCException
from tssc.step_implementers.validate_environment_configuration import \
    Configlint

class TestStepImplementerConfiglint(BaseStepImplementerTestCase):
    @staticmethod
    def create_config_lint_side_effect(
        config_lint_stdout="",
        config_lint_stderr="",
        config_lint_fail=False
    ):
        def config_lint_side_effect(*args, **kwargs):
            kwargs['_out'](config_lint_stdout)
            kwargs['_err'](config_lint_stderr)

            if config_lint_fail:
                raise sh.ErrorReturnCode_255(
                    'config-lint',
                    bytes(config_lint_stdout, 'utf-8'),
                    bytes(config_lint_stderr, 'utf-8')
                )

        return config_lint_side_effect

    @patch('sh.config_lint', create=True)
    def test_configlint_missing_options_and_runtime(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('config-file-to-validate.yml', yml_file.encode())
            file_to_validate_file_path = str(os.path.join(temp_dir.path, 'config-file-to-validate.yml'))
            tssc_results = '''tssc-results:
                validate-environment-configuration:
                        'badoptions':
                            {
                                'yml_path':''' + file_to_validate_file_path + '''
                            }
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules_content = ''
            temp_dir.write('config-lint.rules', configlint_rules_content.encode())
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
                            'yml_path': file_to_validate_file_path
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
            temp_dir.write('config-file-to-validate.yml', yml_file.encode())
            file_to_validate_file_path = str(os.path.join(temp_dir.path, 'config-file-to-validate.yml'))
            tssc_results = '''tssc-results:
                validate-environment-configuration:
                    'badoptions':
                            {
                                'yml_path':''' + file_to_validate_file_path + '''
                            }
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules_content = ''
            temp_dir.write('config-lint.rules', configlint_rules_content.encode())
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
                            'yml_path': file_to_validate_file_path
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
            temp_dir.write('config-file-to-validate.yml', yml_file.encode())
            file_to_validate_file_path = os.path.join(temp_dir.path, 'config-file-to-validate.yml')
            tssc_results = '''tssc-results:
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules_content = ''
            temp_dir.write('config-lint.rules', configlint_rules_content.encode())
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
                'yml_path': file_to_validate_file_path
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
        kube_label_app_expected_value = 'foo-app'

        with TempDirectory() as temp_dir:
            # write config file to validate
            file_to_validate_contents = f"""---
kind: Deployment
spec:
  template:
    metadata:
      creationTimestamp: null
      labels:
        app: {kube_label_app_expected_value}
"""
            temp_dir.write('config-file-to-validate.yml', file_to_validate_contents.encode())
            file_to_validate_file_path = str(os.path.join(temp_dir.path, 'config-file-to-validate.yml'))

            # write config-lint rules file
            configlint_rules_content = f"""version: 1
description: Rules for Kubernetes spec files
type: Kubernetes
files:
  - "*.yml"

rules:

# Rule to check for sidecar annotation in Deployment
- id: TSSC_TEST_EXAMPLE_LABEL
  severity: FAILURE
  message: Deployment example for a label
  resource: Deployment
  assertions:
    - key: spec.template.metadata.labels.app
      op: contains
      value: '{kube_label_app_expected_value}'
"""
            config_lint_rules_file_name = 'config-lint-test-rules.yml'
            temp_dir.write(config_lint_rules_file_name, configlint_rules_content.encode())
            config_lint_rules_file_path = os.path.join(temp_dir.path, config_lint_rules_file_name)


            # write results thus far
            tssc_results = f"""---
tssc-results:
    validate-environment-configuration:
        'options':
            'yml_path': '{file_to_validate_file_path}'
"""
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())

            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'Configlint',
                        'config': {
                            'rules': config_lint_rules_file_path
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
                            'yml_path': file_to_validate_file_path
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
            configlint_mock.side_effect = \
                TestStepImplementerConfiglint.create_config_lint_side_effect(config_lint_stdout)

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='validate-environment-configuration',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args,
                expected_stdout=config_lint_stdout,
                expected_stderr=None
            )

    @patch('sh.config_lint', create=True)
    def test_configlint_missing_rule(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('config-file-to-validate.yml', yml_file.encode())
            file_to_validate_file_path = str(os.path.join(temp_dir.path, 'config-file-to-validate.yml'))
            # write results thus far
            tssc_results = f"""---
tssc-results:
    validate-environment-configuration:
        'options':
            'yml_path': '{file_to_validate_file_path}'
"""
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules_content = ''
            temp_dir.write('config-lint.rules', configlint_rules_content.encode())
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
                            'yml_path': file_to_validate_file_path
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
            temp_dir.write('config-file-to-validate.yml', yml_file.encode())
            file_to_validate_file_path = str(os.path.join(temp_dir.path, 'config-file-to-validate.yml'))

            # write results thus far
            tssc_results = f"""---
tssc-results:
    validate-environment-configuration:
        'options':
            'yml_path': '{file_to_validate_file_path}'
"""
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())

            configlint_rules_content = ''
            temp_dir.write('config-lint.rules', configlint_rules_content.encode())
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
                            'yml_path': file_to_validate_file_path
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
                r'Error invoking config-lint: .*'
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'validate-environment-configuration',
                    config,
                    expected_step_results, runtime_args
                )

    @patch('sh.config_lint', create=True)
    def test_configlint_missing_yml_file(self, configlint_mock):
        with TempDirectory() as temp_dir:
            yml_file = ''
            temp_dir.write('badconfig-file-to-validate.yml', yml_file.encode())
            file_to_validate_file_path = str(os.path.join(temp_dir.path, 'config-file-to-validate.yml'))

            # write results thus far
            tssc_results = f"""---
tssc-results:
    validate-environment-configuration:
        'options':
            'yml_path': '{file_to_validate_file_path}'
"""
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())

            configlint_rules_content = ''
            temp_dir.write('config-lint.rules', configlint_rules_content.encode())
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
                            'yml_path': file_to_validate_file_path
                        },
                        'report-artifacts': [
                        ]
                    }
                }
            }
            with self.assertRaisesRegex(
                ValueError,
                r'Specified file in yml_path not found: ' + file_to_validate_file_path
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'validate-environment-configuration',
                    config,
                    expected_step_results, runtime_args
                )

    @patch('sh.config_lint', create=True)
    def test_configlint_failed_validation(self, configlint_mock):
        kube_label_app_expected_value = 'foo-app'

        with TempDirectory() as temp_dir:
            # write config file to validate
            file_to_validate_contents = f"""---
kind: Deployment
spec:
  template:
    metadata:
      creationTimestamp: null
      labels:
        app: {kube_label_app_expected_value}
"""
            temp_dir.write('config-file-to-validate.yml', file_to_validate_contents.encode())
            file_to_validate_file_path = str(os.path.join(temp_dir.path, 'config-file-to-validate.yml'))

            # write config-lint rules file
            configlint_rules_content = f"""version: 1
description: Rules for Kubernetes spec files
type: Kubernetes
files:
  - "*.yml"

rules:

# Rule to check for sidecar annotation in Deployment
- id: TSSC_TEST_EXAMPLE_LABEL
  severity: FAILURE
  message: Deployment example for a label
  resource: Deployment
  assertions:
    - key: spec.template.metadata.labels.app
      op: contains
      value: '{kube_label_app_expected_value}'
"""
            config_lint_rules_file_name = 'config-lint-test-rules.yml'
            temp_dir.write(config_lint_rules_file_name, configlint_rules_content.encode())
            config_lint_rules_file_path = os.path.join(temp_dir.path, config_lint_rules_file_name)


            # write results thus far
            tssc_results = f"""---
tssc-results:
    validate-environment-configuration:
        'options':
            'yml_path': '{file_to_validate_file_path}'
"""
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())

            config = {
                'tssc-config': {
                    'validate-environment-configuration': {
                        'implementer': 'Configlint',
                        'config': {
                            'rules': config_lint_rules_file_path
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
                            'yml_path': file_to_validate_file_path
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

            config_lint_stdout = "mock stdout"
            config_lint_stderr = "mock stderr - validation error"
            configlint_mock.side_effect = \
                TestStepImplementerConfiglint.create_config_lint_side_effect(
                    config_lint_stdout=config_lint_stdout,
                    config_lint_stderr=config_lint_stderr,
                    config_lint_fail=True
                )

            with self.assertRaisesRegex(
                TSSCException,
                r'Failed config-lint scan. See standard out and standard error.'
            ):
                self.run_step_test_with_result_validation(
                    temp_dir=temp_dir,
                    step_name='validate-environment-configuration',
                    config=config,
                    expected_step_results=expected_step_results,
                    runtime_args=runtime_args,
                    expected_stdout=config_lint_stdout,
                    expected_stderr=config_lint_stderr
                )
