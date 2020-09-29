import os
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase


class TestStepImplementerPushArtifact(BaseStepImplementerTestCase):

    # ------------ SIMPLE tests that test the config required items
    @patch('sh.mvn', create=True)
    def test_push_artifact_with_repo_id_missing_from_config(self, mvn_mock):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'push-artifacts': {
                        'implementer': 'Maven'
                    }
                }
            }
            runtime_args = {}
            expected_step_results = {}
            with self.assertRaisesRegex(
                    AssertionError,
                    'The .* configuration .* is missing .*maven-push-artifact-repo-id.*'):
                self.run_step_test_with_result_validation(temp_dir, 'push-artifacts',
                                                     config, expected_step_results, runtime_args)

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
                            'maven-push-artifact-repo-id': 'id',
                            'maven-push-artifact-repo-url': 'repo',
                        }
                    }
                }
            }
            runtime_args = {}
            expected_step_results = {}
            with self.assertRaisesRegex(
                    ValueError,
                    'generate-metadata results missing version'):
                self.run_step_test_with_result_validation(temp_dir, 'push-artifacts',
                                                     config, expected_step_results, runtime_args)

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
                   'global-defaults': {
                       'maven-servers': [
                           {'id': 'ID1', 'username': 'USER1', 'password': 'PW1'},
                           {'id': 'ID2'}
                       ],
                       'maven-repositories': [
                           {'id': 'ID1', 'url': 'URL1', 'snapshots': 'true', 'releases': 'false'},
                           {'id': 'ID2', 'url': 'URL2'}
                       ],
                       'maven-mirrors': [
                           {'id': 'ID1', 'url': 'URL1', 'mirror-of': '*'},
                           {'id': 'ID2', 'url': 'URL2', 'mirror-of': '*'}
                       ],
                   },
                   'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'maven-push-artifact-repo-id': 'repoid',
                            'maven-push-artifact-repo-url': 'repourl'
                        }
                    }
                }
            }
            runtime_args = {}
            expected_step_results = {}
            with self.assertRaisesRegex(
                    ValueError,
                    'package results missing artifacts'):
                self.run_step_test_with_result_validation(temp_dir, 'push-artifacts',
                                                     config, expected_step_results, runtime_args)


    @patch('sh.mvn', create=True)
    def test_push_artifact_with_artifacts_results(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('target')
            temp_dir.write('target/my-app-1.0-SNAPSHOT.jar', b'''sandbox''')
            jar_file_path = str(os.path.join(temp_dir.path, 'target/my-app-1.0-SNAPSHOT.jar'))
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
                package:
                    'artifacts': [{
                        'path':''' + jar_file_path + ''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    }]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'maven-servers': [
                            {'id': 'ID1', 'username': 'USER1', 'password': 'PW1'},
                            {'id': 'ID2'}
                        ],
                        'maven-repositories': [
                            {'id': 'ID1', 'url': 'URL1', 'snapshots': 'true', 'releases': 'false'},
                            {'id': 'ID2', 'url': 'URL2'}
                        ],
                        'maven-mirrors': [
                            {'id': 'ID1', 'url': 'URL1', 'mirror-of': '*'},
                            {'id': 'ID2', 'url': 'URL2', 'mirror-of': '*'}
                        ],
                    },
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                                    'maven-push-artifact-repo-id': 'repoid',
                                    'maven-push-artifact-repo-url': 'repourl',
                        }
                    }
                }
            }
            runtime_args = {}
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
                                    'path': jar_file_path,
                                    'pom-path': 'pom.xml'
                                }
                             ]
                        },
                        'push-artifacts':
                        {
                            'result': {
                                'success': True,
                                'message': 'push artifacts step completed - see report-artifacts',
                            },
                            'report-artifacts':
                            [
                                {
                                    'artifact-id': 'my-app',
                                    'group-id': 'com.mycompany.app',
                                    'path': jar_file_path,
                                    'version': '1.0-123abc'
                                }
                            ]
                        }
                    }
            }

            self.run_step_test_with_result_validation(temp_dir, 'push-artifacts',
                                                 config, expected_step_results, runtime_args)

    @patch('sh.mvn', create=True)
    def test_push_artifact_with_artifacts_results_bad(self, mock_mvn):

        with TempDirectory() as temp_dir:
            temp_dir.makedir('target')
            temp_dir.write('target/my-app-1.0-SNAPSHOT.jar', b'''sandbox''')
            jar_file_path = str(os.path.join(temp_dir.path, 'target/my-app-1.0-SNAPSHOT.jar'))
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
                package:
                    'artifacts': [{
                        'path':''' + jar_file_path + ''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    }]
            '''
            temp_dir.write('tssc-results/tssc-results.yml', tssc_results.encode())
            runtime_args = {}
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'maven-servers': [
                            {'id': 'ID1', 'username': 'USER1', 'password': 'PW1'},
                            {'id': 'ID2'}
                        ],
                        'maven-repositories': [
                            {'id': 'ID1', 'url': 'URL1', 'snapshots': 'true', 'releases': 'false'},
                            {'id': 'ID2', 'url': 'URL2'}
                        ],
                        'maven-mirrors': [
                            {'id': 'ID1', 'url': 'URL1', 'mirror-of': '*'},
                            {'id': 'ID2', 'url': 'URL2', 'mirror-of': '*'}
                        ],
                    },
                    'push-artifacts': {
                        'implementer': 'Maven',
                        'config': {
                            'maven-push-artifact-repo-id': 'repoid',
                            'maven-push-artifact-repo-url': 'repourl',
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
                                    'path': jar_file_path,
                                    'pom-path': 'pom.xml'
                                }
                            ]
                        },
                        'push-artifacts':
                        {
                            'result': {
                                'success': True,
                                'message': 'push artifacts step completed - see report-artifacts',
                            },
                            'report-artifacts':
                            [
                                {
                                    'artifact-id': 'my-app',
                                    'group-id': 'com.mycompany.app',
                                    'path': jar_file_path,
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
                self.run_step_test_with_result_validation(temp_dir, 'push-artifacts',
                                                     config, expected_step_results, runtime_args)

    @patch('sh.mvn', create=True)
    def test_push_artifact_with_artifacts_results_multi_no_maven_config(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('target')
            temp_dir.write('target/my-app-1.0-SNAPSHOT.jar', b'''sandbox''')
            jar_file_path = str(os.path.join(temp_dir.path, 'target/my-app-1.0-SNAPSHOT.jar'))
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
                package:
                    'artifacts': [{
                        'path':''' + jar_file_path + ''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    },
                    {
                        'path':''' + jar_file_path + ''',
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
                            'maven-push-artifact-repo-id': 'repoid',
                            'maven-push-artifact-repo-url': 'repourl',
                        }
                    }
                }
            }
            runtime_args = {}
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
                                            'path': jar_file_path,
                                            'pom-path': 'pom.xml'
                                        },
                                        {
                                            'artifact-id': 'my-app',
                                            'group-id': 'com.mycompany.app',
                                            'package-type': 'jar',
                                            'path': jar_file_path,
                                            'pom-path': 'pom.xml'
                                        }
                                    ]
                            },
                        'push-artifacts':
                            {
                                'result': {
                                    'success': True,
                                    'message': 'push artifacts step completed - see report-artifacts',
                                },
                                'report-artifacts':
                                    [
                                        {
                                            'artifact-id': 'my-app',
                                            'group-id': 'com.mycompany.app',
                                            'path': jar_file_path,
                                            'version': '1.0-123abc'
                                        },
                                        {
                                            'artifact-id': 'my-app',
                                            'group-id': 'com.mycompany.app',
                                            'path': jar_file_path,
                                            'version': '1.0-123abc'
                                        }
                                    ]
                            }
                    }
            }
            self.run_step_test_with_result_validation(temp_dir, 'push-artifacts',
                                                 config, expected_step_results, runtime_args)
    @patch('sh.mvn', create=True)
    def test_push_artifact_with_artifacts_results_multi(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('target')
            temp_dir.write('target/my-app-1.0-SNAPSHOT.jar', b'''sandbox''')
            jar_file_path = str(os.path.join(temp_dir.path, 'target/my-app-1.0-SNAPSHOT.jar'))
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
                package:
                    'artifacts': [{
                        'path':''' + jar_file_path + ''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    },
                    {
                        'path':''' + jar_file_path + ''',
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
                            'maven-push-artifact-repo-id': 'repoid',
                            'maven-push-artifact-repo-url': 'repourl',
                            'maven-servers': [
                                {'id': 'ID1', 'username': 'USER1', 'password': 'PW1'},
                            ],
                            'maven-repositories': [
                                {'id': 'ID1', 'url': 'URL1', 'snapshots': 'true', 'releases': 'false'},
                            ],
                            'maven-mirrors': [
                                {'id': 'ID1', 'url': 'URL1', 'mirror-of': '*'},
                            ]
                        }
                    }
                }
            }
            runtime_args = {}
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
                                            'path': jar_file_path,
                                            'pom-path': 'pom.xml'
                                        },
                                        {
                                            'artifact-id': 'my-app',
                                            'group-id': 'com.mycompany.app',
                                            'package-type': 'jar',
                                            'path': jar_file_path,
                                            'pom-path': 'pom.xml'
                                        }
                                    ]
                            },
                        'push-artifacts':
                            {
                                'result': {
                                    'success': True,
                                    'message': 'push artifacts step completed - see report-artifacts',
                                },
                                'report-artifacts':
                                    [
                                        {
                                            'artifact-id': 'my-app',
                                            'group-id': 'com.mycompany.app',
                                            'path': jar_file_path,
                                            'version': '1.0-123abc'
                                        },
                                        {
                                            'artifact-id': 'my-app',
                                            'group-id': 'com.mycompany.app',
                                            'path': jar_file_path,
                                            'version': '1.0-123abc'
                                        }
                                    ]
                            }
                    }
            }
            self.run_step_test_with_result_validation(temp_dir, 'push-artifacts',
                                                 config, expected_step_results, runtime_args)

    @patch('sh.mvn', create=True)
    def test_push_artifact_with_artifacts_results_multi_missing_id(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('target')
            temp_dir.write('target/my-app-1.0-SNAPSHOT.jar', b'''sandbox''')
            jar_file_path = str(os.path.join(temp_dir.path, 'target/my-app-1.0-SNAPSHOT.jar'))
            tssc_results = '''tssc-results:
                generate-metadata:
                    version: 1.0-123abc
                package:
                    'artifacts': [{
                        'path':''' + jar_file_path + ''',
                        'artifact-id': 'my-app',
                        'group-id': 'com.mycompany.app',
                        'package-type': 'jar',
                        'pom-path': 'pom.xml'
                    },
                    {
                        'path':''' + jar_file_path + ''',
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
                            'maven-push-artifact-repo-id': 'repoid',
                            'maven-push-artifact-repo-url': 'repourl',
                            'maven-servers': [
                                {'username': 'USER1', 'password': 'PW1'},
                            ],
                        }
                    }
                }
            }
            runtime_args = {}
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
                                            'path': jar_file_path,
                                            'pom-path': 'pom.xml'
                                        },
                                        {
                                            'artifact-id': 'my-app',
                                            'group-id': 'com.mycompany.app',
                                            'package-type': 'jar',
                                            'path': jar_file_path,
                                            'pom-path': 'pom.xml'
                                        }
                                    ]
                            },
                        'push-artifacts':
                            {
                                'result': {
                                    'success': True,
                                    'message': 'push artifacts step completed - see report-artifacts',
                                },
                                'report-artifacts':
                                    [
                                        {
                                            'artifact-id': 'my-app',
                                            'group-id': 'com.mycompany.app',
                                            'path': jar_file_path,
                                            'version': '1.0-123abc'
                                        },
                                        {
                                            'artifact-id': 'my-app',
                                            'group-id': 'com.mycompany.app',
                                            'path': jar_file_path,
                                            'version': '1.0-123abc'
                                        }
                                    ]
                            }
                    }
            }
            with self.assertRaisesRegex(
                AssertionError,
                r"Configuration for maven servers must specify a 'id':"
                r" {'username': 'USER1', 'password': 'PW1'}"
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'push-artifacts',
                    config,
                    expected_step_results, runtime_args
                )
