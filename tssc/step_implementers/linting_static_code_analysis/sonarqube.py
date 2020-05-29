"""
Step Implementer for the linting-static-code-analysis step for SonarQube.
"""

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {}

class SonarQube(StepImplementer):
    """
    StepImplementer for the tag-source step for SonarQube.
    """

    def __init__(self, config, results_file):
        super().__init__(config, results_file, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.LINTING_STATIC_CODE_ANALYSIS

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
