"""
Step Implementer for the generate-metadata step for generating a
semantic version from other metadata.

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
Could come from either configuration file or
from runtime configuration.

.. Note::
    This step implementer has not step configuration.

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

| Step Name           | Result Key    | Description
|---------------------|---------------|------------
| `generate-metadata` | `app-version` | Value to use for `version` portion of semantic version \
                                        (https://semver.org/).
| `generate-metadata` | `pre-release` | Value to use for `pre-release` portion of semantic version \
                                        (https://semver.org/). \
                                        Uses the Git branch name.
| `generate-metadata` | `build`       | Value to use for `build` portion of semantic version \
                                        (https://semver.org/). \
                                        Uses a portion of the latest Git commit hash.

Results
-------

Results output by this step.

| Result Key  | Description
|-------------|------------
| `version`   | Constructed semantic version (https://semver.org/).
| `image-tag` | Constructed semantic version (https://semver.org/) without build #

Examples
--------

**Example 1**

*Previous Step Results*

    {'tssc-results': {
      'generate-metadata': {
        'app-version': '1.0.0',
        'pre-release': 'feature_test0',
        'build': 'abc123'
      }
    }

*Step Results after this Step Implementer*

    {'tssc-results': {
      'generate-metadata': {
        'app-version': '42.1.0',
        'pre-release': 'feature_test0',
        'build': 'abc123',
        'version': '42.1.0-feature_foo+abc123',
        'image-tag': '42.1.0-feature_foo'
      }
    }}

**Example 2**

*Previous Step Results*

    {'tssc-results': {
      'generate-metadata': {
        'app-version': '42.1.0',
        'pre-release': 'master',
        'build': 'abc123'
      }
    }

*Step Results after this Step Implementer*

    {'tssc-results': {
      'generate-metadata': {
        'app-version': '42.1.0',
        'pre-release': 'master',
        'build': 'abc123',
        'version': '42.1.0+abc123',
        'image-tag': '42.1.0'
      }
    }}
"""

from tssc import StepImplementer

DEFAULT_CONFIG = {
    'release-branch': 'master'
}


class SemanticVersion(StepImplementer):  # pylint: disable=too-few-public-methods
    """
    StepImplementer for the generate-metadata step for SemanticVersion.
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

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        dict
            Results of running this step.
        """
        app_version = None
        pre_release = None
        build = None

        release_branch = self.get_config_value('release-branch')

        app_version = self.get_config_value('app-version')

        if app_version is None:
            app_version = self.get_artifact_value(step_name='generate-metadata',
                                                  artifact_name='app-version')

        if app_version is None:
            self.step_result.success = False
            self.step_result.message = f'No value for (app-version) provided via runtime flag ' \
                                       f'(app-version) or from prior step implementer ' \
                                       f'({self.step_name})'
            return

        pre_release = self.get_config_value('pre-release')

        if pre_release is None:
            pre_release = self.get_artifact_value(step_name=self.step_name,
                                                  artifact_name='pre-release')

        if pre_release is None:
            self.step_result.success = False
            self.step_result.message = f'No value for (pre-release) provided via runtime flag ' \
                                       f'(pre-release) or from prior step implementer ' \
                                       f'({self.step_name})'
            return

        build = self.get_config_value('build')
        if build is None:
            build = self.get_artifact_value(step_name=self.step_name,
                                            artifact_name='build')

        if build is None:
            self.step_result.success = False
            self.step_result.message = f'No value for (build) provided via runtime flag ' \
                                       f'(build) or from prior step implementer ({self.step_name})'
            return

        if pre_release == release_branch:
            version = "{0}+{1}".format(app_version, build)
            image_tag = "{0}".format(app_version)
        else:
            version = "{0}-{1}+{2}".format(app_version, pre_release, build)
            image_tag = "{0}-{1}".format(app_version, pre_release)

        self.step_result.add_artifact(name='version', value=version)
        self.step_result.add_artifact(name='container-image-version', value=image_tag)
