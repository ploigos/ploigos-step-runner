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

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_CONFIG = {
    'release-branch': 'master'
}

class SemanticVersion(StepImplementer): # pylint: disable=too-few-public-methods
    """
    StepImplementer for the generate-metadata step for SemanticVersion.
    """

    @staticmethod
    def step_name():
        """
        Getter for the TSSC Step name implemented by this step.

        Returns
        -------
        str
            TSSC step name implemented by this step.
        """
        return DefaultSteps.GENERATE_METADATA

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

    def _run_step(self, runtime_step_config):
        """
        Runs the TSSC step implemented by this StepImplementer.

        Parameters
        ----------
        runtime_step_config : dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.

        Returns
        -------
        dict
            Results of running this step.
        """
        app_version = None
        pre_release = None
        build = None
        release_branch = runtime_step_config['release-branch']

        current_step_results = self.current_step_results()
        if 'app-version' in runtime_step_config:
            app_version = runtime_step_config['app-version']
        elif 'app-version' in current_step_results:
            app_version = current_step_results['app-version']
        else:
            raise ValueError(
                """No value for (app-version) provided via runtime flag
                (app-version) or from prior step implementer ({0}).
                """.format(self.step_name))

        if 'pre-release' in runtime_step_config:
            pre_release = runtime_step_config['pre-release']
        elif 'pre-release' in current_step_results:
            pre_release = current_step_results['pre-release']
        else:
            raise ValueError(
                """No value for (pre_release) provided via runtime flag
                (pre-release) or from prior step implementer ({0})
                """.format(self.step_name))

        if 'build' in runtime_step_config:
            build = runtime_step_config['build']
        elif 'build' in current_step_results:
            build = current_step_results['build']
        else:
            raise ValueError(
                """No value for (build) provided via runtime flag
                (build) or from prior step implementer ({0})
                """.format(self.step_name))

        if pre_release == release_branch:
            version = "{0}+{1}".format(app_version, build)
            image_tag = "{0}".format(app_version)
        else:
            version = "{0}-{1}+{2}".format(app_version, pre_release, build)
            image_tag = "{0}-{1}".format(app_version, pre_release)

        results = {
            'version': version,
            'image-tag': image_tag
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(SemanticVersion)
