"""
com.redhat.tssc.step_implementers.metadata_generator
"""

from .. import TSSCFactory
from .. import StepImplementer
from .. import DefaultSteps

class MetadataGenerator(StepImplementer): # pylint: disable=too-few-public-methods 
    """
    Default step implementer for the generate-metadata step.

    Attributes
    ----------
    STEP_NAME: str
        TSSC step that this StepImplementer implements
    """

    STEP_NAME = DefaultSteps.GENERATE_METADATA

    def run_step(self):
        """
        Generate the metadata.
        """
        print('MetadataGenerator.call - TODO: (' + str(self.config) + ')')

# register step implementer
TSSCFactory.register_step_implementer(MetadataGenerator, True)
