"""`StepImplementer` for the `generate-metadata` step using Git.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key        | Required? | Default                  | Description
-------------------------|-----------|--------------------------|-----------
`repo-root`              | Yes       | `./`                     | Directory path to the Git repo to generate \
                                                                  metadata from. Must not be in a detached head state \
                                                                  so that `pre-release` value can be determined.
`release-branch-regexes` | No        | `['^main$', '^master$']` | If current git branch matches any of the given regex patterns, \
                                                                  then this will be considered a release else \
                                                                  will be considered a pre-release. \
                                                                  If no patterns given then will be considered a pre-release.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`branch`            | Current branch name.
`is-pre-release`    | `True` if this build should be considered a pre-release, \
                      `False` if should be considered a release.
`sha`               | Current commit sha.

"""# pylint: disable=line-too-long

import re

from git import InvalidGitRepositoryError, Repo

from ploigos_step_runner import StepImplementer, StepResult

DEFAULT_CONFIG = {
    'repo-root': './',
    'release-branch-regexes': ['^main$', '^master$']
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'repo-root'
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
        try:
            repo = Repo(repo_root)
        except InvalidGitRepositoryError:
            step_result.success = False
            step_result.message = f'Given repo-root ({repo_root}) is not a Git repository'
            return step_result

        if repo.bare:
            step_result.success = False
            step_result.message = f'Given repo-root ({repo_root}) is not a Git repository'
            return step_result

        # Need to be able to determine the branch name to determine if is a pre-release build or not
        if repo.head.is_detached:
            step_result.success = False
            step_result.message = f'Expected a Git branch in given repo_root ({repo_root})' \
                ' but has a detached head'
            return step_result

        # add branch artifact
        git_branch = repo.head.reference.name
        step_result.add_artifact(
            name='branch',
            value=git_branch
        )

        # determine if pre-release
        release_branch_regexes = self.get_value('release-branch-regexes')
        if release_branch_regexes:
            is_pre_release = True
            if not isinstance(release_branch_regexes, list):
                release_branch_regexes = [release_branch_regexes]
            for release_branch_regex in release_branch_regexes:
                if re.match(release_branch_regex, git_branch):
                    is_pre_release = False
                    break
        else:
            is_pre_release = True

        # add pre-release artifact
        step_result.add_artifact(
            name='is-pre-release',
            value=is_pre_release
        )

        # add commit sha artifact
        try:
            git_branch_last_commit_sha = str(repo.head.reference.commit)
            step_result.add_artifact(
                name='sha',
                value=git_branch_last_commit_sha
            )
        except ValueError:
            step_result.success = False
            step_result.message = f'Given repo-root ({repo_root}) is a' \
                f' git branch ({git_branch}) with no commit history'
            return step_result

        return step_result
