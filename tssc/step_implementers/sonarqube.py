"""
com.redhat.tssc.step_implementers.sonarqube
"""

from .. import TSSCFactory
from .. import StepImplementer
from .. import DefaultSteps

class SonarQube(StepImplementer): # pylint: disable=too-few-public-methods 
    """
    SonarQube implementation of the security-static-code-analysis TSSC step.

    Attributes
    ----------
    STEP_NAME: str
        TSSC step that this StepImplementer implements
    """

    STEP_NAME = DefaultSteps.SECURITY_STATIC_CODE_ANALYSIS

 #   def __init__(self, config):
 #       super().__init__(config)

    def run_step(self):
        """
        Invoke SonarQube
        """
        print('SonarQube.run_step - TODO: (' + str(self.config) + ')')

# register step implementer
TSSCFactory.register_step_implementer(SonarQube)
