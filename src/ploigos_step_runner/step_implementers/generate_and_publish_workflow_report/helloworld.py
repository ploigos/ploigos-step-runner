"""`StepImplementers` for the `generate_and_publish_workflow_report` step.
"""
from ploigos_step_runner import StepImplementer
from ploigos_step_runner.step_result import StepResult


DEFAULT_CONFIG = {
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'container-image-signer-pgp-private-key',
    'container-image-tag'
]


class HelloWorld(StepImplementer):  
    """StepImplementer for the generate-and-publish-workflow-report step for HelloWorld.
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
	    #TODO - Add Logic Here
        print("Step Implementer Hello World")
        return step_result
