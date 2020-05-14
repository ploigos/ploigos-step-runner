"""
Abstract class and helper constants for StepImplementer.
"""

from abc import ABC, abstractmethod
import os
import yaml
from .exceptions import TSSCException

_TSSC_RESULTS_KEY = 'tssc-results'

class DefaultSteps: # pylint: disable=too-few-public-methods
    """
    Convinence constants for the default steps used in the default TSSC wofkflow definition.
    """
    GENERATE_METADATA = 'generate-metadata'
    TAG_SOURCE = 'tag-source'
    SECURITY_STATIC_CODE_ANALYSIS = 'security-static-code-analysis'
    LINTING_STATIC_CODE_ANALYSIS = 'security-static-code-analysis'
    PACKAGE = 'package'
    UNIT_TEST = 'unit-test'
    PUSH_ARTIFACTS = 'push-artifacts'
    CREATE_CONTAINER_IMAGE = 'create-container'
    PUSH_CONTAINER_IMAGE = 'push-container-image'
    CONTAINER_IMAGE_UNIT_TEST = 'container-image-unit-test'
    CONTAINER_IMAGE_STATIC_COMPLIANCE_SCAN = 'container-image-static-compliance-scan'
    CONTAINER_IMAGE_STATIC_ULNERABILITY_SCAN = 'container-image-static-vulnerability-scan'
    PUSH_TRUSTED_CONTAINER_IMAGE = 'push-trusted-container-image'
    CREATE_KUBE_PROJECT = 'create-kube-project'
    DEPLOY_TO_KUBE_PROJECT = 'deploy-to-kube-project'
    UAT = 'uat'
    RUNTIME_VULNERABILITY_SCAN = 'runtime-vulnerability-scan'
    CANARY_TEST = 'canary-test'
    PUBLISH_WROKFLOW_RESULTS = 'publish-workflow-results'

class StepImplementer(ABC): # pylint: disable=too-few-public-methods
    """
    Abstract represnetation of a TSSC step implementer.

    Parameters
    ----------
    config : dict
        Configuration specific to the StepImplementer
    results_dir_path : str
        Path to the file to write the results of the step to
    config_defaults : dict
        Defaults for any items not given in the config
    """

    def __init__(self, step_name, config, results_dir_path, config_defaults=None):
        self.step_name = step_name
        if not config_defaults:
            config_defaults = {}
        step_config = {**config_defaults, **config}
        self.step_config = step_config
        self.results_dir_path = results_dir_path
        super().__init__()

    @property
    def step_config(self):
        """
        Getter for step_config property.
        """
        return self.__step_config

    @step_config.setter
    def step_config(self, val):
        """
        Setter with validation for step_config property.
        """
        self.validate_step_config(val)
        self.__step_config = val

    def validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuraiton to validate.

        Raises
        ------
        TSSCException
            If existing step results file has invalid YAML.
        """

    def write_results(self, results):
        """
        Write the given results to a results file specific to this step in the results directory.

        Parameters
        ----------
        restuls : dict
            Dictionary of results to write to the step specific results file.
        """
        if not os.path.exists(self.results_dir_path):
            os.makedirs(self.results_dir_path)

        step_results_file_name = self.step_name + '.yml'
        step_results_file_path = os.path.join(self.results_dir_path, step_results_file_name)

        current_step_results = None
        if os.path.exists(step_results_file_path):
            with open(step_results_file_path, 'r') as step_results_file:
                try:
                    current_step_results = yaml.safe_load(step_results_file.read())
                except (yaml.scanner.ScannerError, ValueError) as err:
                    raise TSSCException(
                        'Existing results file'
                        + ' (' + step_results_file_path + ')'
                        + ' for step (' + self.step_name + ')'
                        + ' has invalid yaml: ' + str(err)
                    )

            if current_step_results:
                if _TSSC_RESULTS_KEY not in current_step_results:
                    raise TSSCException(
                        'Existing results file'
                        + ' (' + step_results_file_path + ')'
                        + ' for step (' + self.step_name + ')'
                        + ' does not have expected top level element'
                        + ' (' + _TSSC_RESULTS_KEY + '): ' + str(current_step_results)
                    )
        else:
            current_step_results = {
                _TSSC_RESULTS_KEY: {}
            }

        new_step_results = {
            _TSSC_RESULTS_KEY: {
                self.step_name: results
            }
        }
        updated_step_results = {**current_step_results, **new_step_results}

        with open(step_results_file_path, 'w') as step_results_file:
            yaml.dump(updated_step_results, step_results_file)

    @abstractmethod
    def run_step(self, **kwargs):
        """
        Runs the TSSC step implmented by this StepImplementer.

        Parameters
        ----------
        kwargs
            TODO
        """
