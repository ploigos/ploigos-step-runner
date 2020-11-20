"""Step Implementer for the generate-metadata step for Maven.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default     | Description
|-------------------|-----------|-------------|-----------
| `pom-file`        | True      | `'pom.xml'` | pom file to read the app version out of

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

.. Note:: This step implementer does not expect results from any previous steps.

Results
-------

Results output by this step.

| Result Key    | Description
|---------------|------------
| `app-version` | Value to use for `version` portion of semantic version (https://semver.org/). \
                    Uses the version read out of the given pom file.
"""

import os.path

from tssc import StepImplementer
from tssc.step_result import StepResult

from tssc.utils.xml import get_xml_element

DEFAULT_CONFIG = {
    'pom-file': 'pom.xml'
}

REQUIRED_CONFIG_KEYS = [
    'pom-file'
]


class Maven(StepImplementer):  # pylint: disable=too-few-public-methods
    """
    StepImplementer for the generate-metadata step for Maven.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

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
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.

        See Also
        --------
        _validate_runtime_step_config

        """
        return REQUIRED_CONFIG_KEYS

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Results of running this step.
        """
        step_result = StepResult.from_step_implementer(self)

        pom_file = self.get_config_value('pom-file')

        # verify runtime config
        if not os.path.exists(pom_file):
            step_result.success = False
            step_result.message = f'Given pom file does not exist: {pom_file}'
            return step_result

        pom_version_element = get_xml_element(pom_file, 'version')
        pom_version = pom_version_element.text

        step_result.add_artifact(
            name='app-version',
            value=pom_version
        )

        return step_result
