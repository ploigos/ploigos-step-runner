"""
Abstract class and helper constants for StepImplementer.
"""

from abc import ABC, abstractmethod
from contextlib import redirect_stdout, redirect_stderr
import os
from pathlib import Path
import pprint
import textwrap
import sys
from tssc.config.config_value import ConfigValue
from tssc.utils.io import TextIOIndenter

from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult


class DefaultSteps:  # pylint: disable=too-few-public-methods
    """
    Convenience constants for the default steps used in the default TSSC workflow definition.
    """
    GENERATE_METADATA = 'generate-metadata'
    TAG_SOURCE = 'tag-source'
    STATIC_CODE_ANALYSIS = 'static-code-analysis'
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
    PUBLISH_WORKFLOW_RESULTS = 'publish-workflow-results'


class StepImplementer(ABC):  # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
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
    config : TSSCSubStepConfig
        Configuration for this step.
    environment : str
        Environment name to execute this step against

    Attributes
    __config : TSSCSubStepConfig
    __environment : str
    """

    __TSSC_RESULTS_KEY = 'tssc-results'
    __TITLE_LENGTH = 80

    def __init__(  # pylint: disable=too-many-arguments
            self,
            results_dir_path,
            results_file_name,
            work_dir_path,
            config,
            environment=None):

        self.__results_dir_path = results_dir_path
        self.__results_file_name = results_file_name
        self.__work_dir_path = work_dir_path

        self.__config = config
        self.__environment = environment

        self.__results_file_path = None

        # results_file_path example: /home/me/tssc-results/tssc-results.plkl
        self.results_file_path()

        # WORKFLOW
        # todo: Move this to the working folder (pkl will be in work folder)
        self.__workflowResults = WorkflowResult(self.__results_file_path)

        # STEP_RESULTS
        # todo: the step result will be in the constructor for workflow?  hmm.
        self.__step_result = StepResult(config.step_name, config.sub_step_name)

        super().__init__()

    @property
    def config(self):
        """
        Returns
        -------
        TSSCSubStepConfig
            Configuration for this step.
        """
        return self.__config

    @property
    def environment(self):
        """
        Returns
        -------
        str
            Environment name to execute this step against
        """
        return self.__environment

    @property
    def step_config(self):
        """
        Returns
        -------
        dict
            Step configuration.
        """
        return self.config.sub_step_config

    @property
    def step_config_overrides(self):
        """
        Returns
        -------
        dict
            Step configuration overrides.
        """
        return self.config.step_config_overrides

    @property
    def step_environment_config(self):
        """
        Returns
        -------
        dict
            Step configuration specific to the current environment.
        """
        return self.config.get_sub_step_env_config(self.environment)

    @property
    def global_config_defaults(self):
        """
        Returns
        -------
        dict
            Global configuration defaults affecting this step.
        """
        return self.config.global_defaults

    @property
    def global_environment_config_defaults(self):
        """
        Returns
        -------
        dict
            Global configuration defaults affecting this step specific to the current environment.
        """

        if self.environment is not None:
            defaults_for_env = self.config.get_global_environment_defaults(self.environment)
        else:
            defaults_for_env = {}

        return defaults_for_env

    def results_file_path(self):
        """
        Get the OS path to the results file for this step.

        Returns
        -------
        str
            OS path to the results file for this step.
        """
        # todo: is this the best place to create the folder?
        if not os.path.exists(self.__results_dir_path):
            os.makedirs(self.__results_dir_path)
        if not self.__results_file_path:
            self.__results_file_path = os.path.join(
                self.__results_dir_path,
                self.__results_file_name)

        return self.__results_file_path

    @property
    def step_name(self):
        """
        Getter for the TSSC Step name implemented by this step.
        Returns
        -------
        str
            TSSC step name implemented by this step.
        """
        return self.config.step_name

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
    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

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
                    ((not runtime_step_config[required_config_key]) and \
                     (not isinstance(runtime_step_config[required_config_key], bool)))):
                missing_required_config_keys.append(required_config_key)

        assert (not missing_required_config_keys), \
            "The runtime step configuration (" + \
            f"{ConfigValue.convert_leaves_to_values(runtime_step_config)}) is missing " + \
            f"the required configuration keys ({missing_required_config_keys})"

    def run_step(self):
        """
        Wrapper for running the implemented step.
        """

        StepImplementer.__print_section_title(f"Step Start - {self.step_name}")

        # print information about theconfiguration
        StepImplementer.__print_section_title(
            f"Configuration - {self.step_name}",
            div_char="-",
            indent=1
        )
        StepImplementer.__print_data(
            "Step Implementer Configuration Defaults",
            ConfigValue.convert_leaves_to_values(self.step_implementer_config_defaults())
        )
        StepImplementer.__print_data(
            "Global Configuration Defaults",
            ConfigValue.convert_leaves_to_values(self.global_config_defaults)
        )
        StepImplementer.__print_data(
            "Global Environment Configuration Defaults",
            ConfigValue.convert_leaves_to_values(self.global_environment_config_defaults)
        )
        StepImplementer.__print_data(
            "Step Configuration",
            ConfigValue.convert_leaves_to_values(self.step_config)
        )
        StepImplementer.__print_data(
            "Step Environment Configuration",
            ConfigValue.convert_leaves_to_values(self.step_environment_config)
        )
        StepImplementer.__print_data(
            "Step Configuration Runtime Overrides",
            ConfigValue.convert_leaves_to_values(self.step_config_overrides)
        )

        # create the munged runtime step configuration and print
        copy_of_runtime_step_config = self.get_copy_of_runtime_step_config()
        StepImplementer.__print_data(
            "Runtime Step Configuration",
            ConfigValue.convert_leaves_to_values(copy_of_runtime_step_config)
        )
        # add in the runtime-config

        # validate the runtime step configuration
        StepImplementer.__print_section_title(
            f"Standard Out - {self.step_name}",
            div_char="-",
            indent=1
        )
        self._validate_runtime_step_config(copy_of_runtime_step_config)

        # run the step and save the results
        indented_stdout = TextIOIndenter(
            parent_stream=sys.stdout,
            indent_level=2
        )
        indented_stderr = TextIOIndenter(
            parent_stream=sys.stderr,
            indent_level=2
        )
        with redirect_stdout(indented_stdout), redirect_stderr(indented_stderr):
            # peggy
            self._run_step()
            self._workflow_result_update()

        # print the step run results
        StepImplementer.__print_section_title(
            f"Results - {self.step_name}",
            div_char="-",
            indent=1
        )

        StepImplementer.__print_data('Results File Path', self.__results_file_path)

        StepImplementer.__print_data('Results', self.__step_result.get_step_result_json())

        StepImplementer.__print_section_title(f'Step End - {self.step_name}')

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
            Unexpected error
        """
        return self.__step_result.get_step_result()

    def get_config_value(self, key):
        """Convenience function for self.config.get_config_value.

        Get the configuration value for a given configuration key from the
        merged set of configuration sources.

        From least precedence to highest precedence.

            1. defaults
            2. Global Configuration Defaults (self.global_config_defaults)
            3. Global Environment Configuration Defaults (self.global_environment_config_defaults)
            4. Step Configuration ( self.step_config)
            5. Step Environment Configuration (self.step_environment_config)
            6. Step Configuration Runtime Overrides (step_config_runtime_overrides)

        Also See
        --------
        TSSCSubStepConfig.get_config_value
        get_copy_of_runtime_step_config

        Parameters
        ----------
        key : str
            Key to get the configuration value for.
        environment : str, optional
            Environment to include the configuration for if running in the context of
            a specific environment.
        defaults : dict, optional
            If no value for the given configuration key found in any of the configuration
            sources then use these defaults as last resort.

        Returns
        -------
        str, int, dict, list, or bool or None
            Value of the given configuration key or None if one does not exist
            for this sub step in the given context with the given defaults.
        """
        return self.config.get_config_value(
            key,
            self.environment,
            self.step_implementer_config_defaults())

    def get_copy_of_runtime_step_config(self):
        """Convenience function for self.config.get_copy_of_runtime_step_config

        See Also
        --------
        TSSCSubStepConfig.get_copy_of_runtime_step_config
        get_config_value

        Returns
        -------
        dict
            A deep copy of the merged runtime step configuration
        """
        return self.config.get_copy_of_runtime_step_config(
            self.environment,
            self.step_implementer_config_defaults())

    def has_config_value(self, keys, match_any=False):
        """Determins if step has values for any of the given keys.

        Parmaeters
        ----------
        keys : str or list of str
            Keys to check to see if there are values for any or all of these key(s).
        match_any : bool
            If True only one key has to have a value.
            If False then all given keys have to have values.

        Returns
        -------
        bool
            True if any/all (depending on value of match_any) keys have a value.
            False otherwise.
        """
        if isinstance(keys, str):
            keys = [keys]

        result = not match_any
        for key in keys:
            if match_any and self.get_config_value(key) is not None:
                result = True
                break

            if not match_any and self.get_config_value(key) is None:
                result = False
                break

        return result

    def get_step_results(self, step_name):
        """Get the results of a specific step.

        Parameters
        ----------
        step_name : str
            TSSC step name to get the results for

        Returns
        -------
        dict
            The results of a specific step. None if results DNE
        """
        return self.__workflow_results.get_step_result(step_name)


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
        # todo: how to manage include previous implementers?
        return self.__step_result.get_step_result()

    # todo: get_value or get_config_or_result_value

    def create_working_folder(self):
        """
        If it does not exist, create working folder

        Returns
        -------
        str
            return a string to the absolute path
        """
        if not os.path.exists(self.__work_dir_path):
            os.makedirs(self.__work_dir_path)
        step_path = os.path.join(self.__work_dir_path, self.step_name)
        if not os.path.exists(step_path):
            os.makedirs(step_path)

        return os.path.abspath(step_path)

    def write_working_file(self, filename, contents=None):
        """
        Write content to filename in working directory

        Parameters
        ----------
        filename : str
            Relative path (to working dir), including file name, to create.
        contents : str, optional
            Contents to write to the file

        Returns
        -------
        str
            return a string to the absolute file path
        """
        working_folder = self.create_working_folder()

        file_path = os.path.join(working_folder, filename)

        # if given contents write it to file
        # else just touch empty file
        #
        # NOTE: in either case auto create any missing parent directories
        if contents is not None:
            with open(file_path, 'wb') as file:
                file.write(contents)
        else:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            Path(file_path).touch()

        return file_path

    @staticmethod
    def __print_section_title(title, div_char="=", indent=0):
        """
        Utility function for pretty printing section title.

        Parameters
        ----------
        title : str
            Section title to print
        """
        print()
        print()
        StepImplementer.__print_indented(
            text=div_char * StepImplementer.__TITLE_LENGTH,
            indent=indent
        )
        StepImplementer.__print_indented(
            text=title.center(StepImplementer.__TITLE_LENGTH),
            indent=indent
        )
        StepImplementer.__print_indented(
            text=div_char * StepImplementer.__TITLE_LENGTH,
            indent=indent
        )

    @staticmethod
    def __print_data(title, data, indent=2):
        """Utility function for pretty printing data.

        Notes
        -----
        Indent levels are each are 4 spaces wide.

        Parameters
        ----------
        title : str
            Title of the data to print.
        data
            Data to print
        indent : int
            Amount to indent the title by and then the content by this +1
        """
        printer = pprint.PrettyPrinter()
        StepImplementer.__print_indented(
            text=title,
            indent=indent
        )
        StepImplementer.__print_indented(
            text=printer.pformat(data),
            indent=indent + 1
        )
        print()

    @staticmethod
    def __print_indented(text, indent=0):
        """Prints the given text indented by a given indent level.

        Notes
        -----
        Indent levels are each are 4 spaces wide.

        Parameters
        ----------
        text : str
            Text to print indented.
        indent : indent
            amount to indent the given text by before printing.
        """
        print(textwrap.indent(
            text=text,
            prefix=" " * (4 * indent)
        ))

    @property
    def step_result(self):
        """
        :return: dict
        """
        return self.__step_result

    @property
    def workflow(self):
        """
        :return: dict
        """
        return self.__workflow_results

    # todo: how to organize this better?
    def _workflow_result_update(self):
        """
        this is where we actually write the file to disk
        :return: dict
        """
        # peggy
        # todo:  move to the constructor of the workflow_result
        self.__workflow_results.add_step_result(self.__step_result)

        self.__workflow_results.dump()
        # todo: dump the pkl to tssc-working
        # todo: dump the yml to tssc-results
