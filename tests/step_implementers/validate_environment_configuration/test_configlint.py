import os
import unittest
from unittest.mock import patch

import sh
from testfixtures import TempDirectory

from tests.helpers.test_utils import run_step_test_with_result_validation

from tssc.step_implementers.validate_environment_configuration import Configlint


class TestStepImplementerConfiglint(unittest.TestCase):
    @patch('sh.config_lint', create=True)
    def test_configlint_ok(self, configlint_mock):
        with TempDirectory() as temp_dir:
            lint_me_yml = '''
               empty file
            '''
            temp_dir.write('lintme.yml', lint_me_yml.encode())
            path_lintme_yml = os.path.join(temp_dir.path, 'lintme.yml')
            tssc_results = '''tssc-results:
                deploy:
                   'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path':'''+str(path_lintme_yml)+'''
                            }
                        ]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = '''
               used for testing existence of file
            '''
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
                    'deploy': {
                        'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path': path_lintme_yml
                            }
                        ]
                    },
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
            run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                 config, expected_step_results, runtime_args)

    @patch('sh.config_lint', create=True)
    def test_configlint_missing_deploy_argocd(self, configlint_mock):
        with TempDirectory() as temp_dir:
            lint_me_yml = '''
               empty file
            '''
            temp_dir.write('lintme.yml', lint_me_yml.encode())
            path_lintme_yml = os.path.join(temp_dir.path, 'lintme.yml')
            tssc_results = '''tssc-results:
                deploy:
                   'report-artifacts': [
                            {
                                'name': 'badargocd',
                                'path':'''+str(path_lintme_yml)+'''
                            }
                        ]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = '''
               used for testing existence of file
            '''
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
                    'deploy': {
                        'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path': path_lintme_yml
                            }
                        ]
                    },
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
                    ValueError,
                    'Severe error: Deploy results missing yml element name=argocd'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                 config, expected_step_results, runtime_args)

    @patch('sh.config_lint', create=True)
    def test_configlint_missing_deploy(self, configlint_mock):
        with TempDirectory() as temp_dir:
            lint_me_yml = '''
               empty file
            '''
            temp_dir.write('lintme.yml', lint_me_yml.encode())
            path_lintme_yml = os.path.join(temp_dir.path, 'lintme.yml')
            tssc_results = '''tssc-results:
                deploy:
                   'badreport-artifacts': [
                            {
                                'name': 'badargocd',
                                'path':'''+str(path_lintme_yml)+'''
                            }
                        ]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = '''
               used for testing existence of file
            '''
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
                    'deploy': {
                        'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path': path_lintme_yml
                            }
                        ]
                    },
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
                    ValueError,
                    'Severe error: Deploy results is missing report-artifacts'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                 config, expected_step_results, runtime_args)

    @patch('sh.config_lint', create=True)
    def test_configlint_missing_deploy_yml(self, configlint_mock):
        with TempDirectory() as temp_dir:
            lint_me_yml = '''
               empty file
            '''
            temp_dir.write('lintme.yml', lint_me_yml.encode())
            path_lintme_yml = os.path.join(temp_dir.path, 'badlintme.yml')
            tssc_results = '''tssc-results:
                deploy:
                   'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path':'''+str(path_lintme_yml)+'''
                            }
                        ]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = '''
               used for testing existence of file
            '''
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
                    'deploy': {
                        'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path': path_lintme_yml
                            }
                        ]
                    },
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
                    ValueError,
                    r'Severe error: File not found .*'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                 config, expected_step_results, runtime_args)


    @patch('sh.config_lint', create=True)
    def test_configlint_missing_rules(self, configlint_mock):
        with TempDirectory() as temp_dir:
            lint_me_yml = '''
               empty file
            '''
            temp_dir.write('lintme.yml', lint_me_yml.encode())
            path_lintme_yml = os.path.join(temp_dir.path, 'lintme.yml')
            tssc_results = '''tssc-results:
                deploy:
                   'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path':'''+str(path_lintme_yml)+'''
                            }
                        ]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = '''
               used for testing existence of file
            '''
            temp_dir.write('config-lint.rules', configlint_rules.encode())
            rules = os.path.join(temp_dir.path, 'badconfig-lint.rules')
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
                    'deploy': {
                        'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path': path_lintme_yml
                            }
                        ]
                    },
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
                    ValueError,
                    'Rules file in tssc config not found: {file}'.format(file=str(rules))):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                 config, expected_step_results, runtime_args)


    @patch('sh.config_lint', create=True)
    def test_configlint_bad_sh_call(self, configlint_mock):
        with TempDirectory() as temp_dir:
            lint_me_yml = '''
               empty file
            '''
            temp_dir.write('lintme.yml', lint_me_yml.encode())
            path_lintme_yml = os.path.join(temp_dir.path, 'lintme.yml')
            tssc_results = '''tssc-results:
                deploy:
                   'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path':'''+str(path_lintme_yml)+'''
                            }
                        ]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            configlint_rules = '''
               used for testing existence of file
            '''
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
                    'deploy': {
                        'report-artifacts': [
                            {
                                'name': 'argocd',
                                'path': path_lintme_yml
                            }
                        ]
                    },
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
            sh.config_lint.side_effect = sh.ErrorReturnCode('config_lint',
                                                              b'mock stdout', b'mock error')
            with self.assertRaisesRegex(
                    RuntimeError,
                    r'Error invoking config-lint: .*'):
                run_step_test_with_result_validation(temp_dir, 'validate-environment-configuration',
                                                 config, expected_step_results, runtime_args)

