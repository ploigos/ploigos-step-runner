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

from tssc import StepImplementer

DEFAULT_CONFIG = {
    'repo-root': './',
    'build-string-length': 7
}

REQUIRED_CONFIG_KEYS = [
    'repo-root'
]

class Git(StepImplementer): # pylint: disable=too-few-public-methods
    """
    StepImplementer for the generate-metadata step for Git.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

        Notes
        -----
        These are the lowest precedence configuration values.

        Returns
        -------
        dict
            Default values to use for step configuration values.
        """
        return DEFAULT_CONFIG

    @staticmethod
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.

        See Also
        --------
        _validate_runtime_step_config

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.
        """
        return REQUIRED_CONFIG_KEYS

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        dict
            Results of running this step.
        """
        repo_root = self.get_config_value('repo-root')
        build_string_length = self.get_config_value('build-string-length')

        try:
            repo = Repo(repo_root)
        except InvalidGitRepositoryError as err:
            self.step_result.success = False
            self.step_result.message = 'InvalidGitRepositoryError'
            return

        if repo.bare:
            self.step_result.success = False
            self.step_result.message = f"Given directory ({repo_root}) is a bare Git repository"
            return

        if repo.head.is_detached:
            self.step_result.success = False
            self.step_result.message = f'Expected a Git branch in given directory ({repo_root}) but has a detached head.'
            return

        git_branch = str(repo.head.reference)

        try:
            git_branch_last_commit_hash = str(repo.head.reference.commit)[:build_string_length]
        except ValueError as err:
            self.step_result.success = False
            self.step_result.message = f'Given directory ({repo_root}) is a Git branch ({git_branch}) with no commit history'
            return

        # make the git branch safe
        pre_release_regex = re.compile(r"/", re.IGNORECASE)
        pre_release = re.sub(pre_release_regex, '_', git_branch)

        # step_result
        self.step_result.success = True
        self.step_result.add_artifact('pre-release', pre_release)
        self.step_result.add_artifact('build', git_branch_last_commit_hash)

