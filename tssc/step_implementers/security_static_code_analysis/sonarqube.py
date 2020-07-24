"""Step Implementer for the security-static-code-analysis step for SonarQube.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default | Description
|-------------------|-----------|---------|-----------
| `TODO`            | True      |         |

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

| Step Name | Result Key | Description
|-----------|------------|------------
| `TODO`    | `TODO`     | TODO

Results
-------

Results output by this step.

| Result Key | Description
|------------|------------
| `TODO`     | TODO


**Example**

    'tssc-results': {
        'TODO': {
            'TODO': ''
        }
    }
"""

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {}

class SonarQube(StepImplementer):
    """
    StepImplementer for the tag-source step for SonarQube.
    """

    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.SECURITY_STATIC_CODE_ANALYSIS

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """

    def _run_step(self, runtime_step_config):
        results = {
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(SonarQube)
