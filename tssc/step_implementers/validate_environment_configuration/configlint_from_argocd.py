"""Step Implementer for the 'validate-environment-config' step for ConfiglintFromArgocd.
The ConfiglintFromArogcd step takes the output of the Deploy (argocd) step and prepares
it as input for the Configlint step.

Step Configuration
------------------
Step configuration expected as input to this step.  Could come from either
configuration file or from runtime configuration.

| Configuration Key     | Required | Default                   | Description
|-----------------------|----------|---------------------------|---------------------------
| `argocd-result-set`   | True     | N/A                       | Yml file to be linted

Results
-------
Results output by this step.

| Result Key            | Description
|-----------------------|------------
| `configlint-yml-file` | Yml file to be linted

"""

import os
from tssc.step_result import StepResult

from tssc import StepImplementer

DEFAULT_CONFIG = {
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'argocd-result-set'
]

class ConfiglintFromArgocd(StepImplementer):
    """
    StepImplementer for the validate-environment-configuration sub-step ConfiglintFromArgocd
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
        """
        Getter for step configuration keys that are required before running the step.

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
        step_result = StepResult.from_step_implementer(self)

        argocd_result_set = self.get_value('argocd-result-set')

        if not os.path.exists(argocd_result_set):
            step_result.success = False
            step_result.message = 'File specified in ' \
                                  f'argocd-result-set {argocd_result_set} not found'
            return step_result

        step_result.add_artifact(
            name='configlint-yml-path',
            value=argocd_result_set
        )
        return step_result
