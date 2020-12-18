"""`StepImplementer` for the `generate-metadata` step using NPM.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key | Required? | Default          | Description
------------------|-----------|------------------|-----------
`package-file`    | True      | `'package.json'` | node.js package file to read \
                                                   the app version out of

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`app-version`       | Value to use for `version` portion of semantic version \
                      (https://semver.org/). Uses the version read out of the given pom file.
"""

import json
import os.path

from ploigos_step_runner import StepImplementer
from ploigos_step_runner.step_result import StepResult

DEFAULT_CONFIG = {
    'package-file': 'package.json'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'package-file'
]

class Npm(StepImplementer): # pylint: disable=too-few-public-methods
    """`StepImplementer` for the `generate-metadata` step using NPM.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

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
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * given 'package-file' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        package_file = self.get_value('package-file')
        assert os.path.exists(package_file), \
            f'Given npm package file (package-file) does not exist: {package_file}'

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        package_file = self.get_value('package-file')

        with open(package_file) as package_file_object:
            package_file_data = json.load(package_file_object)

        if not "version" in package_file_data:
            step_result.success = False
            step_result.message = f'Given npm package file ({package_file})' + \
              ' does not contain a \"version\" key.'
            return step_result

        step_result.add_artifact(
            name='app-version',
            value=package_file_data["version"]
        )

        return step_result
