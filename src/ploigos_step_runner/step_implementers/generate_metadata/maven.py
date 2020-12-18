"""`StepImplementer` for the `generate-metadata` step using Maven.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key | Required? | Default     | Description
------------------|-----------|-------------|-----------
`pom-file`        | True      | `'pom.xml'` | pom file to read the app version out of

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`app-version`       | Value to use for `version` portion of semantic version \
                      (https://semver.org/). Uses the version read out of the given pom file.
"""

import os.path

from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.utils.xml import get_xml_element

DEFAULT_CONFIG = {
    'pom-file': 'pom.xml'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'pom-file'
]


class Maven(StepImplementer):  # pylint: disable=too-few-public-methods
    """`StepImplementer` for the `generate-metadata` step using Maven.
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

        pom_file = self.get_value('pom-file')
        assert os.path.exists(pom_file), \
            f'Given pom file (pom-file) does not exist: {pom_file}'

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        pom_file = self.get_value('pom-file')

        pom_version = None
        try:
            pom_version_element = get_xml_element(pom_file, 'version')
            pom_version = pom_version_element.text
        except ValueError:
            pom_version = None

        if not pom_version:
            step_result.success = False
            step_result.message = f'Given pom file ({pom_file})' + \
                ' does not contain a \"version\" key.'
            return step_result

        step_result.add_artifact(
            name='app-version',
            value=pom_version
        )

        return step_result
