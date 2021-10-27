"""`StepImplementer` for the `tag-source` step using Git.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key | Required? | Default  | Description
------------------|-----------|----------|-----------
`version`         | No        | `latest` | Semantic version to use as Git tag.
`git-repo-root`   | Yes       | `./`     | Directory path to the Git repository to perform git operations on.
`repo-root`       | No        |          | Alias for `git-repo-root`.
`git-url`         | No        | Git repo root configured origin url \
                                         | URL to Git repository to perform Git operations on. \
                                           If not given will use Git remote url set in given Git repository root.
`url`             | No        |          | Alias for `git-url`.
`git-username`    | No        |          | Git username to use when connecting with Git remote. \
                                           Will override username in given git url. \
                                           Will override username in Git url in Git repository root remote url. \
                                           Will be ignored if Git repository url is using SSH.
`git-password`    | No        |          | Git password to use when connecting with Git remote. \
                                           Will override password in given git url. \
                                           Will override password in Git url in Git repository root remote url. \
                                           Will be ignored if Git repository url is using SSH.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`tag`               | This is the value that was used to tag the source.
"""# pylint: disable=line-too-long

from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared import GitMixin

DEFAULT_CONFIG = {
    'version': 'latest',
    'git-repo-root': './',
}
"""
Note
---
Some required fields inherited from GitMixin (see `_required_config_or_result_keys`)
"""
REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = []

class Git(StepImplementer, GitMixin):
    """StepImplementer for the tag-source step for Git.

    Note
    ----
    This makes extensive use of the python sh library. This was a deliberate choice,
    as the gitpython library doesn't appear to easily support username/password auth
    for http and https git repos, and that is a desired use case.
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

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # get the tag
        tag = self.__get_tag_value()
        step_result.add_artifact(
            name='tag',
            value=tag
        )

        # tag and push tags
        try:
            self.git_tag(tag)
            self.git_push_tags()
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = f"Error tagging and pushing tags: {error}"

        return step_result

    def __get_tag_value(self):
        """Get the tag value to tag the Git repository with.

        Returns
        -------
        str
            Value to use for the git tag.
        """
        tag = self.get_value('version')
        if tag is None:
            tag = 'latest'
            print('No version found in metadata. Using latest')
        return tag
