"""`StepImplementer` for the `tag-source` step using Git.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key | Required?          | Default              | Description
------------------|--------------------|----------------------|-----------
`url`             | Yes                | git url returned by \
                                         `git config --get \
                                         remote.origin.url` \
                                         in container         | This is the url for the \
                                                                git server.
`git-username`    | Yes (if url \
                    is http or https)  |                      | This is the username to use. \
                                                                Due to security concerns this \
                                                                should only be only provided by \
                                                                the runtime configuration
`git-password`    | Yes (if url \
                    is http or https)  |                      | This is the password to use. \
                                                                Due to security concerns this \
                                                                should only be only provided by \
                                                                the runtime configuration
`version`         | No                 | `latest`             | Semantic version, \
                                                                if not found this step \
                                                                will use `latest` as the version \
                                                                to perform the git tag with

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`tag`               | This is the value that was used to tag the source.
"""
import re
import sys
from io import StringIO

import sh
from ploigos_step_runner import StepImplementer
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_result import StepResult

DEFAULT_CONFIG = {}

AUTHENTICATION_CONFIG = {
    'git-username': None,
    'git-password': None
}


class Git(StepImplementer):
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
        return []

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * either both git-username and git-password are set or neither.

        Raises
        ------
        StepRunnerException
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # ensure either both git-username and git-password are set or neither
        runtime_auth_config = {}
        for auth_config_key in AUTHENTICATION_CONFIG:
            runtime_auth_config_value = self.get_value(auth_config_key)

            if runtime_auth_config_value is not None:
                runtime_auth_config[auth_config_key] = runtime_auth_config_value

        if (any(element in runtime_auth_config for element in AUTHENTICATION_CONFIG)) and \
                (not all(element in runtime_auth_config for element in AUTHENTICATION_CONFIG)):
            raise StepRunnerException(
                "Either 'git-username' or 'git-password 'is not set. Neither or both must be set."
            )

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        username = None
        password = None

        if self.has_config_value(AUTHENTICATION_CONFIG):
            username = self.get_value('git-username')
            password = self.get_value('git-password')
        else:
            print('No username/password found, assuming ssh')

        tag = self.__get_tag()

        try:
            self.__git_tag(tag)
            git_url = self.__git_url()
            if git_url.startswith('http://'):
                if username and password:
                    self.__git_push('http://' + username + ':' + password + '@' + git_url[7:])
                else:
                    step_result.success = False
                    step_result.message = 'For a http:// git url, you need to also provide ' \
                                        'username/password pair'
                    return step_result
            elif git_url.startswith('https://'):
                if username and password:
                    self.__git_push('https://' + username + ':' + password + '@' + git_url[8:])
                else:
                    step_result.success = False
                    step_result.message = 'For a https:// git url, you need to also provide ' \
                                        'username/password pair'
                    return step_result
            else:
                self.__git_push(None)
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = str(error)

        step_result.add_artifact(
            name='tag',
            value=tag
        )

        return step_result

    def __get_tag(self):
        tag = self.get_value('version')
        if tag is None:
            tag = 'latest'
            print('No version found in metadata. Using latest')
        return tag

    def __git_url(self):
        git_url = None
        if self.get_value('url'):
            git_url = self.get_value('url')
        else:
            try:
                out = StringIO()
                sh.git.config(
                    '--get',
                    'remote.origin.url',
                    _encoding='UTF-8',
                    _decode_errors='ignore',
                    _out=out,
                    _err=sys.stderr,
                    _tee='err'
                )
                git_url = out.getvalue().rstrip()

                # remove ANYTHING@ from beginning of git_url since step will pass in its own
                # username and password
                #
                # Regex:
                #   ^[^@]+@ - match from beginning of line any character up until
                #             an @ and then the @
                #   (.*) - match any character and capture to capture group 1
                #   \1 - capture group 1 which is the http or https if there was one
                #   \2 - capture group 2 which is anything after the first @ if there was one
                git_url = re.sub(r"^(http://|https://)[^@]+@(.*)", r"\1\2", git_url)

            except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
                raise StepRunnerException(
                    f"Error invoking git config --get remote.origin.url: {error}"
                ) from error
        return git_url

    @staticmethod
    def __git_tag(git_tag_value):
        try:
            # NOTE:
            # this force is only needed locally in case of a re-run of the same pipeline
            # without a fresh check out. You will notice there is no force on the push
            # making this an acceptable work around to the issue since on the off chance
            # actually overwriting a tag with a different comment, the push will fail
            # because the tag will be attached to a different git hash.
            sh.git.tag(  # pylint: disable=no-member
                git_tag_value,
                '-f',
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )
        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise StepRunnerException(
                f"Error pushing git tag ({git_tag_value}): {error}"
            ) from error

    @staticmethod
    def __git_push(url=None):
        try:
            if url:
                sh.git.push(
                    url,
                    '--tag',
                    _out=sys.stdout,
                    _err=sys.stderr,
                    _tee='err'
                )
            else:
                sh.git.push(
                    '--tag',
                    _out=sys.stdout,
                    _err=sys.stderr,
                    _tee='err'
                )
        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise StepRunnerException(f"Error invoking git push: {error}") from error
