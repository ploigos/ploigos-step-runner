"""Abstract class and helper constants for StepImplementer.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key       | Required? | Default | Description
------------------------|-----------|---------|-----------
`additional-artifacts`  | No        | `[]`    | List of additional artifacts, or list of dicts \
                                                of additional artifacts to add as artifacts on the \
                                                step step result (pass or fail). \
<br/><b>EX 1</b>: <br/>\
<pre>additional-artifacts: <br/>\
- randomValue1 <br/>\
- /path/to/something/important_dir <br/>\
- /path/to/cool/file.xml</pre> \
<br/><b>EX 1</b>: <br/>\
<pre>additional-artifacts: <br/>\
- name: mock-value <br/>\
  value: randomValue1 <br/>\
- name: mock-dir <br/>\
  value: /path/to/something/important_dir <br/>\
- name: mock-file <br/>\
  value: /path/to/cool/file.xml</pre>
"""# pylint: disable=line-too-long
import json
import os
import pprint
import sys
import textwrap
from abc import ABC, abstractmethod
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner import StepResult
from ploigos_step_runner.utils.io import TextIOIndenter


class DefaultSteps:  # pylint: disable=too-few-public-methods
    """Convenience constants for the default steps used in the default workflow definition.
    """
    GENERATE_METADATA = 'generate-metadata'
    TAG_SOURCE = 'tag-source'
    STATIC_CODE_ANALYSIS = 'static-code-analysis'
    PACKAGE = 'package'
    UNIT_TEST = 'unit-test'
    PUSH_ARTIFACTS = 'push-artifacts'
    CREATE_CONTAINER_IMAGE = 'create-container-image'
    PUSH_CONTAINER_IMAGE = 'push-container-image'
    SIGN_CONTAINER_IMAGE = 'sign-container-image'
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
    """Abstract representation of a step implementer.

    Parameters
    ----------
    workflow_result : WorkflowResult
        The WorkflowResult to add StepResult to when running this StepImplementer.
    parent_work_dir_path : str
        Path to the directory to write step working files to
    step_environment_config : dict, optional
        Step configuration specific to the current environment.
    config : SubStepConfig
        Configuration for this step.
    environment : str
        Environment name to execute this step against

    Attributes
    __config : SubStepConfig
    __environment : str
    """

    __TITLE_LENGTH = 80
    __INDENT_SIZE   = 4

    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None
    ):
        self.__parent_work_dir_path = parent_work_dir_path

        self.__config = config
        self.__environment = environment

        self.__workflow_result = workflow_result

        super().__init__()

    @property
    def config(self):
        """
        Returns
        -------
        SubStepConfig
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

    @property
    def work_dir_path(self):
        """Get the OS path to the working folder for this step.
        If the folder does not exist, create it.

        Returns
        -------
        str
            OS path to the working folder plus step name.
        """
        work_dir_path_step = os.path.join(self.__parent_work_dir_path, self.step_name)
        if self.environment:
            work_dir_path_step = os.path.join(work_dir_path_step, self.environment)
        os.makedirs(work_dir_path_step, exist_ok=True)
        return work_dir_path_step


    @property
    def step_name(self):
        """
        Getter for the step name implemented by this step.
        Returns
        -------
        str
            Step name implemented by this step.
        """
        return self.config.step_name

    @property
    def sub_step_name(self):
        """
        Getter for the sub step name implemented by this step.
        Returns
        -------
        str
            Sub step name.
        """
        return self.config.sub_step_name

    @property
    def sub_step_implementer_name(self):
        """
        Getter for the sub step implementer name implemented by this step.
        Returns
        -------
        str
            Sub step implementer name.
        """
        return self.config.sub_step_implementer_name

    @property
    def workflow_result(self):
        """
        Returns
        -------
        WorkflowResult
            Object containing a list of dictionary of step results
            from previous steps.
        """
        return self.__workflow_result

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
    def _required_config_or_result_keys():
        """Getter for step configuration or previous step result artifacts that are required before
        running this step.

        See Also
        --------
        _validate_required_config_or_previous_step_result_artifact_keys

        Returns
        -------
        array_list
            Array of configuration keys or previous step result artifacts
            that are required before running the step.
        """

    @abstractmethod
    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values.
        """
        invalid_required_keys = []
        for required_key in self._required_config_or_result_keys():
            required_value = self.get_value(required_key)

            if required_value is None:
                invalid_required_keys.append(required_key)

        assert (not invalid_required_keys), \
            'Missing required step configuration or previous step result artifact keys: ' + \
            f'{invalid_required_keys}'

    def run_step(self):
        """Wrapper for running the implemented step.

        Returns
        -------
        StepResult
            Results of running this step.
        """

        StepImplementer.__print_section_title(
            f"Step Start - {self.step_name} ({self.sub_step_name})"
        )

        # print information about the configuration
        StepImplementer.__print_section_title(
            f"Configuration - {self.step_name} ({self.sub_step_name})",
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

        step_result = None
        try:
            # validate the runtime step configuration
            self._validate_required_config_or_previous_step_result_artifact_keys()

            # run the step
            StepImplementer.__print_section_title(
                f"Standard Out - {self.step_name} ({self.sub_step_name})",
                div_char="-",
                indent=1
            )
            indented_stdout = TextIOIndenter(parent_stream=sys.stdout, indent_level=2)
            indented_stderr = TextIOIndenter(parent_stream=sys.stderr, indent_level=2)
            with redirect_stdout(indented_stdout), redirect_stderr(indented_stderr):
                step_result = self._run_step()
                sys.stdout.flush()
                sys.stderr.flush()

            # add any additional artifacts
            self.__add_additional_artifacts_to_step_result(step_result=step_result)
        except AssertionError as invalid_error:
            step_result = StepResult.from_step_implementer(self)
            step_result.success = False
            step_result.message = str(invalid_error)

        # print the step run results
        StepImplementer.__print_section_title(
            f"Results - {self.step_name} ({self.sub_step_name})",
            div_char="-",
            indent=1
        )
        StepImplementer.__print_data('Environment', step_result.environment)
        StepImplementer.__print_data('Step', step_result.step_name)
        StepImplementer.__print_data('Sub Step', step_result.sub_step_name)
        StepImplementer.__print_data('Sub Step Implementer', step_result.sub_step_implementer_name)
        StepImplementer.__print_data('Success', step_result.success)
        StepImplementer.__print_data('Message', step_result.message)
        StepImplementer.__print_data('Artifacts', step_result.artifacts_dicts)
        StepImplementer.__print_data('Evidence', step_result.evidence_dicts)

        StepImplementer.__print_section_title(f'Step End - {self.step_name} ({self.sub_step_name})')
        return step_result

    def get_value(self, key):
        """Get the value for a given key, either from given configuration or from the result
        of any previous step.

        Parameters
        ----------
        key : str, array
            Key to get the configuration value or result value for.
            If array will get configuration value or result value for first key in list with a
            value.

        Returns
        -------
        str, int, dict, list, or bool or None
            Configuration value, or if not set, result value from any previous step for the given
            key. Or None if not found.
        """

        if isinstance(key, list):
            keys = key
        else:
            keys = [key]

        for k in keys:
            # first try to get config value
            config_value = self.get_config_value(k)
            if config_value is not None:
                return config_value

            # if not found config value try to get result value specific to current environment
            if self.environment:
                result_value = self.get_result_value(
                    artifact_name=k,
                    environment=self.environment
                )
                if result_value is not None:
                    return result_value

            # last try getting result value from no specific environment
            result_value = self.get_result_value(
                artifact_name=k
            )

            if result_value:
                break

        return result_value

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
        SubStepConfig.get_config_value
        get_copy_of_runtime_step_config

        Parameters
        ----------
        key : str
            Key to get the configuration value for.

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
        SubStepConfig.get_copy_of_runtime_step_config
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
        """Determines if step has values for any of the given keys.

        Parameters
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
            if match_any and self.get_value(key) is not None:
                result = True
                break

            if not match_any and self.get_value(key) is None:
                result = False
                break

        return result

    def get_result_value(
        self,
        artifact_name,
        step_name=None,
        sub_step_name=None,
        environment=None
    ):
        """Get the value for the named artifact from a previous step result.

        If step_name is provided,
            search for artifact_name in step_name only
        If step_name and sub_step_name is provided,
            search for artifact_name in step_name/sub_step only
        Otherwise,
             search for the FIRST occurrence of the artifact_name

        EG:  Artifacts are a dictionary; return the contents of the value key.
          In this example, 'foo' is the artifact name, return 'bar'
          'foo' : {'description': '', 'value': 'bar'}

        Parameters
        ----------
        artifact_name : str
           Key name of the dictionary.

        Returns
        -------
        str
           Contents of the value for the specified result artifact_name.
        """
        return (
            self.workflow_result.get_artifact_value(
                artifact=artifact_name,
                step_name=step_name,
                sub_step_name=sub_step_name,
                environment=environment
            )
        )

    def create_working_dir_sub_dir(self, sub_dir_relative_path=""):
        """Create a folder under the working/stepname folder.

        Returns
        -------
        str
            Path to created working sub directory.
        """
        file_path = os.path.join(self.work_dir_path, sub_dir_relative_path)
        os.makedirs(file_path, exist_ok=True)
        return file_path

    def write_working_file(self, filename, contents=None):
        """Write content or touch filename in working directory for this step.

        Parameters
        ----------
        filename : str
            File name to create
        contents : str, optional
            Contents to write to the file

        Returns
        -------
        str
            Return a string to the file path
        """
        # eg: step-runner-working/step_name
        file_path = os.path.join(self.work_dir_path, filename)

        # sub-directories might be passed filename, eg: foo/filename
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if contents is None:
            Path(file_path).touch()
        else:
            with open(file_path, 'wb') as file:
                file.write(contents)
        return file_path

    def __add_additional_artifacts_to_step_result(self, step_result):
        """Adds user supplied additional artifacts to step result if given.

        Parameters
        ----------
        step_result : StepResult
            StepResult to add the additional artifacts to.
        """
        additional_artifacts = self.get_value('additional-artifacts')
        if isinstance(additional_artifacts, list):
            for additional_artifact in additional_artifacts:
                if isinstance(additional_artifact, dict):
                    step_result.add_artifact(
                        name=additional_artifact['name'],
                        value=additional_artifact['value']
                    )
                else:
                    step_result.add_artifact(
                        name=os.path.basename(additional_artifact),
                        value=additional_artifact
                    )

    @staticmethod
    def __print_section_title(title, div_char="=", indent=0):
        """Utility function for pretty printing section title.

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
        Indent levels are each are StepImplementer.__INDENT_SIZE spaces wide.

        Parameters
        ----------
        title : str
            Title of the data to print.
        data
            Data to print
        indent : int
            Amount to indent the title by and then the content by this +1
        """

        StepImplementer.__print_indented(
            text=title,
            indent=indent
        )

        # NOTE: do a json.dumps so that when printing dicts and arrays the {} and [] get put on
        #       their own lines which there is no way to do with PrettyPrinter.
        if isinstance(data, (dict, list)):
            formated_data = json.dumps(
                data,
                indent=StepImplementer.__INDENT_SIZE
            )
        elif isinstance(data, str):
            formated_data = data
        else:
            printer = pprint.PrettyPrinter()
            formated_data = printer.pformat(data)

        StepImplementer.__print_indented(
            text=formated_data,
            indent=indent + 1
        )
        print()

    @staticmethod
    def __print_indented(text, indent=0):
        """Prints the given text indented by a given indent level.

        Notes
        -----
        Indent levels are each are StepImplementer.__INDENT_SIZE spaces wide.

        Parameters
        ----------
        text : str
            Text to print indented.
        indent : indent
            amount to indent the given text by before printing.
        """
        print(textwrap.indent(
            text=text,
            prefix=" " * (StepImplementer.__INDENT_SIZE * indent)
        ))
