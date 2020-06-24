"""
Step Implementer for the generate-metadata step for Maven.
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
    StepImplementer for the generate-metadata step for Maven.

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

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """
        if 'pom-file' not in step_config or not step_config['pom-file']:
            raise ValueError('Key (pom-file) must have none empty value in the step configuration')

    def _run_step(self, runtime_step_config):
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
            'app-version': pom_version
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(Maven)
