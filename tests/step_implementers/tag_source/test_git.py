from testfixtures import TempDirectory
import unittest
from unittest.mock import patch

from test_utils import *
from tssc.step_implementers.tag_source import Git

class TestStepImplementerTagSourceGit(unittest.TestCase):
    @patch('sh.git', create=True)
    def test_tag_ssh_latest_version(self, git_mock):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {}
                    }
                }
            }
    
            expected_step_results = {
                'tssc-results': {
                    'tag-source': {
                        'tag': 'latest'
                    }
                }
            }
            runtime_args = {
                'username': 'unit_test_username',
                'password': 'unit_test_password'
            }

            run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)
            git_mock.tag.assert_called_once_with('latest','-f')
            git_mock.push.assert_called_once()
    
    @patch('sh.git', create=True)
    def test_tag_ssh_latest_version_url(self, git_mock):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {
                            'url': 'git@github.com:rhtconsulting/tssc-python-package.git'
                        }
                    }
                }
            }
            expected_step_results = {
                'tssc-results': {
                    'tag-source': {
                        'tag': 'latest'
                    }
                }
            }
            run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results)
            git_mock.tag.assert_called_once_with('latest','-f')
            git_mock.push.assert_called_once()
    
    @patch('sh.git', create=True)
    def test_tag_http_latest_version(self, git_mock):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {}
                    }
                }
            }
            expected_step_results = {
                'tssc-results': {
                    'tag-source': {
                        'tag': 'latest'
                    }
                }
            }
            runtime_args = {
                'username': 'unit_test_username',
                'password': 'unit_test_password'
            }
            run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)
            git_mock.tag.assert_called_once_with('latest','-f')
            git_mock.push.assert_called_once()
    
    @patch('sh.git', create=True)
    def test_tag_http_latest_version_url(self, git_mock):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {
                            'url': 'http://gitea.apps.tssc.rht-set.com/tssc-references/tssc-reference-app-quarkus-rest-json.git'
                        }
                    }
                }
            }
            expected_step_results = {
                'tssc-results': {
                    'tag-source': {
                        'tag': 'latest'
                    }
                }
            }
            runtime_args = {
                'username': 'unit_test_username',
                'password': 'unit_test_password'
            }
            run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)
            git_mock.tag.assert_called_once_with('latest','-f')
            git_mock.push.assert_called_once()
    
    @patch('sh.git', create=True)
    def test_tag_ssh_metadata_version(self, git_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                version: 1.0+69442c8
                image-tag: 1.0-69442c8
                ''')
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {}
                    }
                }
            }
    
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata': {
                        'image-tag': '1.0-69442c8',
                        'version': '1.0+69442c8'
                    },
                    'tag-source': {
                        'tag': '1.0+69442c8'
                    }
                }
            }
            runtime_args = {
                'username': 'unit_test_username',
                'password': 'unit_test_password'
            }
            run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)
            git_mock.tag.assert_called_once_with('1.0+69442c8','-f')
            git_mock.push.assert_called_once()
    
    @patch('sh.git', create=True)
    def test_tag_http_metadata_version(self, git_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                version: 1.0+69442c8
                image-tag: 1.0-69442c8
                ''')
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {
                            'url': 'https://github.com/rhtconsulting/tssc-python-package.git'
                        }
                    }
                }
            }
    
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata': {
                        'image-tag': '1.0-69442c8',
                        'version': '1.0+69442c8'
                    },
                    'tag-source': {
                        'tag': '1.0+69442c8'
                    }
                }
            }
            runtime_args = {
                'username': 'unit_test_username',
                'password': 'unit_test_password'
            }
            run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)
            git_mock.tag.assert_called_once_with('1.0+69442c8','-f')
            git_mock.push.assert_called_once()
    
    @patch('sh.git', create=True)
    def test_tag_http_metadata_version_missing_username(self, git_mock):
        passed = False
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                image-tag: 1.0-69442c8
                ''')
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {
                            'username_env_var': 'GIT_USERNAME'
                        }
                    }
                }
            }
    
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata': {
                        'image-tag': '1.0-69442c8',
                        'version': '1.0+69442c8'
                    },
                    'tag-source': {
                        'tag': '1.0+69442c8'
                    }
                }
            }
            runtime_args = {
                'username': 'unit_test_username',
            }

            with self.assertRaisesRegex(
                    ValueError, 
                    'Either username or password is not set. Neither or both must be set.'):
                run_step_test_with_result_validation(
                    temp_dir,
                    'tag-source',
                    config, 
                    expected_step_results,
                    runtime_args)

    @patch('sh.git', create=True)
    def test_tag_http_metadata_version_blank_password(self, git_mock):
        passed = False
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                image-tag: 1.0-69442c8
                ''')
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {}
                    }
                }
            }
    
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata': {
                        'image-tag': '1.0-69442c8'
                    },
                    'tag-source': {
                        'tag': '1.0-69442c8'
                    }
                }
            }
            runtime_args = {
                'username': 'unit_test_username',
                'password': ''
            }

            with self.assertRaisesRegex(
                    ValueError, 
                    'Both username and password must have non-empty value in the runtime step configuration'):
                run_step_test_with_result_validation(temp_dir, 'tag-source', config, \
                  expected_step_results, runtime_args)
    
    @patch('sh.git', create=True)
    def test_tag_https_no_username_or_password(self, git_mock):
        passed = False
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                image-tag: 1.0-69442c8
                ''')
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {
                            'url': 'https://github.com/rhtconsulting/tssc-python-package.git'
                        }
                    }
                }
            }
    
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata': {
                        'image-tag': '1.0-69442c8'
                    },
                    'tag-source': {
                        'tag': '1.0-69442c8'
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError, 
                    'For a https:// git url, you need to also provide username/password pair'):
                run_step_test_with_result_validation(temp_dir, 'tag-source', config, \
                  expected_step_results)
     
    @patch('sh.git', create=True)
    def test_tag_http_no_username_or_password(self, git_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                image-tag: 1.0-69442c8
                ''')
            config = {
                'tssc-config': {
                    'tag-source': {
                        'implementer': 'Git',
                        'config': {
                            'url': 'http://github.com/rhtconsulting/tssc-python-package.git'
                        }
                    }
                }
            }
    
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata': {
                        'image-tag': '1.0-69442c8'
                    },
                    'tag-source': {
                        'tag': '1.0-69442c8'
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError, 
                    'For a http:// git url, you need to also provide username/password pair'):
                run_step_test_with_result_validation(temp_dir, 'tag-source', config, \
                  expected_step_results)

