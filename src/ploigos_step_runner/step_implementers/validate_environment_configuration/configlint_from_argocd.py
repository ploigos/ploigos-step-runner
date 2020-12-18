"""`StepImplementer` for the `validate-environment-configuration` step to take the output from
the `deploy` ArgoCD step implementer and turn it into input for the ConnfigLint implementer
for this step.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results


| Configuration Key     | Required | Default                   | Description
|-----------------------|----------|---------------------------|---------------------------
| `argocd-deployed-manifest`   | Yes      | N/A                       | Yml file to be linted

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key     | Description
------------------------|------------
| `configlint-yml-file` | Yml file to be linted

"""

import os
from ploigos_step_runner.step_result import StepResult

from ploigos_step_runner import StepImplementer

DEFAULT_CONFIG = {
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'argocd-deployed-manifest'
]

class ConfiglintFromArgocd(StepImplementer):
    """`StepImplementer` for the `validate-environment-configuration` step to take the output from
    the `deploy` ArgoCD step implementer and turn it into input for the ConnfigLint implementer
    for this step.
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
    def _required_config_or_result_keys():
        """Getter for step configuration keys that are required before running the step.

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.

        See Also
        --------
        _validate_required_config_or_previous_step_result_artifact_keys
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

        argocd_result_set = self.get_value('argocd-deployed-manifest')

        if not os.path.exists(argocd_result_set):
            step_result.success = False
            step_result.message = 'File specified in ' \
                                  f'argocd-deployed-manifest {argocd_result_set} not found'
            return step_result

        step_result.add_artifact(
            name='configlint-yml-path',
            value=argocd_result_set
        )
        return step_result
