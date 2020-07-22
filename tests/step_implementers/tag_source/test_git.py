import os

import pytest
from testfixtures import TempDirectory
import yaml
import mock

from tssc import TSSCFactory
from tssc.step_implementers.tag_source import Git

from test_utils import *

def mock_git_tag(self, tag):
    return True

def mock_git_push(self, url):
    return True

def test_tag_ssh_latest_version():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {
                'tag-source': {
                    'implementer': 'Git',
                    'config': {}
                }
            }
        }
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push

        expected_step_results = {
            'tssc-results': {
                'tag-source': {
                    'git_tag': 'latest'
                }
            }
        }
        runtime_args = {
            'username': 'unit_test_username',
            'password': 'unit_test_password'
        }
        run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)

def test_tag_ssh_latest_version_git_url():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {
                'tag-source': {
                    'implementer': 'Git',
                    'config': {
                        'git_url': 'git@github.com:rhtconsulting/tssc-python-package.git'
                    }
                }
            }
        }
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push
        expected_step_results = {
            'tssc-results': {
                'tag-source': {
                    'git_tag': 'latest'
                }
            }
        }
        run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results)

def test_tag_http_latest_version():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {
                'tag-source': {
                    'implementer': 'Git',
                    'config': {}
                }
            }
        }
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push
        expected_step_results = {
            'tssc-results': {
                'tag-source': {
                    'git_tag': 'latest'
                }
            }
        }
        runtime_args = {
            'username': 'unit_test_username',
            'password': 'unit_test_password'
        }
        run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)

def test_tag_http_latest_version_git_url():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {
                'tag-source': {
                    'implementer': 'Git',
                    'config': {
                        'git_url': 'http://gitea.apps.tssc.rht-set.com/tssc-references/tssc-reference-app-quarkus-rest-json.git'
                    }
                }
            }
        }
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push
        expected_step_results = {
            'tssc-results': {
                'tag-source': {
                    'git_tag': 'latest'
                }
            }
        }
        runtime_args = {
            'username': 'unit_test_username',
            'password': 'unit_test_password'
        }
        run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)

def test_tag_ssh_metadata_version():
    with TempDirectory() as temp_dir:
        temp_dir.makedir('tssc-results')
        temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
          generate-metadata:
            image-tag: 1.0-SNAPSHOT-69442c8
            ''')
        config = {
            'tssc-config': {
                'tag-source': {
                    'implementer': 'Git',
                    'config': {}
                }
            }
        }
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push

        expected_step_results = {
            'tssc-results': {
                'generate-metadata': {
                    'image-tag': '1.0-SNAPSHOT-69442c8'
                },
                'tag-source': {
                    'git_tag': '1.0-SNAPSHOT-69442c8'
                }
            }
        }
        runtime_args = {
            'username': 'unit_test_username',
            'password': 'unit_test_password'
        }
        run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)

def test_tag_http_metadata_version():
    with TempDirectory() as temp_dir:
        temp_dir.makedir('tssc-results')
        temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
          generate-metadata:
            image-tag: 1.0-SNAPSHOT-69442c8
            ''')
        config = {
            'tssc-config': {
                'tag-source': {
                    'implementer': 'Git',
                    'config': {
                        'git_url': 'https://github.com/rhtconsulting/tssc-python-package.git'
                    }
                }
            }
        }
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push

        expected_step_results = {
            'tssc-results': {
                'generate-metadata': {
                    'image-tag': '1.0-SNAPSHOT-69442c8'
                },
                'tag-source': {
                    'git_tag': '1.0-SNAPSHOT-69442c8'
                }
            }
        }
        runtime_args = {
            'username': 'unit_test_username',
            'password': 'unit_test_password'
        }
        run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results, runtime_args)
        _environ = dict(os.environ)  # or os.environ.copy()


def test_tag_http_metadata_version_missing_username():
    passed = False
    with TempDirectory() as temp_dir:
        temp_dir.makedir('tssc-results')
        temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
          generate-metadata:
            image-tag: 1.0-SNAPSHOT-69442c8
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
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push

        expected_step_results = {
            'tssc-results': {
                'generate-metadata': {
                    'image-tag': '1.0-SNAPSHOT-69442c8'
                },
                'tag-source': {
                    'git_tag': '1.0-SNAPSHOT-69442c8'
                }
            }
        }
        runtime_args = {
            'username': 'unit_test_username',
        }
        try:
            run_step_test_with_result_validation(temp_dir, 'tag-source', config, \
              expected_step_results, runtime_args)
        except ValueError as err:
            if err.__str__() == 'Either username or password is not set. Neither ' \
              'or both must be set.':
                passed = True
    assert passed

def test_tag_http_metadata_version_blank_password():
    passed = False
    with TempDirectory() as temp_dir:
        temp_dir.makedir('tssc-results')
        temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
          generate-metadata:
            image-tag: 1.0-SNAPSHOT-69442c8
            ''')
        config = {
            'tssc-config': {
                'tag-source': {
                    'implementer': 'Git',
                    'config': {}
                }
            }
        }
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push

        expected_step_results = {
            'tssc-results': {
                'generate-metadata': {
                    'image-tag': '1.0-SNAPSHOT-69442c8'
                },
                'tag-source': {
                    'git_tag': '1.0-SNAPSHOT-69442c8'
                }
            }
        }
        runtime_args = {
            'username': 'unit_test_username',
            'password': ''
        }
        try:
            run_step_test_with_result_validation(temp_dir, 'tag-source', config, \
              expected_step_results, runtime_args)
        except ValueError as err:
            print(err.__str__())
            if err.__str__() == 'Both username and password must have ' \
              'non-empty value in the runtime step configuration':
                passed = True
    assert passed

def test_tag_https_no_username_or_password():
    passed = False
    with TempDirectory() as temp_dir:
        temp_dir.makedir('tssc-results')
        temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
          generate-metadata:
            image-tag: 1.0-SNAPSHOT-69442c8
            ''')
        config = {
            'tssc-config': {
                'tag-source': {
                    'implementer': 'Git',
                    'config': {
                        'git_url': 'https://github.com/rhtconsulting/tssc-python-package.git'
                    }
                }
            }
        }
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push

        expected_step_results = {
            'tssc-results': {
                'generate-metadata': {
                    'image-tag': '1.0-SNAPSHOT-69442c8'
                },
                'tag-source': {
                    'git_tag': '1.0-SNAPSHOT-69442c8'
                }
            }
        }
        try:
            run_step_test_with_result_validation(temp_dir, 'tag-source', config, \
              expected_step_results)
        except ValueError as err:
            print(err.__str__())
            if err.__str__() == 'For a https:// git url, you need to also provide ' \
              'username/password pair':
                passed = True
    assert passed

def test_tag_http_no_username_or_password():
    passed = False
    with TempDirectory() as temp_dir:
        temp_dir.makedir('tssc-results')
        temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
          generate-metadata:
            image-tag: 1.0-SNAPSHOT-69442c8
            ''')
        config = {
            'tssc-config': {
                'tag-source': {
                    'implementer': 'Git',
                    'config': {
                        'git_url': 'http://github.com/rhtconsulting/tssc-python-package.git'
                    }
                }
            }
        }
        Git._git_tag = mock_git_tag
        Git._git_push = mock_git_push

        expected_step_results = {
            'tssc-results': {
                'generate-metadata': {
                    'image-tag': '1.0-SNAPSHOT-69442c8'
                },
                'tag-source': {
                    'git_tag': '1.0-SNAPSHOT-69442c8'
                }
            }
        }
        try:
            run_step_test_with_result_validation(temp_dir, 'tag-source', config, \
              expected_step_results)
        except ValueError as err:
            print(err.__str__())
            if err.__str__() == 'For a http:// git url, you need to also provide ' \
              'username/password pair':
                passed = True
    assert passed
