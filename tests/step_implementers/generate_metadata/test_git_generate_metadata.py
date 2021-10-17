
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
    def test_step_implementer_config_defaults(self):
        defaults = Git.step_implementer_config_defaults()
        expected_defaults = {
            'repo-root': './',
            'release-branch-regexes': ['^main$', '^master$']
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Git._required_config_or_result_keys()
        expected_required_keys = [
            'repo-root'
        ]
        self.assertEqual(required_keys, expected_required_keys)

@patch('ploigos_step_runner.step_implementers.generate_metadata.git.Repo')
class TestStepImplementerGitGenerateMetadata_run_step(TestStepImplementerGitGenerateMetadataBase):
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
            mock_repo().bare = False
            mock_repo().head.is_detached = False
            mock_repo().head.reference.name = 'main'
            mock_repo().head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

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
            mock_repo().bare = False
            mock_repo().head.is_detached = False
            mock_repo().head.reference.name = 'release/mock1'
            mock_repo().head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

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
            mock_repo().bare = False
            mock_repo().head.is_detached = False
            mock_repo().head.reference.name = 'release/mock1'
            mock_repo().head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

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
            mock_repo().bare = False
            mock_repo().head.is_detached = False
            mock_repo().head.reference.name = 'feature/mock1'
            mock_repo().head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

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
            mock_repo().bare = False
            mock_repo().head.is_detached = False
            mock_repo().head.reference.name = 'feature/mock1'
            mock_repo().head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

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

    def test_success_pre_release_branch_custom_release_branch_regexes_string(self, mock_repo):
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
            mock_repo().bare = False
            mock_repo().head.is_detached = False
            mock_repo().head.reference.name = 'feature/mock1'
            mock_repo().head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

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
            mock_repo().bare = False
            mock_repo().head.is_detached = False
            mock_repo().head.reference.name = 'feature/mock1'
            mock_repo().head.reference.commit = 'a1b2c3d4e5f6g7h8i9'

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
            expected_step_result.message = f'Given repo-root ({temp_dir.path})' \
                ' is not a Git repository'

            self.assertEqual(actual_step_result, expected_step_result)


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
            mock_repo().bare = True

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.success = False
            expected_step_result.message = f'Given repo-root ({temp_dir.path})' \
                ' is not a Git repository'

            self.assertEqual(actual_step_result, expected_step_result)

    def test_fail_is_detached(self, mock_repo):
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
            mock_repo().bare = False
            mock_repo().head.is_detached = True

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.success = False
            expected_step_result.message = f'Expected a Git branch in given repo_root' \
                f' ({temp_dir.path}) but has a detached head'

            self.assertEqual(actual_step_result, expected_step_result)

    def test_fail_no_commit_history(self, mock_repo):
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
            mock_repo().bare = False
            mock_repo().head.is_detached = False
            mock_repo().head.reference.name = 'main'
            type(mock_repo().head.reference).commit = PropertyMock(side_effect=ValueError)

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
            expected_step_result.success = False
            expected_step_result.message =  f'Given repo-root ({temp_dir.path}) is a' \
                f' git branch (main) with no commit history'

            self.assertEqual(actual_step_result, expected_step_result)
