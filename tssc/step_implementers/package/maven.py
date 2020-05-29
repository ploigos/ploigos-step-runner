"""
Step Implementer for the package step for Maven.
"""

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {}

class Maven(StepImplementer):
    """
    StepImplementer for the package step for Maven.
    """

    def __init__(self, config, results_file):
        super().__init__(config, results_file, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.PACKAGE

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
TSSCFactory.register_step_implementer(Maven)
