"""`StepImplementer` for the `generate-metadata` step using Git.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key     | Required? | Default | Description
----------------------|-----------|---------|-----------
`repo-root`           | Yes       | `./`    | Directory path to the Git repo to generate \
                                            metadata from.
`build-string-length` | Yes       | `7`     | Length of the Git hash to use for the \
                                              `build` portion of the semantic version.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`pre-release` | Value to use for `pre-release` portion of semantic version \
                (https://semver.org/). Uses the Git branch name.
`build`       | Value to use for `build` portion of semantic version (https://semver.org/). \
                Uses a portion of the latest Git commit hash.
"""

import re

from git import InvalidGitRepositoryError, Repo

from ploigos_step_runner import StepImplementer, StepResult

DEFAULT_CONFIG = {
    'repo-root': './',
    'build-string-length': 7
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'repo-root',
    'build-string-length'
]

class Git(StepImplementer):  # pylint: disable=too-few-public-methods
    """
    StepImplementer for the generate-metadata step for Git.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

        Returns
        -------
        dict
            Default values to use for step configuration values.

        Notes
        -----
        These are the lowest precedence configuration values.

        """
        return DEFAULT_CONFIG

    @staticmethod
    def _required_config_or_result_keys():
        """Getter for step configuration or previous step result artifacts that are required before
        running this step.

        See Also
        --------
        _validate_required_config_or_previous_step_result_artifact_keys

        Returns
        -------
        array_list
            Array of configuration keys or previous step result artifacts
            that are required before running the step.
        """
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        repo_root = self.get_value('repo-root')
        build_string_length = self.get_value('build-string-length')

        try:
            repo = Repo(repo_root)
        except InvalidGitRepositoryError:
            step_result.success = False
            step_result.message = 'Given directory (repo_root) is not a Git repository'
            return step_result

        if repo.bare:
            step_result.success = False
            step_result.message = 'Given directory (repo_root) is a bare Git repository'
            return step_result

        if repo.head.is_detached:
            step_result.success = False
            step_result.message = 'Expected a Git branch in given directory (repo_root) but has' \
                                  ' a detached head'
            return step_result

        git_branch = str(repo.head.reference)
        pre_release_regex = re.compile(r"/", re.IGNORECASE)
        pre_release = re.sub(pre_release_regex, '_', git_branch)
        step_result.add_artifact(
            name='pre-release',
            value=pre_release
        )

        try:
            git_branch_last_commit_hash = str(repo.head.reference.commit)[:build_string_length]

            step_result.add_artifact(
                name='build',
                value=git_branch_last_commit_hash
            )
        except ValueError:
            step_result.success = False
            step_result.message = 'Given directory (repo_root) is a git branch (git_branch) with' \
                                  ' no commit history'
            return step_result

        return step_result
