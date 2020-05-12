"""
com.redhat.tssc.step_implementers.metadata_generator
"""

from .. import TSSCFactory

class MetadataGenerator: # pylint: disable=too-few-public-methods 
    """
    Default step implementer for the generate-metadata step.

    Attributes
    ----------
    step_name : str
        TSSC step that this Step Implementer implements
    """
    step_name = 'generate-metadata'

    def __init__(self, config):
        self.config = config

    def call(self):
        """
        Generate the metadata.
        """
        print('MetadataGenerator.call - TODO: (' + str(self.config) + ')')

# register step implementer
TSSCFactory.register_step_implementer(MetadataGenerator.step_name, MetadataGenerator, True)
