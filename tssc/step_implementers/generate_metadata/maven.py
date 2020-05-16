"""
com.redhat.tssc.step_implementers.metadata_generator.maven
"""

import re
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

    def __init__(self, config, results_file):
        super().__init__(config, results_file, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.GENERATE_METADATA

    def validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """
        if 'pom-file' not in step_config:
            raise ValueError('Key (pom-file) must be in the step configuration')

    def run_step(self, **kwargs):
        runtime_step_config = {**self.step_config, **kwargs}
        pom_file = runtime_step_config['pom-file']

        # verify runtime config
        if not os.path.exists(pom_file):
            raise ValueError('Given pom file does not exist: ' + pom_file)

        # parse the pom file and figure out the namespace if there is one
        pom_xml = ElementTree.parse(pom_file)
        pom_root = pom_xml.getroot()
        pom_namespace_match = re.match(r'\{.*}', str(pom_root.tag))
        pom_namespace = ''
        if pom_namespace_match:
            pom_namespace = pom_namespace_match.group(0)

        # extract needed information from the pom file
        pom_version_element = pom_xml.getroot().find('./' + pom_namespace + 'version')

        # verify information from pom file
        if pom_version_element is None:
            raise ValueError('Given pom file (' + pom_file + ') does not have ./version element')

        pom_version = pom_version_element.text

        results = {
            'version': pom_version
        }

        self.write_results(results)

    def example_without_test(self):
        """
        example of bad PR with missing test
        """
        print(self.step_name)


# register step implementer
TSSCFactory.register_step_implementer(Maven)
