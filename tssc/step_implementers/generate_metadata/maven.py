"""
com.redhat.tssc.step_implementers.metadata_generator.maven
"""

import os.path
from xml.etree import ElementTree

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {
    'pom-file': 'pom.xml'
}

class Maven(StepImplementer): # pylint: disable=too-few-public-methods 
    """
    Default step implementer for the generate-metadata step.

    Attributes
    ----------
    STEP_NAME: str
        TSSC step that this StepImplementer implements

    Raises
    ------
    ValueError
        If given pom file does not exist
        If given pom file does not contain required elements
    """

    STEP_NAME = DefaultSteps.GENERATE_METADATA

    def __init__(self, config, results_file):
        super().__init__(Maven.STEP_NAME, config, results_file, DEFAULT_ARGS)

    def validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuraiton to validate.
        """
        if 'pom-file' not in step_config:
            raise ValueError('Key (pom-file) must be in the step configuration')

    def run_step(self, **kwargs):
        runtime_step_config = {**self.step_config, **kwargs}
        pom_file = runtime_step_config['pom-file']

        # verify runtime config
        if not os.path.exists(pom_file):
            raise ValueError('Given pom file does not exist: ' + pom_file)

        # parse the pom file
        pom_xml = ElementTree.parse(pom_file)

        # extract needed information from the pom file
        pom_version_element = pom_xml.getroot().find("./version")
        pom_group_id_element = pom_xml.getroot().find("./groupId")
        pom_artifact_id_element = pom_xml.getroot().find("./artifactId")

        # verify information from pom file
        if pom_version_element is None:
            raise ValueError('Given pom file (' + pom_file + ') does not have ./version element')

        if pom_group_id_element is None:
            raise ValueError('Given pom file (' + pom_file + ') does not have ./groupId element')

        if pom_artifact_id_element is None:
            raise ValueError('Given pom file (' + pom_file + ') does not have ./artifactId element')


        pom_version = pom_version_element.text
        pom_group_id = pom_group_id_element.text
        pom_artifact_id = pom_artifact_id_element.text

        print(pom_version)
        print(pom_group_id)
        print(pom_artifact_id)



# register step implementer
TSSCFactory.register_step_implementer(Maven)
