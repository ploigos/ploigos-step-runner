"""
Step Implementer for the generate-metadata step for git.
"""

import re
from git import Repo
from git import InvalidGitRepositoryError

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {
    'repo-root': './',
    'build-string-length': 7
}

class Git(StepImplementer): # pylint: disable=too-few-public-methods 
    """
    StepImplementer for the generate-metadata step for Git.

    Raises
    ------
    ValueError
        If given pom file does not exist
        If given pom file does not contain required elements
    """

    def __init__(self, config, results_file):
        super().__init__(config, results_file, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.GENERATE_METADATA

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """
        if 'repo-root' not in step_config or not step_config['repo-root']:
            raise ValueError('Key (repo-root) must have non-empty value in the step configuration')

    def _run_step(self, runtime_step_config):
        repo_root = runtime_step_config['repo-root']
        build_string_length = runtime_step_config['build-string-length']

        try:
            repo = Repo(repo_root)
        except InvalidGitRepositoryError as err:
            raise err

        if repo.bare:
            raise ValueError("Given directory ({0}) is a bare Git repository".format(repo_root))

        if repo.head.is_detached:
            raise ValueError(
                "Expected a Git branch in given directory ({0}) but has a detached head."
                .format(repo_root)
            )

        git_branch = str(repo.head.reference)

        try:
            git_branch_last_commit_hash = str(repo.head.reference.commit)[:build_string_length]
        except ValueError as err:
            raise ValueError(
                "Given directory ({0}) is a Git branch ({1}) with no commit history".format(
                    repo_root, git_branch
                )
            )

        # make the git branch safe
        pre_release_regex = re.compile(r"/", re.IGNORECASE)
        pre_release = re.sub(pre_release_regex, '_', git_branch)

        results = {
            'pre-release': pre_release,
            'build': git_branch_last_commit_hash
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(Git)
