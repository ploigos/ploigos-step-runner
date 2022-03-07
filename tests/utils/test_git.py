"""Test for git.py

Test for the utility for git operations.
"""

from unittest.mock import ANY, call, patch

from ploigos_step_runner.utils.git import *
from tests.helpers.base_test_case import BaseTestCase
from tests.helpers.test_utils import create_sh_side_effect


class TestGitUtils_get_git_repo_regex(BaseTestCase):
    def test_get_git_repo_regex(self):
        self.assertEqual(
            re.compile(r'(?P<protocol>^https:\/\/|^http:\/\/)?(?P<address>.*$)'),
            get_git_repo_regex()
        )


class TestGitUtils_clone_repo(BaseTestCase):
    @patch('sh.git', create=True)
    def test_clone_repo_success(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_url = 'git@git.ploigos.xyz:/foo/test.git'
        username = 'Test'
        password = 'Password'

        clone_repo(
            repo_dir=repo_dir,
            repo_url=repo_url,
            username=username,
            password=password
        )

        git_mock.clone.assert_called_once_with(
            repo_url,
            repo_dir,
            _out=ANY,
            _err=ANY
        )

    @patch('sh.git', create=True)
    def test_clone_repo_success_https(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_url = 'https://Test:Password@git.ploigos.xyz'
        username = 'Test'
        password = 'Password'
        repo_url_with_auth = 'https://git.ploigos.xyz'

        clone_repo(
            repo_dir=repo_dir,
            repo_url=repo_url_with_auth,
            username=username,
            password=password
        )

        git_mock.clone.assert_called_once_with(
            repo_url,
            repo_dir,
            _out=ANY,
            _err=ANY
        )

    @patch('sh.git', create=True)
    def test_clone_repo_fail_clone(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_url = 'git@git.ploigos.xyz:/foo/test.git'
        username = 'Test'
        password = 'password'

        git_mock.clone.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('git', b'mock out', b'mock git clone error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error cloning repository \({repo_url}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git clone error",
                re.DOTALL
            )
        ):
            clone_repo(
                repo_dir=repo_dir,
                repo_url=repo_url,
                username=username,
                password=password
            )

            git_mock.clone.assert_called_once_with(
                repo_url,
                repo_dir,
                _out=ANY,
                _err=ANY
            )


class TestGitUtils_git_config(BaseTestCase):
    @patch('sh.git', create=True)
    def test_git_config_success_new_branch(self, git_mock):
        repo_dir = '/does/not/matter'
        git_email = 'test@ploigos.xyz'
        git_name = 'Test Robot'

        git_config(
            repo_dir=repo_dir,
            git_email=git_email,
            git_name=git_name
        )

        git_mock.config.assert_has_calls([
            call(
                'user.email',
                git_email,
                _cwd=repo_dir,
                _out=ANY,
                _err=ANY
            ),
            call(
                'user.name',
                git_name,
                _cwd=repo_dir,
                _out=ANY,
                _err=ANY
            )
        ])

    @patch('sh.git', create=True)
    def test_git_config_fail_config_email(self, git_mock):
        repo_dir = '/does/not/matter'
        git_email = 'test@ploigos.xyz'
        git_name = 'Test Robot'

        git_mock.config.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock git config email error')

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Unexpected error configuring git user.email \({git_email}\)"
                rf" and user.name \({git_name}\) for repository"
                rf" under directory \({repo_dir}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git config email error",
                re.DOTALL
            )
        ):
            git_config(
                repo_dir=repo_dir,
                git_email=git_email,
                git_name=git_name
            )

            git_mock.config.assert_called_once_with(
                'user.email',
                git_email,
                _cwd=repo_dir,
                _out=ANY,
                _err=ANY
            )

    @patch('sh.git', create=True)
    def test_git_config_fail_config_name(self, git_mock):
        repo_dir = '/does/not/matter'
        git_email = 'test@ploigos.xyz'
        git_name = 'Test Robot'

        git_mock.config.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock git config name error')

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Unexpected error configuring git user.email \({git_email}\)"
                rf" and user.name \({git_name}\) for repository"
                rf" under directory \({repo_dir}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git config name error",
                re.DOTALL
            )
        ):
            git_config(
                repo_dir=repo_dir,
                git_email=git_email,
                git_name=git_name
            )

            git_mock.config.assert_has_calls([
                call(
                    'user.email',
                    git_email,
                    _cwd=repo_dir,
                    _out=ANY,
                    _err=ANY
                ),
                call(
                    'user.name',
                    git_name,
                    _cwd=repo_dir,
                    _out=ANY,
                    _err=ANY
                )
            ])


class TestGitUtils_git_checkout(BaseTestCase):
    @patch('sh.git', create=True)
    def test_git_checkout_success_new_branch(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_branch = 'feature/test'

        git_checkout(
            repo_dir=repo_dir,
            repo_branch=repo_branch
        )

        git_mock.checkout.assert_called_once_with(
            repo_branch,
            _cwd=repo_dir,
            _out=ANY,
            _err=ANY
        )

    @patch('sh.git', create=True)
    def test_git_checkout_success_existing_branch(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_branch = 'feature/test'

        git_mock.checkout.side_effect = [
            sh.ErrorReturnCode('git', b'mock out', b'mock git checkout branch does not exist'),
            None
        ]

        git_checkout(
            repo_dir=repo_dir,
            repo_branch=repo_branch
        )

        git_mock.checkout.assert_has_calls([
            call(
                repo_branch,
                _cwd=repo_dir,
                _out=ANY,
                _err=ANY
            ),
            call(
                '-b',
                repo_branch,
                _cwd=repo_dir,
                _out=ANY,
                _err=ANY
            )
        ])

    @patch('sh.git', create=True)
    def test_git_checkout_fail_existing_branch(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_branch = 'feature/test'

        git_mock.checkout.side_effect = [
            sh.ErrorReturnCode('git', b'mock out', b'mock git checkout branch does not exist'),
            sh.ErrorReturnCode('git', b'mock out', b'mock git checkout new branch error'),
        ]

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Unexpected error checking out new or existing branch \({repo_branch}\)"
                rf" from repository under directory \({repo_dir}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git checkout new branch error",
                re.DOTALL
            )
        ):
            git_checkout(
                repo_dir=repo_dir,
                repo_branch=repo_branch
            )

            git_mock.checkout.assert_has_calls([
                call(
                    repo_branch,
                    _cwd=repo_dir,
                    _out=ANY,
                    _err=ANY
                ),
                call(
                    '-b',
                    repo_branch,
                    _cwd=repo_dir,
                    _out=ANY,
                    _err=ANY
                )
            ])


class TestGitUtils_git_commit_file(BaseTestCase):
    @patch('sh.git', create=True)
    def test_git_commit_file_success(self, git_mock):
        git_commit_file(
            git_commit_message='hello world',
            file_path='charts/foo/values-DEV.yaml',
            repo_dir='/does/not/matter'
        )

        git_mock.add.assert_called_once_with(
            'charts/foo/values-DEV.yaml',
            _cwd='/does/not/matter',
            _out=ANY,
            _err=ANY
        )

        git_mock.commit.assert_called_once_with(
            '--allow-empty',
            '--all',
            '--message', 'hello world',
            _cwd='/does/not/matter',
            _out=ANY,
            _err=ANY
        )

    @patch('sh.git', create=True)
    def test_git_commit_file_fail_add(self, git_mock):
        git_mock.add.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('git', b'mock out', b'mock git add error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Unexpected error adding file \(charts/foo/values-DEV.yaml\) to commit"
                r" in git repository \(/does/not/matter\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git add error",
                re.DOTALL
            )
        ):
            git_commit_file(
                git_commit_message='hello world',
                file_path='charts/foo/values-DEV.yaml',
                repo_dir='/does/not/matter'
            )

            git_mock.add.assert_called_once_with(
                'charts/foo/values-DEV.yaml',
                _cwd='/does/not/matter',
                _out=ANY,
                _err=ANY
            )

            git_mock.commit.assert_not_called()

    @patch('sh.git', create=True)
    def test_git_commit_file_fail_commit(self, git_mock):
        git_mock.commit.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('git', b'mock out', b'mock git commit error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Unexpected error commiting file \(charts/foo/values-DEV.yaml\)"
                r" in git repository \(/does/not/matter\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git commit error",
                re.DOTALL
            )
        ):
            git_commit_file(
                git_commit_message='hello world',
                file_path='charts/foo/values-DEV.yaml',
                repo_dir='/does/not/matter'
            )

            git_mock.add.assert_called_once_with(
                'charts/foo/values-DEV.yaml',
                _cwd='/does/not/matter',
                _out=ANY,
                _err=ANY
            )

            git_mock.commit.assert_called_once_with(
                '--allow-empty',
                '--all',
                '--message', 'hello world',
                _cwd='/does/not/matter',
                _out=ANY,
                _err=ANY
            )


class TestGitUtils_git_tag_and_push(BaseTestCase):
    @patch('sh.git', create=True)
    def test_git_tag_and_push_success_ssh(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None
        git_tag_and_push(
            repo_dir=repo_dir,
            tag=tag,
            url=url
        )

        git_mock.push.assert_has_calls([
            call(
                _cwd=repo_dir,
                _out=ANY
            ),
            call(
                '--tag',
                _cwd=repo_dir,
                _out=ANY
            )
        ])
        git_mock.tag.assert_called_once_with(
            tag,
            '-f',
            _cwd=repo_dir,
            _out=ANY,
            _err=ANY
        )

    @patch('sh.git', create=True)
    def test_git_tag_and_push_success_https_url(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = 'https://user:pass@git.ploigos.xyz'
        git_tag_and_push(
            repo_dir=repo_dir,
            tag=tag,
            url=url
        )

        git_mock.push.bake().assert_has_calls([
            call(
                _cwd=repo_dir,
                _out=ANY
            ),
            call(
                '--tag',
                _cwd=repo_dir,
                _out=ANY
            )
        ])
        git_mock.tag.assert_called_once_with(
            tag,
            '-f',
            _cwd=repo_dir,
            _out=ANY,
            _err=ANY
        )

    @patch('sh.git', create=True)
    def test_git_tag_and_push_fail_commit(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None

        git_mock.push.side_effect = [
            sh.ErrorReturnCode('git', b'mock out', b'mock git push error'),
            create_sh_side_effect()
        ]

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error pushing commits from repository directory \({repo_dir}\) to"
                rf" repository \({url}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git push error",
                re.DOTALL
            )
        ):
            git_tag_and_push(
                repo_dir=repo_dir,
                tag=tag,
                url=url
            )

            git_mock.push.assert_has_calls([
                call(
                    _cwd=repo_dir,
                    _out=ANY
                )
            ])

            git_mock.tag.assert_not_called()

    @patch('sh.git', create=True)
    def test_git_tag_and_push_fail_tag(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None

        git_mock.tag.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock git tag error')

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error tagging repository \({repo_dir}\) with tag \({tag}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git tag error",
                re.DOTALL
            )
        ):
            git_tag_and_push(
                repo_dir=repo_dir,
                tag=tag,
                url=url
            )

            git_mock.push.assert_called_once_with(
                _cwd=repo_dir,
                _out=ANY
            )

            git_mock.tag.assert_called_once_with(
                tag,
                '-f',
                _cwd=repo_dir,
                _out=ANY,
                _err=ANY
            )

    @patch('sh.git', create=True)
    def test_git_tag_and_push_fail_push_tag(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None

        git_mock.push.side_effect = [
            create_sh_side_effect(),
            sh.ErrorReturnCode('git', b'mock out', b'mock git push tag error')
        ]

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error pushing tags from repository directory \({repo_dir}\) to"
                rf" repository \({url}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git push tag error",
                re.DOTALL
            )
        ):
            git_tag_and_push(
                repo_dir=repo_dir,
                tag=tag,
                url=url
            )

            git_mock.push.bake().assert_has_calls([
                call(
                    _cwd=repo_dir,
                    _out=ANY
                ),
                call(
                    '--tag',
                    _cwd=repo_dir,
                    _out=ANY
                )
            ])

            git_mock.tag.assert_called_once_with(
                tag,
                '-f',
                _cwd=repo_dir,
                _out=ANY,
                _err=ANY
            )

    @patch('sh.git', create=True)
    def test_git_tag_and_push_override_tls(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None
        git_tag_and_push(
            repo_dir=repo_dir,
            tag=tag,
            url=url,
            force_push_tags=True
        )

        git_mock.push.assert_has_calls([
            call(
                _cwd=repo_dir,
                _out=ANY
            ),
            call(
                '--tag',
                '--force',
                _cwd=repo_dir,
                _out=ANY
            )
        ])
        git_mock.tag.assert_called_once_with(
            tag,
            '-f',
            _cwd=repo_dir,
            _out=ANY,
            _err=ANY
        )
