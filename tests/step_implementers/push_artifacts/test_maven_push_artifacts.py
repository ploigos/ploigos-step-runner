import sh
import os

import unittest 
from unittest.mock import patch

from testfixtures import TempDirectory

from tssc.step_implementers.push_artifacts import Maven


from test_utils import *

class TestStepImplementerPushArtifact(unittest.TestCase):

    # ------------ SIMPLE tests that test the config required items
    @patch('sh.mvn', create=True)
    def test_push_artifact_with_repository_url_missing_from_config(self, mvn_mock):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                        }
                    }
                }
            }
            runtime_args = {
                'user': 'unit.test.user',
                'password': 'unit.test.password'
            }
            expected_step_results = {}
            with self.assertRaisesRegex(
                    ValueError,
                    'url must have none empty value in the step configuration'):
                run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results, runtime_args)

    @patch('sh.mvn', create=True)
    def test_push_artifact_with_user_missing_from_runtime(self, mvn_mock):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc/',
                        }
                     }
                 }
            }
            runtime_args = {
                'password': 'unit.test.password',
            }
            expected_step_results = {}
            with self.assertRaisesRegex(
                    ValueError,
                    'Either user or password is not set. Neither or both must be set.'):
                run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results, runtime_args)

    @patch('sh.mvn', create=True)
    def test_push_artifact_with_password_missing_from_runtime(self, mvn_mock):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc/',
                        }
                    }
                }
            }
            runtime_args = {
                'user': 'unit.test.user',
            }
            expected_step_results = {}
            with self.assertRaisesRegex(
                    ValueError,
                    'Either user or password is not set. Neither or both must be set.'):
                run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results, runtime_args)

    # ------------  Tests that require generate-metadata 
    @patch('sh.mvn', create=True)
    def test_push_artifact_with_version_missing_from_results(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                BADversion: 1.0-123abc
              ''')
            config = {
                'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc/',
                        }
                    }
                }
            }
            runtime_args = {
                'user': 'unit.test.user',
                'password': 'unit.test.password'
            }
            expected_step_results = {}
            with self.assertRaisesRegex(
                    ValueError,
                    'Severe error: Generate-metadata does not have a version'):
                run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results, runtime_args)

    @patch('sh.mvn', create=True)
    def test_push_artifact_with_artifacts_missing_from_results(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                version: 1.0-123abc
              ''')
            config = {
               'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc/',
                        }
                    }
                }
            }
            runtime_args = {
                'user': 'user',
                'password': 'password'
            }
            expected_step_results = {}
            with self.assertRaisesRegex(
                    ValueError,
                    'Severe error: Package does not have artifacts'):
                run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results, runtime_args)


    @patch('sh.mvn', create=True)
    def test_push_artifact_with_artifacts_results(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('target')
            temp_dir.write('target/my-app-1.0-SNAPSHOT.jar', b'''sandbox''')
            jar_file_path = os.path.join(temp_dir.path, 'target/my-app-1.0-SNAPSHOT.jar')
            tssc_results='''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
                package:
                    'artifacts': [{
                        'path':'''+ str(jar_file_path)+''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    }]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            config = {
                'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc/',
                        }
                    }
                 }
            }
            runtime_args = {
                'user': 'unit.test.user',
                'password': 'unit.test.password'
            }
            expected_step_results = {
                'tssc-results': 
                    {
                        'generate-metadata': 
                        {
                            'version': '1.0-123abc'
                        }, 
                        'package': 
                        {
                            'artifacts': 
                            [
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'package-type': 'jar', 
                                    'path': str(jar_file_path), 
                                    'pom-path': 'pom.xml'
                                }
                             ]
                        },
                        'push-artifacts': 
                        {
                            'artifacts': 
                            [
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'path': str(jar_file_path), 
                                    'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc//com/mycompany/app/my-app/1.0-123abc/my-app-1.0-123abc.jar', 
                                    'version': '1.0-123abc'
                                }
                            ]
                        }
                    }
            }

            run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results, runtime_args)
    @patch('sh.mvn', create=True)
    def test_push_artifact_with_no_user_password_results(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('target')
            temp_dir.write('target/my-app-1.0-SNAPSHOT.jar', b'''sandbox''')
            jar_file_path = os.path.join(temp_dir.path, 'target/my-app-1.0-SNAPSHOT.jar')
            tssc_results='''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
                package:
                    'artifacts': [{
                        'path':'''+ str(jar_file_path)+''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    }]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            config = {
                'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc/',
                        }
                    }
                 }
            }
            expected_step_results = {
                'tssc-results': 
                    {
                        'generate-metadata': 
                        {
                            'version': '1.0-123abc'
                        }, 
                        'package': 
                        {
                            'artifacts': 
                            [
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'package-type': 'jar', 
                                    'path': str(jar_file_path), 
                                    'pom-path': 'pom.xml'
                                }
                             ]
                        },
                        'push-artifacts': 
                        {
                            'artifacts': 
                            [
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'path': str(jar_file_path), 
                                    'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc//com/mycompany/app/my-app/1.0-123abc/my-app-1.0-123abc.jar', 
                                    'version': '1.0-123abc'
                                }
                            ]
                        }
                    }
            }

            run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results)

    @patch('sh.mvn', create=True)
    def test_push_artifact_with_artifacts_results_bad(self, mock_mvn):

        with TempDirectory() as temp_dir:
            temp_dir.makedir('target')
            temp_dir.write('target/my-app-1.0-SNAPSHOT.jar', b'''sandbox''')
            jar_file_path = os.path.join(temp_dir.path, 'target/my-app-1.0-SNAPSHOT.jar')
            tssc_results='''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
                package:
                    'artifacts': [{
                        'path':'''+ str(jar_file_path)+''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    }]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            runtime_args = {
                'user': 'unit.test.user',
                'password': 'unit.test.password'
            }
            config = {
                'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc/',
                        }
                    }
                 }
            }
            expected_step_results = {
                'tssc-results': 
                    {
                        'generate-metadata': 
                        {
                            'version': '1.0-123abc'
                        }, 
                        'package': 
                        {
                            'artifacts': 
                            [
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'package-type': 'jar', 
                                    'path': str(jar_file_path), 
                                    'pom-path': 'pom.xml'
                                }
                            ]
                        },
                        'push-artifacts': 
                        {
                            'artifacts': 
                            [
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'path': str(jar_file_path), 
                                    'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc//com/mycompany/app/my-app/1.0-123abc/my-app-1.0-123abc.jar', 
                                    'version': '1.0-123abc'
                                }
                            ]
                        }
                    }
            }
            expected_step_results = {}
            sh.mvn.side_effect = sh.ErrorReturnCode('mvn', b'mock stdout', b'mock error')
            with self.assertRaisesRegex(
                    RuntimeError,
                    'Error invoking mvn'):
                run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results, runtime_args)

    @patch('sh.mvn', create=True)
    def test_push_artifact_with_artifacts_results_multi(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('target')
            temp_dir.write('target/my-app-1.0-SNAPSHOT.jar', b'''sandbox''')
            jar_file_path = os.path.join(temp_dir.path, 'target/my-app-1.0-SNAPSHOT.jar')
            tssc_results='''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
                package:
                    'artifacts': [{
                        'path':'''+ str(jar_file_path)+''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    },
                    {
                        'path':'''+ str(jar_file_path)+''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    }]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            config = {
                'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc/',
                        }
                    }
                 }
            }
            runtime_args = {
                'user': 'unit.test.user',
                'password': 'unit.test.password'
            }
            expected_step_results = {
                'tssc-results': 
                    {
                        'generate-metadata': 
                        {
                            'version': '1.0-123abc'
                        }, 
                        'package': 
                        {
                            'artifacts': 
                            [
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'package-type': 'jar', 
                                    'path': str(jar_file_path), 
                                    'pom-path': 'pom.xml'
                                },
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'package-type': 'jar', 
                                    'path': str(jar_file_path), 
                                    'pom-path': 'pom.xml'
                                }
                             ]
                        },
                        'push-artifacts': 
                        {
                            'artifacts': 
                            [
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'path': str(jar_file_path), 
                                    'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc//com/mycompany/app/my-app/1.0-123abc/my-app-1.0-123abc.jar', 
                                    'version': '1.0-123abc'
                                },
                                {
                                    'artifact-id': 'my-app', 
                                    'group-id': 'com.mycompany.app', 
                                    'path': str(jar_file_path), 
                                    'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/tssc//com/mycompany/app/my-app/1.0-123abc/my-app-1.0-123abc.jar', 
                                    'version': '1.0-123abc'
                                }
                            ]
                        }
                    }
            }

            run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results, runtime_args)

