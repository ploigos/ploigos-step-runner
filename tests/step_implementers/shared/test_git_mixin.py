import os
import unittest
from unittest.mock import MagicMock, patch, PropertyMock, call

from git import InvalidGitRepositoryError, GitCommandError
from ploigos_step_runner import StepImplementer, StepRunnerException
from ploigos_step_runner.step_implementers.shared import GitMixin
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class GitMixinStepImplementerMock(StepImplementer, GitMixin):
    def __init__(
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None
    ):
        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment
        )

    def _run_step(self):
        pass

class TestGitMixinBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            parent_work_dir_path='',
            environment=None
    ):
        return self.create_given_step_implementer(
            step_implementer=GitMixinStepImplementerMock,
            step_config=step_config,
            step_name='mock',
            implementer='GitMixinStepImplementerMock',
            parent_work_dir_path=parent_work_dir_path,
            environment=environment
        )

class TestGitMixin_step_implementer_config_defaults(unittest.TestCase):
    def test_results(self):
        defaults = GitMixin.step_implementer_config_defaults()
        expected_defaults = {
            'git-repo-root': './',
            'git-commit-message': 'Automated commit of changes during release engineering' \
                ' generate-metadata step',
            'git-user-name': 'Ploigos Robot',
            'git-user-email': 'ploigos-robot'
        }
        self.assertEqual(defaults, expected_defaults)

class TestGitMixin__required_config_or_result_keys(unittest.TestCase):
    def test_results(self):
        required_keys = GitMixin._required_config_or_result_keys()
        expected_required_keys = [
            ['git-repo-root', 'repo-root']
        ]
        self.assertEqual(required_keys, expected_required_keys)

@patch('ploigos_step_runner.step_implementers.shared.git_mixin.Repo')
class TestGitMixin_git_repo(unittest.TestCase):
    def test_given_git_repo_root(self, mock_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'git-repo-root' in key:
                return 'mock/repo/path'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_repo = step_implementer.git_repo

        # validate
        self.assertIsNotNone(actual_git_repo)
        mock_repo.assert_called_once_with('mock/repo/path')

    def test_given_repo_root(self, mock_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'repo-root' in key:
                return 'mock/repo/path'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_repo = step_implementer.git_repo

        # validate
        self.assertIsNotNone(actual_git_repo)
        mock_repo.assert_called_once_with('mock/repo/path')

    def test_multiple_calls(self, mock_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'git-repo-root' in key:
                return 'mock/repo/path'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_repo1 = step_implementer.git_repo
        actual_git_repo2 = step_implementer.git_repo

        # validate
        self.assertEqual(actual_git_repo1, actual_git_repo2)
        mock_repo.assert_called_once_with('mock/repo/path')

    def test_repo_error(self, mock_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'git-repo-root' in key:
                return 'mock/bad/repo/path'
        mock_get_value.side_effect = mock_get_value_side_effect
        mock_repo.side_effect = InvalidGitRepositoryError('mock error')

        # run test
        with self.assertRaisesRegex(
            StepRunnerException,
            "Given git-repo-root \(mock/bad/repo/path\) is not a Git repository: mock error"
        ):
            step_implementer.git_repo

        # validate
        mock_repo.assert_called_once_with('mock/bad/repo/path')

@patch.object(GitMixin, 'git_repo')
class TestGitMixin_git_url(unittest.TestCase):
    def test_given_git_url_ssh(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'git-url' in key:
                return 'ssh://git@mock.xyz/mock.git'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'ssh://git@mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_url_ssh(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'ssh://git@mock.xyz/mock.git'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'ssh://git@mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_git_url_https_no_username_no_password(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'https://mock.xyz/mock.git'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'https://mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_git_url_http_no_username_no_password(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'http://mock.xyz/mock.git'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'http://mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_git_url_https_given_config_username(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'https://mock.xyz/mock.git'
            if 'username' in key:
                return 'mock-user'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'https://mock-user@mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_git_url_https_given_config_username_and_given_config_password(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'https://mock.xyz/mock.git'
            if 'username' in key:
                return 'mock-user'
            if 'password' in key:
                return 'mock-pass'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'https://mock-user:mock-pass@mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_git_url_https_with_port_given_config_username_and_given_config_password(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'https://mock.xyz:42/mock.git'
            if 'username' in key:
                return 'mock-user'
            if 'password' in key:
                return 'mock-pass'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'https://mock-user:mock-pass@mock.xyz:42/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_git_url_https_given_config_username_and_given_config_password_and_given_username_in_url(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'https://mock-url-user@mock.xyz/mock.git'
            if 'username' in key:
                return 'mock-config-user'
            if 'password' in key:
                return 'mock-pass'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'https://mock-config-user:mock-pass@mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_git_url_https_given_config_password_and_givin_username_in_url(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'https://mock-url-user@mock.xyz/mock.git'
            if 'password' in key:
                return 'mock-pass'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'https://mock-url-user:mock-pass@mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_git_url_https_given_config_username_and_given_config_password_and_given_password_in_url(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'https://mock-url-user:mock-url-pass@mock.xyz/mock.git'
            if 'username' in key:
                return 'mock-config-user'
            if 'password' in key:
                return 'mock-config-pass'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'https://mock-config-user:mock-config-pass@mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_given_git_url_https_given_config_username_and_given_password_in_url(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'url' in key:
                return 'https://mock-url-user:mock-url-pass@mock.xyz/mock.git'
            if 'username' in key:
                return 'mock-config-user'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'https://mock-config-user:mock-url-pass@mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

    def test_url_from_git_repo_ssh(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            return None
        mock_get_value.side_effect = mock_get_value_side_effect
        type(mock_git_repo.remote()).url = PropertyMock(return_value='ssh://git@mock.xyz/mock.git')

        # run test
        actual_git_url1 = step_implementer.git_url
        actual_git_url2 = step_implementer.git_url

        # validate
        self.assertEqual(actual_git_url1, 'ssh://git@mock.xyz/mock.git')
        self.assertEqual(actual_git_url1, actual_git_url2)
        mock_git_repo.assert_not_called()

@patch.object(GitMixin, 'git_repo')
class TestGitMixin_configure_git_user(unittest.TestCase):
    def test_given_git_user_name_and_given_git_user_email(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'git-user-name' in key:
                return 'mock-git-user'
            if 'git-user-email' in key:
                return 'mock-git-email@mock.xyz'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        step_implementer.configure_git_user()

        # validate
        mock_git_repo.config_writer().set_value.assert_has_calls([
            call('user', 'name', 'mock-git-user'),
            call().release(),
            call('user', 'email', 'mock-git-email@mock.xyz'),
            call().release()
        ])

@patch.object(GitMixin, 'git_repo')
class TestGitMixin_git_commit_changes(unittest.TestCase):
    def test_success(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'git-commit-message' in key:
                return 'mock commit message'
        mock_get_value.side_effect = mock_get_value_side_effect

        # run test
        step_implementer.git_commit_changes()

        # validate
        mock_git_repo.git.commit.assert_called_with('-am', 'mock commit message')

    def test_fail(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_get_value = MagicMock()
        step_implementer.get_value = mock_get_value
        def mock_get_value_side_effect(key):
            if 'git-commit-message' in key:
                return 'mock commit message'
        mock_get_value.side_effect = mock_get_value_side_effect
        mock_git_repo.git.commit.side_effect = GitCommandError('mock error')
        type(mock_git_repo.active_branch).name = PropertyMock(return_value='mock-branch')

        # run test
        with self.assertRaisesRegex(
            StepRunnerException,
            r"Error committing changes to current branch \(mock-branch\): Cmd\('mock'\)"
            r" failed!\s*cmdline: mock error"
        ):
            step_implementer.git_commit_changes()

        # validate
        mock_git_repo.git.commit.assert_called_with('-am', 'mock commit message')

@patch.object(GitMixin, 'git_repo')
@patch.object(GitMixin, 'git_url', new_callable=PropertyMock)
class TestGitMixin_git_push(unittest.TestCase):
    def test_success(self, mock_git_url, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_git_url.return_value = 'mock-url'

        # run test
        step_implementer.git_push()

        # validate
        mock_git_repo.git.push.assert_called_with('mock-url')

    def test_fail(self, mock_git_url, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_git_url.return_value = 'mock-url'
        type(mock_git_repo.active_branch).name = PropertyMock(return_value='mock-branch')
        mock_git_repo.git.push.side_effect = GitCommandError('mock error')

        # run test
        with self.assertRaisesRegex(
            StepRunnerException,
            r"Error pushing changes to remote \(mock-url\) on current branch \(mock-branch\):"
            r" Cmd\('mock'\) failed!\s*cmdline: mock error"
        ):
            step_implementer.git_push()

        # validate
        mock_git_repo.git.push.assert_called_with('mock-url')

@patch.object(GitMixin, 'git_repo')
@patch.object(GitMixin, 'git_url', new_callable=PropertyMock)
class TestGitMixin_git_push_tags(unittest.TestCase):
    def test_success(self, mock_git_url, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_git_url.return_value = 'mock-url'

        # run test
        step_implementer.git_push_tags()

        # validate
        mock_git_repo.git.push.assert_called_with('mock-url', '--tag')

    def test_fail(self, mock_git_url, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_git_url.return_value = 'mock-url'
        type(mock_git_repo.active_branch).name = PropertyMock(return_value='mock-branch')
        mock_git_repo.git.push.side_effect = GitCommandError('mock error')

        # run test
        with self.assertRaisesRegex(
            StepRunnerException,
            r"Error pushing tags to remote \(mock-url\) on current branch \(mock-branch\):"
            r" Cmd\('mock'\) failed!\s*cmdline: mock error"
        ):
            step_implementer.git_push_tags()

        # validate
        mock_git_repo.git.push.assert_called_with('mock-url', '--tag')

@patch.object(GitMixin, 'git_repo')
@patch.object(GitMixin, 'configure_git_user')
@patch.object(GitMixin, 'git_commit_changes')
@patch.object(GitMixin, 'git_push')
class TestGitMixin_commit_changes_and_push(unittest.TestCase):
    def test_is_dirty(self, mock_git_push, mock_git_commit_changes, mock_configure_git_user, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_git_repo.is_dirty.return_value = True

        # run test
        step_implementer.commit_changes_and_push()

        # validate
        mock_configure_git_user.assert_called_once_with()
        mock_git_commit_changes.assert_called_once_with()
        mock_git_push.assert_called_once_with()

    def test_not_dirty(self, mock_git_push, mock_git_commit_changes, mock_configure_git_user, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # set up mocks
        mock_git_repo.is_dirty.return_value = False

        # run test
        step_implementer.commit_changes_and_push()

        # validate
        mock_configure_git_user.assert_not_called()
        mock_git_commit_changes.assert_not_called()
        mock_git_push.assert_not_called()

@patch.object(GitMixin, 'git_repo')
class TestGitMixin_git_tag(unittest.TestCase):
    def test_success(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # run test
        step_implementer.git_tag(
            git_tag_value='v0.42.0-mock'
        )

        # validate
        mock_git_repo.create_tag.assert_called_once_with('v0.42.0-mock', force=True)

    def test_fail(self, mock_git_repo):
        # setup
        step_implementer = GitMixin()

        # setup mock
        mock_git_repo.create_tag.side_effect = GitCommandError('mock error')

        # run test
        with self.assertRaisesRegex(
            StepRunnerException,
            r"Error creating git tag \(v0.42.0-mock\): Cmd\('mock'\) failed!\s*cmdline: mock error"
        ):
            step_implementer.git_tag(
                git_tag_value='v0.42.0-mock'
            )

        # validate
        mock_git_repo.create_tag.assert_called_once_with('v0.42.0-mock', force=True)
