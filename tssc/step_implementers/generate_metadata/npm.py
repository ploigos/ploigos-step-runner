"""Step Implementer for the generate-metadata step for npm.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default          | Description
|-------------------|-----------|------------------|-----------
| `package-file     | True      | `'package.json'` | node.js package file to
|                   |            |                 | ead the app version out of

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
import json

from tssc import StepImplementer

DEFAULT_CONFIG = {
    'package-file': 'package.json'
}

REQUIRED_CONFIG_KEYS = [
    'package-file'
]

class Npm(StepImplementer): # pylint: disable=too-few-public-methods
    """
    StepImplementer for the generate-metadata step for npm.
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
        return REQUIRED_CONFIG_KEYS

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        dict
            Results of running this step.
        """
        package_file = self.get_config_value('package-file')

        # verify runtime config
        if not os.path.exists(package_file):
            raise ValueError('Given npm package file does not exist: ' + package_file)

        with open(package_file) as package_file_object:
            package_file_data = json.load(package_file_object)

        if not "version" in package_file_data:
            raise ValueError('Given npm package file: ' + package_file + \
              ' does not contain a \"version\" key')

        results = {
            'app-version': package_file_data["version"]
        }

        return results
