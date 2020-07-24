"""Step Implementer for the generate-metadata step for git.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key     | Required? | Default | Description
|-----------------------|-----------|---------|-----------
| `repo-root`           | True      | `./`    | Directory path to the Git repo to generate \
                                                metadata from.
| `build-string-length` | True      | `7`     | Length of the Git hash to use for the \
                                                `build` portion of the semantic version.

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

.. Note:: This step implementer does not expect results from any previous steps.

Results
-------

Results output by this step.

| Result Key    | Description
|---------------|------------
| `pre-release` | Value to use for `pre-release` portion of semantic version \
                    (https://semver.org/). \
                    Uses the Git branch name.
| `build`       | Value to use for `build` portion of semantic version (https://semver.org/). \
                    Uses a portion of the latest Git commit hash.
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

    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, DEFAULT_ARGS)

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
