import pytest
from testfixtures import TempDirectory

from git import Repo
from git import InvalidGitRepositoryError

from tssc.step_implementers.generate_metadata import Git

from test_utils import *


def test_root_dir_is_not_git_repo():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {
                'generate-metadata': {
                    'implementer': 'Git'
                }
            }
        }
        expected_step_results = {}

        with pytest.raises(InvalidGitRepositoryError):
            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})

def test_root_dir_is_bare_git_repo():
    with TempDirectory() as temp_dir:
        repo = Repo.init(str(temp_dir.path), bare=True)

        config = {
            'tssc-config': {
                'generate-metadata': {
                    'implementer': 'Git'
                }
            }
        }
        expected_step_results = {}

        with pytest.raises(ValueError):
            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})

def test_no_commit_history():
    with TempDirectory() as temp_dir:
        repo = Repo.init(str(temp_dir.path))

        config = {
            'tssc-config': {
                'generate-metadata': {
                    'implementer': 'Git'
                }
            }
        }
        expected_step_results = {}

        with pytest.raises(ValueError):
            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})

def test_git_repo_with_single_commit_on_master_branch():
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
        expected_step_results = {'tssc-results': {'generate-metadata': {'pre-release': 'master', 'build': git_branch_last_commit_hash[:7]}}}
        
        run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})

def test_git_repo_with_single_commit_on_feature_branch():
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
        expected_step_results = {'tssc-results': {'generate-metadata': {'pre-release': 'feature_test0', 'build': git_branch_last_commit_hash[:7]}}}

        run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})

def test_no_repo_root():
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

        with pytest.raises(ValueError):
            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results)

def test_directory_is_detached_head():
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
        expected_step_results = {}
        
        with pytest.raises(ValueError):
            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})