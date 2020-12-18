"""`StepImplementer` for the `generate-metadata` to generate a semantic version from given input.

Supports the following semantic versions (https://semver.org/) :

  - major.minor.patch+build
  - major.minor.patch-pre_rleease+build

Notes
-----
When tagging container images we will regex + to - due
to https://github.com/docker/distribution/issues/1201.

Source for version sections:

  - major.minor.patch
    * will come from previous sub step of generate_metadata step,
      with step results including 'app_version'
    * known implementers:
      -  maven
  - pre-release
    * will come from previous sub step of generate_metadata step,
      with step results including 'pre_release'
    * known implementers:
      - git
  - build
    * will come from previous sub step of generate_metadata step,
      with step results including 'build'
    * known implementers:
      - git

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key | Required? | Default | Description
------------------|-----------|---------|-----------
`app-version`     | Yes       |         | Value to use for `version` portion of \
                                          semantic version (https://semver.org/).
`pre-release`     | No        |         | Value to use for `pre-release` portion \
                                          of semantic version (https://semver.org/). \
`build`           | Yes       |         | Value to use for `build` portion \
                                          of semantic version (https://semver.org/).

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key       | Description
--------------------------|------------
`version`                 | Constructed semantic version (https://semver.org/).
`container-image-version` | Constructed semantic version (https://semver.org/) without build number
"""

from ploigos_step_runner import StepImplementer
from ploigos_step_runner.step_result import StepResult

DEFAULT_CONFIG = {
    'release-branch': 'master'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'app-version',
    'pre-release',
    'release-branch',
    'build'
]

class SemanticVersion(StepImplementer):  # pylint: disable=too-few-public-methods
    """`StepImplementer` for the `generate-metadata` to generate a
    semantic version from given input.
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

        app_version = None
        pre_release = None
        build = None
        release_branch = self.get_value('release-branch')
        app_version = self.get_value('app-version')
        pre_release = self.get_value('pre-release')
        build = self.get_value('build')

        if pre_release == release_branch:
            version = f'{app_version}+{build}'
            image_tag = f'{app_version}'
        else:
            version = f'{app_version}-{pre_release}+{build}'
            image_tag = f'{app_version}-{pre_release}'

        step_result.add_artifact(
            name='version',
            value=version
        )
        step_result.add_artifact(
            name='container-image-version',
            value=image_tag
        )

        return step_result
