"""`StepImplementer` for the `generate-metadata` step to get metadata from GitLab.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key        | Required? | Default                  | Description
-------------------------|-----------|--------------------------|-----------
N/A                      |           |                          |

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`workflow-run-num`  | Incremental workflow run number.

"""# pylint: disable=line-too-long

import os

from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.results import StepResult

DEFAULT_CONFIG = {
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
]

class GitLab(StepImplementer):  # pylint: disable=too-few-public-methods
    """
    StepImplementer for the generate-metadata step for GitLab.
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

        step_result.add_artifact(
            name='workflow-run-num',
            value=os.environ.get('CI_PIPELINE_ID'),
            description='Incremental workflow run number'
        )

        return step_result
