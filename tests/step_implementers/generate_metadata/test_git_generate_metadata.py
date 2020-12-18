# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os

from git import Repo
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import create_git_commit_with_sample_file
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.generate_metadata import Git


class TestStepImplementerGitGenerateMetadata(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Git,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = Git.step_implementer_config_defaults()
        expected_defaults = {
            'repo-root': './',
            'build-string-length': 7
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Git._required_config_or_result_keys()
        expected_required_keys = ['repo-root', 'build-string-length']
        self.assertEqual(required_keys, expected_required_keys)

    def test_run_step_pass(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            repo = Repo.init(str(temp_dir.path))

            create_git_commit_with_sample_file(temp_dir, repo)

            step_config = {
                'repo-root': str(temp_dir.path)
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            # cheating because we don't want to fully mock this yet
            self.assertTrue(result.success, True)

    def test_root_dir_is_not_git_repo(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'repo-root': '/'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Given directory (repo_root) is not a Git repository'

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    def test_root_dir_is_bare_git_repo(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            Repo.init(str(temp_dir.path), bare=True)

            step_config = {
                'repo-root': str(temp_dir.path)
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Given directory (repo_root) is a bare Git repository'

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    def test_no_commit_history(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            Repo.init(str(temp_dir.path))

            step_config = {
                'repo-root': str(temp_dir.path)
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(
                name='pre-release',
                value='master'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Given directory (repo_root) is a ' \
                                           'git branch (git_branch) with no commit history'

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    def test_git_repo_with_single_commit_on_master(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            repo = Repo.init(str(temp_dir.path))

            create_git_commit_with_sample_file(temp_dir, repo)

            step_config = {
                'repo-root': str(temp_dir.path)
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            # cheating because we don't want to fully mock this yet
            self.assertTrue(result.success, True)

    def test_git_repo_with_single_commit_on_feature(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            repo = Repo.init(str(temp_dir.path))

            create_git_commit_with_sample_file(temp_dir, repo)

            # checkout a feature branch
            git_new_branch = repo.create_head('feature/test0')
            git_new_branch.checkout()

            step_config = {
                'repo-root': str(temp_dir.path)
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            # cheating because we don't want to fully mock this yet
            self.assertEqual(result.get_artifact_value('pre-release'), 'feature_test0')
            self.assertTrue(result.success, True)

    def test_directory_is_detached(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            repo = Repo.init(str(temp_dir.path))

            # create commits
            create_git_commit_with_sample_file(temp_dir, repo, 'test0')
            create_git_commit_with_sample_file(temp_dir, repo, 'test1')

            # detach head
            repo.git.checkout('master^')

            step_config = {
                'repo-root': str(temp_dir.path)
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='Git',
                                              sub_step_implementer_name='Git')
            expected_step_result.success = False
            expected_step_result.message = 'Expected a Git branch in given directory (repo_root) ' \
                                           'but has a detached head'

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())
