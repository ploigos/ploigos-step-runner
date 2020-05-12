"""
com.redhat.tssc.step_implementers.sonarqube
"""

from .. import TSSCFactory

class SonarQube: # pylint: disable=too-few-public-methods 
    """
    SonarQube implementation of the security-static-code-analysis TSSC step.

    Attributes
    ----------
    step_name : str
        TSSC step that this Step Implementer implements
    """
    step_name = 'security-static-code-analysis'

    def __init__(self, config):
        self.config = config

    def call(self):
        """
        Invoke SonarQube
        """
        print('SonarQube.call - TODO: (' + str(self.config) + ')')

# register step implementer
TSSCFactory.register_step_implementer(SonarQube.step_name, SonarQube)
