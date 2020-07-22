"""
Step Implementer for the generate-metadata step for generating a
semantic version from other metadata.

Supports the following semantic versions (https://semver.org/) :
* major.minor.patch+build
* major.minor.patch-pre_rleease+build

Notes
-----
when tagging container images we will regex + to - due to https://github.com/docker/distribution/issues/1201.

Source for version sections:
* major.minor.patch
  * will come from previous sub step of generate_metadata step, with step results including 'app_version'
  * implmeneters
    * maven
* pre-release
  * will come from previous sub step of generate_metadata step, with step results including 'pre_release'
  * implmeneters
    * git
* build
  * will come from previous sub step of generate_metadata step, with step results including 'build'
  * implmeneters
    * git

Example 1
pom.xml: 1.0.0-SNAPSHOT
git branch: feature/foo
generated version: 1.0.0-feature_foo+GITHASH
docker tag: 1.0.0-feature_foo-GITHASH
step results:
{'tssc-results': {

  'generate-metadata': {

    'version': '42.1.0-feature_foo+GITHASH',

    'image-tag': '42.1.0-feature_foo-GITHASH'

    }

}}

Example 2
pom.xml: 1.0.0-SNAPSHOT
git branch: master
generated version: 1.0.0+GITHASH
docker tag: 1.0.0-GITHASH
step results:
{'tssc-results': {
  'generate-metadata': {
    'version': '42.1.0+GITHASH',
    'image-tag': '42.1.0-GITHASH',
   }
}}

"""

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {
    'release-branch': 'master'
}

class SemanticVersion(StepImplementer): # pylint: disable=too-few-public-methods 
    """
    StepImplementer for the generate-metadata step for SemanticVersion.

    Raises
    ------
    """

    def __init__(self, config, results_dir, results_file_name):
        super().__init__(config, results_dir, results_file_name, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.GENERATE_METADATA

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """

    def _run_step(self, runtime_step_config):
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
                """.format(self.step_name())
            )

        if 'pre-release' in runtime_step_config:
            pre_release = runtime_step_config['pre-release']
        elif 'pre-release' in current_step_results:
            pre_release = current_step_results['pre-release']
        else:
            raise ValueError(
                """No value for (pre_release) provided via runtime flag
                (pre-release) or from prior step implementer ({0})
                """.format(self.step_name()))

        if 'build' in runtime_step_config:
            build = runtime_step_config['build']
        elif 'build' in current_step_results:
            build = current_step_results['build']
        else:
            raise ValueError(
                """No value for (build) provided via runtime flag
                (build) or from prior step implementer ({0})
                """.format(self.step_name()))

        if pre_release == release_branch:
            version = "{0}+{1}".format(app_version, build)
            image_tag = "{0}-{1}".format(app_version, build)
        else:
            version = "{0}-{1}+{2}".format(app_version, pre_release, build)
            image_tag = "{0}-{1}-{2}".format(app_version, pre_release, build)

        results = {
            'version': version,
            'image-tag': image_tag
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(SemanticVersion)
