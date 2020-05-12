"""
com.redhat.tssc.step_implementer
"""

from abc import ABC, abstractmethod

class DefaultSteps: # pylint: disable=too-few-public-methods
    """
    Convinence constants for the default steps used in the default TSSC wofkflow definition.
    """
    GENERATE_METADATA = 'generate-metadata'
    TAG_SOURCE = 'tag-source'
    SECURITY_STATIC_CODE_ANALYSIS = 'security-static-code-analysis'

class StepImplementer(ABC): # pylint: disable=too-few-public-methods
    """
    Abstract represnetation of a TSSC step implementer.

    Parameters
    ----------
    config : dict
        Configuration specific to the StepImplementer
    """

    def __init__(self, config):
        self.config = config
        super().__init__()

    @abstractmethod
    def run_step(self):
        """
        Runs the TSSC step implmented by this StepImplementer.
        """
