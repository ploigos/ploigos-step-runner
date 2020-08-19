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
    CREATE_DEPLOYMENT_ENVIRONMENT = 'create-deployment-environment'
    DEPLOY = 'deploy'
    UAT = 'uat'
    RUNTIME_VULNERABILITY_SCAN = 'runtime-vulnerability-scan'
    CANARY_TEST = 'canary-test'
    PUBLISH_WROKFLOW_RESULTS = 'publish-workflow-results'


class StepImplementer(ABC): # pylint: disable=too-many-instance-attributes
    """
    Abstract representation of a TSSC step implementer.

    Parameters
    ----------
    results_dir_path : str
        Path to the directory to write the results of the step to
    results_file_name : str
        Name of file to write the results of the step to
    work_dir_path : str
        Path to the directory to write step working files to
    step_environment_config : dict, optional
        Step configuration specific to the current environment.
    step_config : dict, optional
        Step configuration.
    global_config_defaults : dict, optional
        Global defaults.
    global_environment_config_defaults : dict, optional
        Global defaults specific to the current environment.
    """

    __TSSC_RESULTS_KEY = 'tssc-results'
    __TITLE_LENGTH = 80

    def __init__( # pylint: disable=too-many-arguments
            self,
            results_dir_path,
            results_file_name,
            work_dir_path,
            step_environment_config=None,
            step_config=None,
            global_config_defaults=None,
            global_environment_config_defaults=None):

        if step_environment_config is None:
            step_environment_config = {}
        if step_config is None:
            step_config = {}
        if global_config_defaults is None:
            global_config_defaults = {}
        if global_environment_config_defaults is None:
            global_environment_config_defaults = {}

        self.__results_dir_path = results_dir_path
        self.__results_file_name = results_file_name
        self.__work_dir_path = work_dir_path

        self.__step_environment_config = step_environment_config
        self.__step_config = step_config
        self.__global_config_defaults = global_config_defaults
        self.__global_environment_config_defaults = global_environment_config_defaults

        self.__results_file_path = None
        super().__init__()

    @property
    def step_environment_config(self):
        """
        Returns
        -------
        dict
            Step configuration specific to the current environment.
        """
        return self.__step_environment_config

    @property
    def step_config(self):
        """
        Returns
        -------
        dict
            Step configuration.
        """
        return self.__step_config

    @property
    def global_config_defaults(self):
        """
        Returns
        -------
        dict
            Global configuration defaults affecting this step.
        """
        return self.__global_config_defaults

    @property
    def global_environment_config_defaults(self):
        """
        Returns
        -------
        dict
            Global configuration defaults affecting this step specific to the current environment.
        """
        return self.__global_environment_config_defaults

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
            self.__results_file_path = os.path.join(
                self.__results_dir_path,
                self.__results_file_name)

        return self.__results_file_path

    @staticmethod
    @abstractmethod
    def step_name():
        """
        Getter for the TSSC Step name implemented by this step.

        Returns
        -------
        str
            TSSC step name implemented by this step.
        """

    @staticmethod
    @abstractmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

        Notes
        -----
        These are the lowest precedence configuration values.

        Returns
        -------
        dict
            Default values to use for step configuration values.
        """

    @staticmethod
    @abstractmethod
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.

        See Also
        --------
        _validate_runtime_step_config

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.
        """

    @abstractmethod
    def _run_step(self, runtime_step_config):
        """
        Runs the TSSC step implemented by this StepImplementer.

        Parameters
        ----------
        runtime_step_config : dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.

        Returns
        -------
        dict
            Results of running this step.
        """

    def _validate_runtime_step_config(self, runtime_step_config):
        """
        Validates the given `runtime_step_config` against the required step configuration keys.

        Parameters
        ----------
        runtime_step_config : dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.

        Raises
        ------
        AssertionError
            If the given `runtime_step_config` is not valid with a message as to why.
        """
        missing_required_config_keys = []
        for required_config_key in self.required_runtime_step_config_keys():
            if ((required_config_key not in runtime_step_config) or \
                    ((not runtime_step_config[required_config_key]) and  \
                    (not isinstance(runtime_step_config[required_config_key], bool)))):
                missing_required_config_keys.append(required_config_key)

        assert (not missing_required_config_keys), \
            "The runtime step configuration ({runtime_step_config}) is missing the required".format(
                runtime_step_config=runtime_step_config,) + \
            " configuration keys ({missing_required_config_keys})".format(
                missing_required_config_keys=missing_required_config_keys
            )

    def __create_runtime_step_config(self, step_config_runtime_overrides):
        """
        Creates the step configuration to use when the StepImplementer runs the step.

        From least precedence to highest precedence.

            1. StepImplementer implementation provided configuration defaults
               (self.step_implementer_config_defaults)
            2. Global Configuration Defaults (self.global_config_defaults)
            3. Global Environment Configuration Defaults (self.global_environment_config_defaults)
            4. Step Configuration ( self.step_config)
            5. Step Environment Configuration (self.step_environment_config)
            6. Step Configuration Runtime Overrides (step_config_runtime_overrides)

        Parameters
        ----------
        step_config_runtime_overrides : dict, optional
            Configuration for the step passed in at runtime when the step was invoked that will
            override step configuration coming from any other source.

        Returns
        -------
        dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.
        """
        return {
            **self.step_implementer_config_defaults(),
            **self.global_config_defaults,
            **self.global_environment_config_defaults,
            **self.step_config,
            **self.step_environment_config,
            **step_config_runtime_overrides
        }

    def run_step(self, step_config_runtime_overrides=None):
        """
        Wrapper for running the implemented step.

        Parameters
        ----------
        step_config_runtime_overrides : dict, optional
            Configuration for the step passed in at runtime when the step was invoked that will
            override step configuration coming from any other source.
        """

        step_config_runtime_overrides = {} if step_config_runtime_overrides is None \
                                            else step_config_runtime_overrides

        StepImplementer.__print_section_title("TSSC Step Start - {}".format(self.step_name()))

        # print information about the static step configuration
        StepImplementer.__print_data(
            "Step Implementer Configuration Defaults",
            self.step_implementer_config_defaults())
        StepImplementer.__print_data(
            "Global Configuration Defaults",
            self.global_config_defaults)
        StepImplementer.__print_data(
            "Global Environment Configuration Defaults",
            self.global_environment_config_defaults)
        StepImplementer.__print_data(
            "Step Configuration",
            self.step_config)
        StepImplementer.__print_data(
            "Step Environment Configuration",
            self.step_environment_config)
        StepImplementer.__print_data(
            "Step Configuration Runtime Overrides",
            step_config_runtime_overrides)

        # create the munged runtime step configuration and print
        runtime_step_config = self.__create_runtime_step_config(step_config_runtime_overrides)
        StepImplementer.__print_data(
            "Runtime Step Configuration",
            runtime_step_config)

        # validate the runtime step configuration, run the step, and save the results
        self._validate_runtime_step_config(runtime_step_config)
        results = self._run_step(runtime_step_config)
        self.write_results(results)

        # print the step run results
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
        if not os.path.exists(self.__results_dir_path):
            os.makedirs(self.__results_dir_path)

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

    def write_temp_file(self, filename, contents):
        """
        Write content to filename in working directory

        Returns
        -------
        str
            return a string to the absolute file path
        """
        if not os.path.exists(self.__work_dir_path):
            os.makedirs(self.__work_dir_path)
        step_path = os.path.join(self.__work_dir_path, self.step_name())
        if not os.path.exists(step_path):
            os.makedirs(step_path)

        #file_path = os.path.join(self.__work_dir_path, self.step_name(), filename)
        file_path = os.path.join(step_path, filename)
        with open(file_path, 'wb') as file:
            file.write(contents)
        return file_path

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
