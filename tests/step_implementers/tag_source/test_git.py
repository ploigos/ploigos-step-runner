import unittest
from io import IOBase
from unittest.mock import patch

import sh
from test_utils import *
from testfixtures import TempDirectory
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tssc.config.config import Config
from tssc.step_implementers.tag_source import Git


class TestStepImplementerTagSourceGit(BaseTSSCTestCase):
    @staticmethod
    def __create_git_config_side_effect(remote_origin_url):
        def git_config_side_effect(*args, **kwargs):
            if (args[0] == '--get') and (args[1] == 'remote.origin.url'):
                kwargs['_out'].write(remote_origin_url)

        return git_config_side_effect

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
            git_mock.tag.assert_called_once_with(
                'latest',
                '-f',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
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
            git_mock.tag.assert_called_once_with(
                'latest',
                '-f',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
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
            git_mock.tag.assert_called_once_with(
                'latest',
                '-f',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
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
            git_mock.tag.assert_called_once_with(
                'latest',
                '-f',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
            git_mock.push.assert_called_once()

    @patch('sh.git', create=True)
    def test_tag_ssh_metadata_version(self, git_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                version: 1.0+69442c8
                container-image-version: 1.0-69442c8
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
                        'container-image-version': '1.0-69442c8',
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
            git_mock.tag.assert_called_once_with(
                '1.0+69442c8',
                '-f',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
            git_mock.push.assert_called_once()

    @patch('sh.git', create=True)
    def test_tag_http_metadata_version(self, git_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                version: 1.0+69442c8
                container-image-version: 1.0-69442c8
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
                        'container-image-version': '1.0-69442c8',
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
            git_mock.tag.assert_called_once_with(
                '1.0+69442c8',
                '-f',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
            git_mock.push.assert_called_once()

    @patch('sh.git', create=True)
    def test_tag_http_metadata_version_missing_username(self, git_mock):
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write('tssc-results/tssc-results.yml', b'''tssc-results:
              generate-metadata:
                container-image-version: 1.0-69442c8
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
                        'container-image-version': '1.0-69442c8',
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
                    AssertionError,
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
                container-image-version: 1.0-69442c8
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
                        'container-image-version': '1.0-69442c8'
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
                container-image-version: 1.0-69442c8
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
                        'container-image-version': '1.0-69442c8'
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
                container-image-version: 1.0-69442c8
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
                        'container-image-version': '1.0-69442c8'
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

    def __create_git_step_implementer(self, git_mock, step_config={}):
        config = Config({
            Config.TSSC_CONFIG_KEY: {
                'tag-source': [
                    {
                        'implementer': 'Git',
                        'config': step_config
                    }
                ]

            }
        })

        step_config = config.get_step_config('tag-source')
        sub_step_config = step_config.get_sub_step('Git')

        git_step = Git(
            results_dir_path="",
            results_file_name="",
            work_dir_path="",
            config=sub_step_config
        )

        return git_step

    def __run__git_url_test(self, git_mock, remote_origin_url, expected_result, step_config={}):
        git_mock.config.side_effect = \
            TestStepImplementerTagSourceGit.__create_git_config_side_effect(
                remote_origin_url=remote_origin_url
            )

        git_step = self.__create_git_step_implementer(
            git_mock=git_mock,
            step_config=step_config
        )

        self.assertEqual(
            expected_result,
            git_step._git_url()
        )

    @patch('sh.git', create=True)
    def test__git_url_no_config_http_with_username(self, git_mock):
        self.__run__git_url_test(
            git_mock=git_mock,
            remote_origin_url="http://test-user@gitea.example.xyz",
            expected_result='http://gitea.example.xyz'
        )

    @patch('sh.git', create=True)
    def test__git_url_no_config_https_with_username(self, git_mock):
        self.__run__git_url_test(
            git_mock=git_mock,
            remote_origin_url="https://test-user@gitea.example.xyz",
            expected_result='https://gitea.example.xyz'
        )

    @patch('sh.git', create=True)
    def test__git_url_no_config_http_with_username_and_password(self, git_mock):
        self.__run__git_url_test(
            git_mock=git_mock,
            remote_origin_url="http://test-user:test-pass@gitea.example.xyz",
            expected_result='http://gitea.example.xyz'
        )

    @patch('sh.git', create=True)
    def test__git_url_no_config_https_with_username_and_password(self, git_mock):
        self.__run__git_url_test(
            git_mock=git_mock,
            remote_origin_url="https://test-user:test-pass@gitea.example.xyz",
            expected_result='https://gitea.example.xyz'
        )

    @patch('sh.git', create=True)
    def test__git_url_no_config_http_with_no_username(self, git_mock):
        self.__run__git_url_test(
            git_mock=git_mock,
            remote_origin_url="http://gitea.example.xyz",
            expected_result='http://gitea.example.xyz'
        )

    @patch('sh.git', create=True)
    def test__git_url_no_config_https_with_no_username(self, git_mock):
        self.__run__git_url_test(
            git_mock=git_mock,
            remote_origin_url="https://gitea.example.xyz",
            expected_result='https://gitea.example.xyz'
        )

    @patch('sh.git', create=True)
    def test__git_url_config_http(self, git_mock):
        self.__run__git_url_test(
            git_mock=git_mock,
            remote_origin_url="http://test-user@gitea.example.xyz",
            expected_result='http://use-me-gitea.example.xyz',
            step_config={
                'url': 'http://use-me-gitea.example.xyz'
            }
        )

    @patch('sh.git', create=True)
    def test__git_url_config_https(self, git_mock):
        self.__run__git_url_test(
            git_mock=git_mock,
            remote_origin_url="http://test-user@gitea.example.xyz",
            expected_result='https://use-me-gitea.example.xyz',
            step_config={
                'url': 'https://use-me-gitea.example.xyz'
            }
        )

    @patch('sh.git', create=True)
    def test__git_url_config_ssh(self, git_mock):
        self.__run__git_url_test(
            git_mock=git_mock,
            remote_origin_url="http://test-user@gitea.example.xyz",
            expected_result='git@use-me-gitea.example.xyz',
            step_config={
                'url': 'git@use-me-gitea.example.xyz'
            }
        )

    @patch('sh.git', create=True)
    def test__git_tag_invalid_git_credentials(self, git_mock):
        step_config = {
            'url': 'https://gitea.example.xyz',
            'username': 'bad-user',
            'password': 'bad-password'
        }

        git_step = self.__create_git_step_implementer(
            git_mock=git_mock,
            step_config=step_config
        )

        git_mock.tag.side_effect = sh.ErrorReturnCode('git tag', b'mock out', b'mock authentication error')

        with self.assertRaisesRegex(
            RuntimeError,
            re.compile(
                r"Error pushing git tag \(v1.42.0\):"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock authentication error",
                re.DOTALL
            )
        ):
            git_step._git_tag('v1.42.0')

