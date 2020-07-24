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

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

from tssc.step_implementers.utils.xml import get_xml_element

DEFAULT_ARGS = {
    'pom-file': 'pom.xml'
}

class Maven(StepImplementer): # pylint: disable=too-few-public-methods 
    """
    StepImplementer for the generate-metadata step for Maven.

    Raises
    ------
    ValueError
        If given pom file does not exist
        If given pom file does not contain required elements
    """

    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, DEFAULT_ARGS)

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
        if 'pom-file' not in step_config or not step_config['pom-file']:
            raise ValueError('Key (pom-file) must have none empty value in the step configuration')

    def _run_step(self, runtime_step_config):
        pom_file = runtime_step_config['pom-file']

        # verify runtime config
        if not os.path.exists(pom_file):
            raise ValueError('Given pom file does not exist: ' + pom_file)

        pom_version_element = get_xml_element(pom_file, 'version')
        pom_version = pom_version_element.text

        results = {
            'app-version': pom_version
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(Maven)
