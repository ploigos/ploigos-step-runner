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
    results_file : str
        Path to the file to write the results of the step to
    config_defaults : dict
        Defaults for any items not given in the config
    """

    def __init__(self, step_name, config, results_file, config_defaults=None):
        self.step_name = step_name
        if not config_defaults:
            config_defaults = {}
        step_config = {**config_defaults, **config}
        self.step_config = step_config
        self.results_file = results_file
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
        """

    @abstractmethod
    def run_step(self, **kwargs):
        """
        Runs the TSSC step implmented by this StepImplementer.

        Parameters
        ----------
        kwargs
            TODO
        """
