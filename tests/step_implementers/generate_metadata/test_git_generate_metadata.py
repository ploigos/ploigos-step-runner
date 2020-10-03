from testfixtures import TempDirectory

from git import Repo

from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from tests.helpers.test_utils import create_git_commit_with_sample_file


class TestStepImplementerGenerateMetadataGit(BaseStepImplementerTestCase):
    def test_root_dir_is_not_git_repo(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Git'
                    }
                }
            }
            expected_step_results = {
                'generate-metadata': {
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': False,
                        'message': 'InvalidGitRepositoryError',
                        'artifacts': {},
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path)}
            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_root_dir_is_bare_git_repo(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path), bare=True)

            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Git'
                    }
                }
            }
            expected_step_results = {
                'generate-metadata': {
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': False,
                        'message': f'Given directory ({temp_dir.path}) is a bare Git repository',
                        'artifacts': {},
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path)}
            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_no_commit_history(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Git'
                    }
                }
            }
            expected_step_results = {
                'generate-metadata': {
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': False,
                        'message': f'Given directory ({temp_dir.path}) is a Git branch (master) with no commit history',
                        'artifacts': {},
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path)}
            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_git_repo_with_single_commit_on_master_branch(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            create_git_commit_with_sample_file(temp_dir, repo)

            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Git'
                    }
                }
            }

            git_branch_last_commit_hash = str(repo.head.reference.commit)
            expected_step_results = {
                'generate-metadata': {
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'pre-release': {'value': 'master', 'type': 'str', 'description': ''},
                            'build': {'value': git_branch_last_commit_hash[:7], 'type': 'str', 'description': ''}
                        }
                    }
                }
            }
            runtime_args = {'repo-root': str(temp_dir.path)}
            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_git_repo_with_single_commit_on_feature_branch(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            # create commit
            create_git_commit_with_sample_file(temp_dir, repo)

            # checkout a feature branch
            git_new_branch = repo.create_head('feature/test0')
            git_new_branch.checkout()

            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Git'
                    }
                }
            }

            git_branch_last_commit_hash = str(repo.head.reference.commit)
            expected_step_results = {
                'generate-metadata': {
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'pre-release': {'value': 'feature_test0', 'type': 'str', 'description': ''},
                            'build': {'value': git_branch_last_commit_hash[:7], 'type': 'str', 'description': ''}
                        }
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path)}
            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_no_repo_root(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            # create commit
            create_git_commit_with_sample_file(temp_dir, repo)

            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Git',
                        'config': {
                            'repo-root': None
                        }
                    }
                }
            }

            git_branch_last_commit_hash = str(repo.head.reference.commit)
            expected_step_results = {}
            runtime_args = {}

            # todo: should the assert be refactored
            with self.assertRaisesRegex(
                    AssertionError,
                    r"The runtime step configuration \(\{'repo-root': None, 'build-string-length': 7\}\) is missing the required configuration keys \(\['repo-root'\]\)"):
                self.run_step_test_with_result_validation(
                    temp_dir=temp_dir,
                    step_name='generate-metadata',
                    config=config,
                    expected_step_results=expected_step_results,
                    runtime_args=runtime_args
                )

    def test_directory_is_detached_head(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            # create commits
            create_git_commit_with_sample_file(temp_dir, repo, 'test0')
            create_git_commit_with_sample_file(temp_dir, repo, 'test1')

            # detach head
            repo.git.checkout('master^')

            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Git'
                    }
                }
            }
            expected_step_results = {
                'generate-metadata': {
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': False,
                        'message': f'Expected a Git branch in given directory ({temp_dir.path}) but has a detached head.',
                        'artifacts': {}
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path)}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )
