"""`StepImplementer` for the `generate-metadata` step using Git.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key             | Required? | Default                  | Description
------------------------------|-----------|--------------------------|-----------
`release-branch-regexes`      | No        | `['^main$', '^master$']` | If current git branch matches any of the given regex patterns, \
                                                                       then this will be considered a release else \
                                                                       will be considered a pre-release. \
                                                                       If no patterns given then will be considered a pre-release.
`git-commit-and-push-changes` | No        | `False`                  | When, if ever, to commit and push any changes detected in the repository. \
                                                                       One of [True, False, 'always', 'release', 'pre-release']. \
                                                                       If True or 'always' then will always commit and push any changes. \
                                                                       If False, will never commit and push any changes. \
                                                                       If 'release' will only commit and push changes when on a release branch. \
                                                                       If 'pre-release' will only commit and push changes on a pre-release branch.
`git-repo-root`               | Yes       | `./`                     | Directory path to the Git repository to perform git operations on.
`repo-root`                   | No        |                          | Alias for `git-repo-root`.
`git-url`                     | No        | Git repo root configured origin url \
                                                                     | URL to Git repository to perform Git operations on. \
                                                                       If not given will use Git remote url set in given Git repository root.
`url`                         | No        |                          | Alias for `git-url`.
`git-username`                | No        |                          | Git username to use when connecting with Git remote. \
                                                                       Will override username in given git url. \
                                                                       Will override username in Git url in Git repository root remote url. \
                                                                       Will be ignored if Git repository url is using SSH.
`git-password`                | No        |                          | Git password to use when connecting with Git remote. \
                                                                       Will override password in given git url. \
                                                                       Will override password in Git url in Git repository root remote url. \
                                                                       Will be ignored if Git repository url is using SSH.
`git-user-name`               | Maybe     | `Ploigos Robot`          | User name to use when creating Git commits.
`git-user-email`              | Maybe     | `ploigos-robot`          | User email to use when creating Git commits.
`git-commit-message`          | Maybe     | `Automated commit of changes during release engineering generate-metadata step` \
                                                                     | Git commit message to use when/if creating an automated git commit.

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

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.step_implementers.shared import GitMixin

DEFAULT_CONFIG = {
    'git-repo-root': './',
    'release-branch-regexes': ['^main$', '^master$'],
    'git-commit-and-push-changes': False
}

"""
Note
---
Some required fields inherited from GitMixin (see `_required_config_or_result_keys`)
"""
REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = []

class Git(StepImplementer, GitMixin):  # pylint: disable=too-few-public-methods
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
        return {**GitMixin.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS + \
            GitMixin._required_config_or_result_keys()

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * given 'pom-file' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # validate git-commit-and-push-changes is boolean or valid string option
        git_commit_and_push_changes = self.get_value('git-commit-and-push-changes')
        assert isinstance(git_commit_and_push_changes, bool) or \
            (git_commit_and_push_changes in ['always', 'release', 'pre-release', 'prerelease']), \
            "Given configuration option (git-commit-and-push-changes)" \
            " must either be a boolean or one of [always, release, pre-release]."

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # get the git repo
        repo = None
        try:
            repo = self.git_repo
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = str(error)
            return step_result

        if repo.bare:
            step_result.success = False
            step_result.message = 'Given git-repo-root is not a Git repository'
            return step_result

        # Need to be able to determine the branch name to determine if is a pre-release build or not
        if repo.head.is_detached:
            step_result.success = False
            step_result.message = 'Expected a Git branch in given git repo root' \
                ' but has a detached head'
            return step_result

        # add branch artifact
        git_branch = repo.active_branch.name
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

        # commit and push changes
        if self.__should_commit_changes_and_push(is_pre_release):
            try:
                self.commit_changes_and_push()
            except StepRunnerException as error:
                step_result.success = False
                step_result.message = f"Error committing and pushing changes: {error}"
                return step_result

        # add commit sha artifact
        try:
            git_branch_last_commit_sha = str(repo.head.reference.commit)
            step_result.add_artifact(
                name='sha',
                value=git_branch_last_commit_sha
            )
        except ValueError:
            step_result.success = False
            step_result.message = f'Given Git repository root is a' \
                f' git branch ({git_branch}) with no commit history.'
            return step_result

        return step_result

    def __should_commit_changes_and_push(self, is_pre_release):
        """Determine if should commit changes and push.

        Parameters
        ----------
        is_pre_release : bool
            True if is a pre-release, False if Release.

        Returns
        -------
        bool
            True if should commit changes and push, False if not.
        """
        should_commit_changes_and_push = False
        git_commit_and_push_changes = self.get_value('git-commit-and-push-changes')
        if git_commit_and_push_changes:
            if isinstance(git_commit_and_push_changes, bool) and git_commit_and_push_changes:
                should_commit_changes_and_push = True
            else:
                git_commit_and_push_changes = git_commit_and_push_changes.lower()
                if is_pre_release and (
                    git_commit_and_push_changes in ('always', 'pre-release', 'prerelease') \
                ):
                    should_commit_changes_and_push = True
                elif not is_pre_release and git_commit_and_push_changes in ('always', 'release'):
                    should_commit_changes_and_push = True

        return should_commit_changes_and_push
