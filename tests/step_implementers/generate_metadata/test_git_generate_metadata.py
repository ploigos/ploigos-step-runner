
from unittest.mock import PropertyMock, patch

from git import InvalidGitRepositoryError
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.generate_metadata import Git
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestStepImplementerGitGenerateMetadataBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Git,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )


class TestStepImplementerGitGenerateMetadata_misc(TestStepImplementerGitGenerateMetadataBase):
    def test__validate_required_config_or_previous_step_result_artifact_keys(self):
        step_config = {
        }

        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_step_implementer_config_defaults(self):
        defaults = Git.step_implementer_config_defaults()
        expected_defaults = {
            'git-repo-root': './',
            'release-branch-regexes': ['^main$', '^master$'],
            'git-commit-and-push-changes': False,
            'git-commit-message': 'Automated commit of changes during release engineering'
                                  ' generate-metadata step',
            'git-user-name': 'Ploigos Robot',
            'git-user-email': 'ploigos-robot'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Git._required_config_or_result_keys()
        expected_required_keys = [
            ['git-repo-root', 'repo-root']
        ]
        self.assertEqual(required_keys, expected_required_keys)


class TestStepImplementerGitGenerateMetadata_run_step(TestStepImplementerGitGenerateMetadataBase):
    @patch.object(Git, 'git_repo')
    def test_success_release_branch_default_release_branch_regexes(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = 'main'
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value='main'
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=False
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_success_release_branch_default_prerelease_branch_regexes_commit_and_push_always(
            self,
            mock_repo,
            git_url_mock
    ):
        # Test data setup
        branch_name = "not-main"

        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path,
                'git-commit-and-push-changes': 'always'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = branch_name
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'
            git_url_mock.return_value = "value doesn't matter"

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value=branch_name
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=True
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_success_release_branch_default_prerelease_branch_regexes_commit_and_push_always_not_dirty(
            self,
            mock_repo,
            git_url_mock
    ):
        # Test data setup
        branch_name = "not-main"

        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path,
                'git-commit-and-push-changes': 'always'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.is_dirty.return_value = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = branch_name
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'
            git_url_mock.return_value = "value doesn't matter"

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value=branch_name
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=True
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_success_release_branch_default_release_branch_regexes_commit_and_push_always(
            self,
            mock_repo,
            git_url_mock
    ):
        # Test data setup
        branch_name = "main"

        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path,
                'git-commit-and-push-changes': 'always'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = branch_name
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'
            git_url_mock.return_value = "value doesn't matter"

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value=branch_name
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=False
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_success_release_branch_custom_release_branch_regexes_list(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path,
                'release-branch-regexes': [
                    '^release/.*$'
                ]
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = 'release/mock1'
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value='release/mock1'
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=False
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_success_release_branch_custom_release_branch_regexes_string(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path,
                'release-branch-regexes': '^release/.*$'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = 'release/mock1'
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value='release/mock1'
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=False
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_success_pre_release_branch_default_release_branch_regexes(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = 'feature/mock1'
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value='feature/mock1'
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=True
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_success_pre_release_branch_custom_release_branch_regexes_list(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path,
                'release-branch-regexes': [
                    '^release/.*$'
                ]
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = 'feature/mock1'
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value='feature/mock1'
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=True
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_success_pre_release_branch_custom_release_branch_regexes_string(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path,
                'release-branch-regexes': '^release/.*$',
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = 'feature/mock1'
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value='feature/mock1'
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=True
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_success_pre_release_branch_custom_release_branch_regexes_empty(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path,
                'release-branch-regexes': None
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = 'feature/mock1'
            mock_repo.head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value='feature/mock1'
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=True
            )
            expected_step_result.add_artifact(
                name='sha',
                value='a1b2c3d4e5f6g7h8i9'
            )

            self.assertEqual(actual_step_result, expected_step_result)

    @patch('git.Repo')
    def test_fail_not_a_git_repo(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.side_effect = InvalidGitRepositoryError()

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.success = False
            expected_step_result.message = f'Given git-repo-root ({temp_dir.path})' \
                ' is not a Git repository'

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_fail_git_repo_bare(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = True

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.success = False
            expected_step_result.message = f'Given git-repo-root is not a Git repository'

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_fail_is_detached(self, mock_repo):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'git-repo-root': temp_dir.path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = True

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.success = False
            expected_step_result.message = f'Expected a Git branch in given git repo root' \
                f' but has a detached head'

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_fail_no_commit_history(self, mock_repo):
        # Data setup
        git_branch = 'main'

        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = git_branch
            type(mock_repo.head.reference).commit = PropertyMock(side_effect=ValueError)

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value=git_branch
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=False
            )
            expected_step_result.success = False
            expected_step_result.message = f'Given Git repository root is a' \
                f' git branch ({git_branch}) with no commit history.'

            self.assertEqual(actual_step_result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test_run_step_fail_commit_changes_and_push(self, mock_repo):
        # Data setup
        git_branch = 'main'
        error = 'Holy guacamole..!'

        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path,
                'git-commit-and-push-changes': True
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git'
            )

            # setup mocks
            mock_repo.bare = False
            mock_repo.head.is_detached = False
            mock_repo.active_branch.name = git_branch
            mock_repo.git.commit.side_effect = Exception(error)

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='branch',
                value=git_branch
            )
            expected_step_result.add_artifact(
                name='is-pre-release',
                value=False
            )
            expected_step_result.success = False
            expected_step_result.message = f'Error committing and pushing changes: Error committing changes ' \
                                           f'to current branch ({git_branch}): {error}'

            self.assertEqual(actual_step_result, expected_step_result)
