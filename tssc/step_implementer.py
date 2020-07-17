"""
Abstract class and helper constants for StepImplementer.
"""

from abc import ABC, abstractmethod
import os
import pprint
import yaml
from tabulate import tabulate
from .exceptions import TSSCException


class DefaultSteps:  # pylint: disable=too-few-public-methods
    """
    Convenience constants for the default steps used in the default TSSC workflow definition.
    """
    GENERATE_METADATA = 'generate-metadata'
    TAG_SOURCE = 'tag-source'
    SECURITY_STATIC_CODE_ANALYSIS = 'security-static-code-analysis'
    LINTING_STATIC_CODE_ANALYSIS = 'linting-static-code-analysis'
    PACKAGE = 'package'
    UNIT_TEST = 'unit-test'
    PUSH_ARTIFACTS = 'push-artifacts'
    CREATE_CONTAINER_IMAGE = 'create-container-image'
    PUSH_CONTAINER_IMAGE = 'push-container-image'
    CONTAINER_IMAGE_UNIT_TEST = 'container-image-unit-test'
    CONTAINER_IMAGE_STATIC_COMPLIANCE_SCAN = 'container-image-static-compliance-scan'
    CONTAINER_IMAGE_STATIC_VULNERABILITY_SCAN = 'container-image-static-vulnerability-scan'
    PUSH_TRUSTED_CONTAINER_IMAGE = 'push-trusted-container-image'
    CREATE_DEPLOYMENT_ENVIRONMENT = 'create-deployment-environment'
    DEPLOY = 'deploy'
    UAT = 'uat'
    RUNTIME_VULNERABILITY_SCAN = 'runtime-vulnerability-scan'
    CANARY_TEST = 'canary-test'
    PUBLISH_WROKFLOW_RESULTS = 'publish-workflow-results'


class StepImplementer(ABC):  # pylint: disable=too-few-public-methods
    """
    Abstract representation of a TSSC step implementer.

    Parameters
    ----------
    config : dict
        Configuration specific to the StepImplementer
    results_dir_path : str
        Path to the file to write the results of the step to
    config_defaults : dict
        Defaults for any items not given in the config
    """

    __TSSC_RESULTS_KEY = 'tssc-results'
    __TITLE_LENGTH = 80

    def __init__(self, config, results_dir_path, results_file_name, config_defaults=None):
        if not config_defaults:
            config_defaults = {}
        step_config = {**config_defaults, **config}
        self.step_config = step_config
        self.results_dir_path = results_dir_path
        self.results_file_name = results_file_name
        self.__results_file_path = None
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
        self._validate_step_config(val)
        self.__step_config = val

    @classmethod
    @abstractmethod
    def step_name(cls):
        """
        Getter for the TSSC Step name implemented by this step.

        Returns
        -------
        str
            TSSC step name implemented by this step.
        """

    @abstractmethod
    def _run_step(self, runtime_step_config):
        """
        Runs the TSSC step implemented by this StepImplementer.

        Parameters
        ----------
        runtime_step_config : dict
            Combination of the step configuration as well as overrides
            and additional configuration passed in via runtime.

        Returns
        -------
        dict
            Results of running this step.
        """

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step configuration validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.

        Raises
        ------
        TSSCException
            If existing step results file has invalid YAML.
        """

    @classmethod
    def __print_section_title(cls, title):
        """
        Utility function for pretty printing section title.

        Parameters
        ----------
        title : str
            Section title to print
        """
        print()
        print()
        print(tabulate(
            [[]],
            [title.center(StepImplementer.__TITLE_LENGTH)],
            tablefmt="pretty"
        ))

    @classmethod
    def __print_data(cls, title, data):
        """
        Utility function for pretty printing data.

        Parameters
        ----------
        title : str
            Title of the data to print.
        data
            Data to print
        """
        printer = pprint.PrettyPrinter()
        print(tabulate(
            [[printer.pformat(data)]],
            [title.ljust(StepImplementer.__TITLE_LENGTH)],
            tablefmt="pretty",
            colalign=("left",)
        ))

    def run_step(self, **kwargs):
        """
        Wrapper for running the implemented step.

        Parameters
        ----------
        kwargs : dict
            Arbitrary arguments passed in via runtime to merge with the step_config
            to use when running the step.
        """

        StepImplementer.__print_section_title("TSSC Step Start - {}".format(self.step_name()))
        runtime_step_config = {**self.step_config, **kwargs}

        StepImplementer.__print_data('Static Step Configuration', self.step_config)
        StepImplementer.__print_data('Dynamic Step Configuration', kwargs)
        StepImplementer.__print_data('Runtime Step Configuration', runtime_step_config)

        results = self._run_step(runtime_step_config)
        self.write_results(results)

        StepImplementer.__print_section_title("TSSC Step Results - {}".format(self.step_name()))
        StepImplementer.__print_data('Results File Path', self.results_file_path)
        StepImplementer.__print_data('Step Results', results)

        StepImplementer.__print_section_title("TSSC Step End - {}".format(self.step_name()))

    def write_results(self, results):
        """
        Write the given results to the run's results file.

        Parameters
        ----------
        results : dict
            Results to write to the run's specific results file that is set as part of the factory

        Raises
        ------
        TSSCException
            Existing results file has invalid yaml or existing results file does not have expected
            element.
        """
        #If you are looking at this code you are going to need this:
        # https://treyhunner.com/2018/10/asterisks-in-python-what-they-are-and-how-to-use-them/
        if results is not None:
            current_results = self.current_results()
            if current_results:
                if current_results[StepImplementer.__TSSC_RESULTS_KEY].get(self.step_name()):
                    updated_step_results = {
                        StepImplementer.__TSSC_RESULTS_KEY: {
                            **current_results[StepImplementer.__TSSC_RESULTS_KEY],
                            self.step_name(): {
                                **current_results \
                                  [StepImplementer.__TSSC_RESULTS_KEY] \
                                  [self.step_name()], \
                                  **results
                            }
                        }
                    }
                else:
                    updated_step_results = {
                        StepImplementer.__TSSC_RESULTS_KEY: {
                            **current_results[StepImplementer.__TSSC_RESULTS_KEY],
                            self.step_name(): {
                                **results
                            }
                        }
                    }
            else:
                updated_step_results = {
                    StepImplementer.__TSSC_RESULTS_KEY: {
                        self.step_name(): {
                            **results
                        }
                    }
                }
            step_results_file_path = self.results_file_path
            with open(step_results_file_path, 'w') as step_results_file:
                yaml.dump(updated_step_results, step_results_file)

    def current_results(self):
        """
        Get the results of the TSSC so far from other step implementers that have already been run
        for this step and other previous steps.

        Returns
        -------
        dict
            The results of the TSSC so far from other step implementers that have already been run
            for this step and other previous steps.

        Raises
        ------
        TSSCException
            Existing results file has invalid yaml or existing results file does not have expected
            element.
        """
        if not os.path.exists(self.results_dir_path):
            os.makedirs(self.results_dir_path)

        step_results_file_path = self.results_file_path

        current_results = None
        if os.path.exists(step_results_file_path):
            with open(step_results_file_path, 'r') as step_results_file:
                try:
                    current_results = yaml.safe_load(step_results_file.read())
                except (yaml.scanner.ScannerError, yaml.parser.ParserError, ValueError) as err:
                    raise TSSCException(
                        'Existing results file'
                        +' (' + step_results_file_path + ')'
                        +' has invalid yaml: ' + str(err)
                    )

            if current_results:
                if StepImplementer.__TSSC_RESULTS_KEY not in current_results:
                    raise TSSCException(
                        'Existing results file'
                        +' (' + step_results_file_path + ')'
                        +' does not have expected top level element'
                        +' (' + StepImplementer.__TSSC_RESULTS_KEY + '): '
                        + str(current_results)
                    )
        else:
            current_results = {
                StepImplementer.__TSSC_RESULTS_KEY: {
                    self.step_name(): {}
                }
            }

        return current_results

    def get_step_results(self, step_name):
        """
        Get the results of a specific step.

        Parameters
        ----------
        step_name : str
            TSSC step name to get the results for

        Returns
        -------
        dict
            The results of a specific step. None if results DNE
        """
        return self.current_results()[StepImplementer.__TSSC_RESULTS_KEY].get(step_name)

    def current_step_results(self):
        """
        Get the results of this step so far from other step implementers that have already been run.

        Returns
        -------
        dict
            The results of this step so far from other step implementers that have already been run

        Raises
        ------
        TSSCException
            Existing results file has invalid yaml or existing results file does not have expected
            element.
        """
        return self.get_step_results(self.step_name())
        #return self.current_results()[StepImplementer.__TSSC_RESULTS_KEY][self.step_name()]

    @property
    def results_file_path(self):
        """
        Get the OS path to the results file for this step.

        Returns
        -------
        str
            OS path to the results file for this step.
        """
        if not self.__results_file_path:
            self.__results_file_path = os.path.join(self.results_dir_path, self.results_file_name)

        return self.__results_file_path
