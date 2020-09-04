import os
import unittest
from unittest.mock import patch

import sh
from testfixtures import TempDirectory

from tests.helpers.test_utils import run_step_test_with_result_validation

from tssc.step_implementers.static_code_analysis import SonarQube


class TestStepImplementerSonarQube(unittest.TestCase):
    @patch('sh.sonar_scanner', create=True)
    def test_sonarqube_ok(self, sonar_mock):
        with TempDirectory() as temp_dir:
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            sonar_properties = '''
                used to test existence of file
            '''
            temp_dir.write('sonar-project.properties', sonar_properties.encode())
            properties = os.path.join(temp_dir.path, 'sonar-project.properties')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'tssc',
                        'service-name': 'tssc-reference-testcase'
                    },
                    'static-code-analysis': {
                        'implementer': 'SonarQube',
                        'config': {
                            'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                            'properties': properties
                        }
                    }
                }
            }
            runtime_args = {
                'user': 'unit.test.user',
                'password': 'unit.test.password'
            }
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata': {
                        'version': '1.0-123abc'
                    },
                    'static-code-analysis': {
                        'result': {
                            'success': True,
                            'message': 'sonarqube step completed - see report-artifacts'
                        },
                        'report-artifacts': [
                            {
                                'name': 'sonarqube result set',
                                'path': f'file://{temp_dir.path}' +
                                        '/tssc-working/static-code-analysis/report-task.txt'
                            }
                        ]
                    }
                }
            }
            run_step_test_with_result_validation(temp_dir, 'static-code-analysis',
                                                 config, expected_step_results, runtime_args)

    @patch('sh.sonar_scanner', create=True)
    def test_sonar_missing_user(self, sonar_mock):
        with TempDirectory() as temp_dir:
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            sonar_properties = '''
                used to test existence of file
            '''
            temp_dir.write('sonar-project.properties', sonar_properties.encode())
            properties = os.path.join(temp_dir.path, 'sonar-project.properties')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'tssc',
                        'service-name': 'tssc-reference-testcase'
                    },
                    'static-code-analysis': {
                        'implementer': 'SonarQube',
                        'config': {
                            'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                            'properties': properties
                        }
                    }
                }
            }
            runtime_args = {
                'password': 'unit.test.password'
            }
            expected_step_results = {
            }

            with self.assertRaisesRegex(
                    AssertionError,
                    r'Either username or password is not set. Neither or both must be set.'):
                run_step_test_with_result_validation(temp_dir, 'static-code-analysis',
                                                     config, expected_step_results, runtime_args)

    @patch('sh.sonar_scanner', create=True)
    def test_sonar_missing_password(self, sonar_mock):
        with TempDirectory() as temp_dir:
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            sonar_properties = '''
                used to test existence of file
            '''
            temp_dir.write('sonar-project.properties', sonar_properties.encode())
            properties = os.path.join(temp_dir.path, 'sonar-project.properties')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'tssc',
                        'service-name': 'tssc-reference-testcase'
                    },
                    'static-code-analysis': {
                        'implementer': 'SonarQube',
                        'config': {
                            'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                            'properties': properties
                        }
                    }
                }
            }
            runtime_args = {
                'user': 'unit.test.user'
            }
            expected_step_results = {
            }
            with self.assertRaisesRegex(
                    AssertionError,
                    r'Either username or password is not set. Neither or both must be set.'):
                run_step_test_with_result_validation(temp_dir, 'static-code-analysis',
                                                     config, expected_step_results, runtime_args)

    @patch('sh.sonar_scanner', create=True)
    def test_sonar_missing_user_and_password(self, sonar_mock):
        with TempDirectory() as temp_dir:
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            sonar_properties = '''
                used to test existence of file
            '''
            temp_dir.write('sonar-project.properties', sonar_properties.encode())
            properties = os.path.join(temp_dir.path, 'sonar-project.properties')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'tssc',
                        'service-name': 'tssc-reference-testcase'
                    },
                    'static-code-analysis': {
                        'implementer': 'SonarQube',
                        'config': {
                            'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                            'properties': properties
                        }
                    }
                }
            }
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata': {
                        'version': '1.0-123abc'
                    },
                    'static-code-analysis': {
                        'result': {
                            'success': True,
                            'message': 'sonarqube step completed - see report-artifacts',
                        },
                        'report-artifacts': [
                            {
                                'name': 'sonarqube result set',
                                'path': f'file://{temp_dir.path}' +
                                        '/tssc-working/static-code-analysis/report-task.txt'
                            }
                        ]
                    }
                }
            }

            run_step_test_with_result_validation(temp_dir, 'static-code-analysis',
                                                 config, expected_step_results)

    @patch('sh.sonar_scanner', create=True)
    def test_sonar_missing_version(self, sonar_mock):
        with TempDirectory() as temp_dir:
            tssc_results = '''tssc-results:
                generate-metadata-bad:
                    version: 1.0-123abc
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            sonar_properties = '''
                used to test existence of file
            '''
            temp_dir.write('sonar-project.properties', sonar_properties.encode())
            properties = os.path.join(temp_dir.path, 'sonar-project.properties')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'tssc',
                        'service-name': 'tssc-reference-testcase'
                    },
                    'static-code-analysis': {
                        'implementer': 'SonarQube',
                        'config': {
                            'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                            'properties': properties
                        }
                    }
                }
            }
            expected_step_results = {
            }

            with self.assertRaisesRegex(
                    ValueError,
                    'Severe error: Generate-metadata results is missing a version tag'):
                run_step_test_with_result_validation(temp_dir, 'static-code-analysis',
                                                     config, expected_step_results)

    @patch('sh.sonar_scanner', create=True)
    def test_sonar_bad_sonar_scanner_results(self, sonar_mock):
        with TempDirectory() as temp_dir:
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            sonar_properties = '''
                used to test existence of file
            '''
            temp_dir.write('sonar-project.properties', sonar_properties.encode())
            properties = os.path.join(temp_dir.path, 'sonar-project.properties')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'tssc',
                        'service-name': 'tssc-reference-testcase'
                    },
                    'static-code-analysis': {
                        'implementer': 'SonarQube',
                        'config': {
                            'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                            'properties': properties
                        }
                    }
                }
            }
            expected_step_results = {}
            sh.sonar_scanner.side_effect = sh.ErrorReturnCode('sonar_scanner',
                                                              b'mock stdout', b'mock error')
            with self.assertRaisesRegex(
                    RuntimeError,
                    'Error invoking sonarscanner'):
                run_step_test_with_result_validation(temp_dir, 'static-code-analysis',
                                                     config, expected_step_results)

    @patch('sh.sonar_scanner', create=True)
    def test_sonarqube_missing_url(self, sonar_mock):
        with TempDirectory() as temp_dir:
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            sonar_properties = '''
                used to test existence of file
            '''
            temp_dir.write('sonar-project.properties', sonar_properties.encode())
            properties = os.path.join(temp_dir.path, 'sonar-project.properties')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'tssc',
                        'service-name': 'tssc-reference-testcase'
                    },
                    'static-code-analysis': {
                        'implementer': 'SonarQube',
                        'config': {
                            'properties': properties
                        }
                    }
                }
            }
            expected_step_results = {
            }
            with self.assertRaisesRegex(
                    AssertionError,
                    r'is missing.*url*'):
                run_step_test_with_result_validation(temp_dir, 'static-code-analysis',
                                                     config, expected_step_results)

    @patch('sh.sonar_scanner', create=True)
    def test_sonarqube_missing_properties_file(self, sonar_mock):
        with TempDirectory() as temp_dir:
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'tssc',
                        'service-name': 'tssc-reference-testcase'
                    },
                    'static-code-analysis': {
                        'implementer': 'SonarQube',
                        'config': {
                            'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                            'properties': 'missingfile'
                        }
                    }
                }
            }
            expected_step_results = {
            }
            with self.assertRaisesRegex(
                    ValueError,
                    r'Properties file in tssc config not found.*'):
                run_step_test_with_result_validation(temp_dir, 'static-code-analysis',
                                                     config, expected_step_results)
