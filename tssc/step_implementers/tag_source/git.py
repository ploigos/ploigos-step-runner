"""Step Implementer for the tag-source step for Git.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required?          | Default              | Description
|-------------------|--------------------|----------------------|-----------
| `url`             | False              | git url returned by  | This is the url for the git
                                           `git config --get      server.
                                           remote.origin.url`
                                           in container
| `username`        | True (if url       | n/a                  | This is the username to use.
                      is http or https)                           Due to security concerns this
                                                                  should only be only provided by
                                                                  the runtime configuration
| `password`        | True (if url       | n/a                  | This is the password to use.
                      is http or https)                           Due to security concerns this
                                                                  should only be only provided by
                                                                  the runtime configuration

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step may require. If not found, it
will attempt to tag the source with `latest`

| Step Name           | Result Key | Description
|---------------------|------------|------------
| `generate-metadata` | `version`  | Semantic version, if not found this step
                                     will use `latest` as the version to perform
                                     the git tag with

Results
-------

Results output by this step.

| Result Key | Description
|------------|------------
| `tag`      | This is the value that was used to tag the source.


**Example**

    'tssc-results': {
        'tag-source': {
            'git-tag': 'latest'
        }
    }
"""
import re
import sys
from io import StringIO

import sh
from tssc import DefaultSteps, StepImplementer

DEFAULT_CONFIG = {}

AUTHENTICATION_CONFIG = {
    'username': None,
    'password': None
}


class Git(StepImplementer):
    """
    StepImplementer for the tag-source step for Git.

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
        return []

    def _validate_runtime_step_config(self, runtime_step_config):
        """
        Validates the given `runtime_step_config` against the required step configuration keys.

        Parameters
        ----------
        runtime_step_config : dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.

        Raises
        ------
        AssertionError
            If the given `runtime_step_config` is not valid with a message as to why.
        """
        super()._validate_runtime_step_config(runtime_step_config) #pylint: disable=protected-access

        assert ( \
            all(element in runtime_step_config for element in AUTHENTICATION_CONFIG) or \
            not any(element in runtime_step_config for element in AUTHENTICATION_CONFIG) \
        ), 'Either username or password is not set. Neither or both must be set.'

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        dict
            Results of running this step.
        """
        username = None
        password = None

        if self.has_config_value(AUTHENTICATION_CONFIG):
            if(self.get_config_value('username') \
              and self.get_config_value('password')):
                username = self.get_config_value('username')
                password = self.get_config_value('password')
            else:
                raise ValueError(
                    'Both username and password must have ' \
                    'non-empty value in the runtime step configuration'
                )
        else:
            print('No username/password found, assuming ssh')
        tag = self._get_tag()
        self._git_tag(tag)
        git_url = self._git_url()
        if git_url.startswith('http://'):
            if username and password:
                self._git_push('http://' + username + ':' + password + '@' + git_url[7:])
            else:
                raise ValueError(
                    'For a http:// git url, you need to also provide ' \
                    'username/password pair'
                )
        elif git_url.startswith('https://'):
            if username and password:
                self._git_push('https://' + username + ':' + password + '@' + git_url[8:])
            else:
                raise ValueError(
                    'For a https:// git url, you need to also provide ' \
                    'username/password pair'
                )
        else:
            self._git_push(None)
        results = {
            'tag' : tag
        }
        return results

    def _get_tag(self):
        tag = 'latest'
        if(self.get_step_results(DefaultSteps.GENERATE_METADATA) \
          and self.get_step_results(DefaultSteps.GENERATE_METADATA).get('version')):
            tag = self.get_step_results(DefaultSteps.GENERATE_METADATA).get('version')
        else:
            print('No version found in metadata. Using latest')
        return tag

    def _git_url(self):
        git_url = None
        if self.get_config_value('url'):
            git_url = self.get_config_value('url')
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

                # remove ANYTHING@ from begining of git_url since step will pass in its own
                # username and password
                #
                # Regex:
                #   ^[^@]+@ - match from begining of line any charcter up until an @ and then the @
                #   (.*) - match any character and capture to capture group 1
                #   \1 - capture group 1 which is the http or https if there was one
                #   \2 - capture group 2 which is anything after the first @ if there was one
                git_url = re.sub(r"^(http://|https://)[^@]+@(.*)", r"\1\2", git_url)

            except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable # pragma: no cover
                raise RuntimeError('Error invoking git config --get remote.origin.url') from error
        return git_url

    @staticmethod
    def _git_tag(git_tag_value):  # pragma: no cover
        try:
            # NOTE:
            # this force is only needed locally in case of a re-reun of the same pipeline
            # without a fresh check out. You will notice there is no force on the push
            # making this an acceptable work around to the issue since on the off chance
            # actually orverwriting a tag with a different comment, the push will fail
            # because the tag will be attached to a different git hash.
            sh.git.tag(  # pylint: disable=no-member
                git_tag_value,
                '-f',
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )
        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise RuntimeError(f"Error pushing git tag ({git_tag_value}): {error}") from error

    @staticmethod
    def _git_push(url=None):  # pragma: no cover
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
            raise RuntimeError('Error invoking git push') from error
