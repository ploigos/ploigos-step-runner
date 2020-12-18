"""Representation of configuration for workflow.
"""

import copy
import glob
import os.path

from ploigos_step_runner.decryption_utils import DecryptionUtils
from ploigos_step_runner.config.step_config import StepConfig
from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.utils.file import parse_yaml_or_json_file
from ploigos_step_runner.utils.dict import deep_merge

class Config:
    """Representation of configuration for Ploigos workflow.

    Parameters
    ----------
    config : dict, list, str (file or directory), optional
        A dictionary that is a valid configuration,
        or a string that is a path to a YAML or JSON file that is
        a valid configuration,
        or a string that is a path to a directory containing one or more
        files that are valid YAML or JSON files that are valid
        configurations,
        or a list of any of the former.

    Attributes
    ----------
    __global_defaults : dict
    __global_environment_defaults : dict
    __step_configs : dict of str (step names) to StepConfig

    Raises
    ------
    ValueError
        If given config is not of expected type.
    AssertionError
        If given config contains any invalid configurations.
    """
    CONFIG_KEY = 'step-runner-config'
    CONFIG_KEY_GLOBAL_DEFAULTS = 'global-defaults'
    CONFIG_KEY_GLOBAL_ENVIRONMENT_DEFAULTS = 'global-environment-defaults'
    CONFIG_KEY_ENVIRONMENT_NAME = 'environment-name'
    CONFIG_KEY_STEP_IMPLEMENTER = 'implementer'
    CONFIG_KEY_SUB_STEP_NAME = 'name'
    CONFIG_KEY_SUB_STEP_CONFIG = 'config'
    CONFIG_KEY_SUB_STEP_ENVIRONMENT_CONFIG = 'environment-config'
    CONFIG_KEY_DECRYPTORS = 'config-decryptors'
    CONFIG_KEY_DECRYPTOR_IMPLEMENTER = 'implementer'
    CONFIG_KEY_DECRYPTOR_CONFIG = 'config'

    def __init__(self, config=None):
        self.__global_defaults = {}
        self.__global_environment_defaults = {}
        self.__step_configs = {}

        if config is not None:
            self.add_config(config)

    @property
    def global_defaults(self):
        """Get a deep copy of the global defaults.

        Returns
        -------
        dict
            Deep copy of the global defaults.
        """
        return copy.deepcopy(self.__global_defaults)

    @property
    def global_environment_defaults(self):
        """Deep copy of all global environment defaults for all environments.

        Returns
        -------
        dict
            deep copy of all global environment defaults.
        """
        return copy.deepcopy(self.__global_environment_defaults)

    @property
    def step_configs(self):
        """
        Returns
        -------
        list of StepConfig
        """
        return self.__step_configs

    def get_global_environment_defaults_for_environment(self, env):
        """Get a deep copy of all of the global environment defaults or for a given an environment.

        Parameters
        ----------
        env : str
            The global environment defaults for the given environment.
            If given environment name does not exist in environment defaults then empty dict.

        Returns
        -------
        dict
            Deep copy of the global environment defaults for the given environment
            or empty dict if no environment given or environment does not exist in the defaults
        """
        if env is not None:
            if env in self.__global_environment_defaults:
                global_environment_defaults = copy.deepcopy(self.__global_environment_defaults[env])
            else:
                global_environment_defaults = {}
        else:
            global_environment_defaults = {}

        return global_environment_defaults

    def get_step_config(self, step_name):
        """Get the step config for a given step name.

        Parameters
        ----------
        step_name : str
            Name of the step to get the step configuration for.

        Returns
        -------
        StepConfig
            Step configuration for the given step name or None if does not exist
        """
        if step_name in self.step_configs:
            step_config = self.step_configs[step_name]
        else:
            step_config = None

        return step_config

    def get_sub_step_configs(self, step_name):
        """Gets lit of configured sub step configurations for a step with the given name.

        Parameters
        ----------
        step_name : str
            Name of step to get configured sub steps for.

        Returns
        -------
        list of SubStepConfig
            List of configured sub step configurations for the step with the given name.
        """

        if step_name in self.step_configs:
            sub_step_configs = self.step_configs[step_name].sub_steps
        else:
            sub_step_configs = []

        return sub_step_configs

    def add_config(self, config):
        """Parses, validates, and adds a given config to this Config.

        Parameters
        ----------
        config : dict, list, str (file or directory)
            A dictionary that is a valid configuration,
            or aa string that is a path to a YAML or JSON file that is
            a valid configuration,
            or a string that is a path to a directory containing one or more
            files that are valid YAML or JSON files that are valid
            configurations,
            or a list of any of the former.

        Raises
        ------
        ValueError
            If given config is not of expected type.
        AssertionError
            If given config contains any invalid configurations.
        """
        if isinstance(config, dict):
            # add the config
            self.__add_config_dict(config)
        elif isinstance(config, list):
            # for each item in the list, treat it as a config to add
            for _config in config:
                self.add_config(_config)
        elif isinstance(config, str):
            if os.path.isfile(config):
                self.__add_config_file(config)
            elif os.path.isdir(config):
                # for each recursively found file in the directory add the config file
                config_dir_files = glob.glob(config + '/**', recursive=True)
                found_nested_file = False
                for config_dir_file in config_dir_files:
                    if os.path.isfile(config_dir_file):
                        found_nested_file = True
                        self.__add_config_file(config_dir_file)

                if not found_nested_file:
                    raise ValueError(
                        f"Given config string ({config}) is a directory" +
                        " with no recursive children files."
                    )
            else:
                raise ValueError(
                    f"Given config string ({config}) is not a valid path."
                )
        else:
            raise ValueError(
                f"Given config ({config}) is unexpected type ({type(config)}) " +
                "not a dictionary, string, or list of former."
            )

    def set_step_config_overrides(self, step_name, step_config_overrides):
        """Sets configuration overrides for all sub steps of a given step.

        Notes
        -----
        If step configuration overrides are already set for the given step then
        the existing overides will be replaced with the newly given step configuration
        overrides.

        Parameters
        ----------
        step_name : str
            Name of step to add configuration overrides for all sub steps for.
        step_config_overrides : dict
            Overrides for all sub steps for the step with the given name.
        """
        if step_name not in self.step_configs:
            self.step_configs[step_name] = StepConfig(self, step_name)

        self.step_configs[step_name].step_config_overrides = step_config_overrides

    def __add_config_file(self, config_file):
        """Adds a JSON or YAML file as config to this Config.

        Parameters
        ----------
        config_file : str (file path)
            A string that is a path to an existing YAML or JSON file to
            parse and validate as a configuration to add to this Config.

        Raises
        ------
        ValueError
            If can not parse given file as YAML or JSON
        AssertionError
            If dictionary parsed from given YAML or JSON file is not a valid config.
        """
        # parse the configuration file
        try:
            parsed_config_file = parse_yaml_or_json_file(config_file)
        except ValueError as error:
            raise ValueError(
                f"Error parsing config file ({config_file}) as json or yaml"
            ) from error

        # add the config parsed from file
        try:
            self.__add_config_dict(parsed_config_file, config_file)
        except AssertionError as error:
            raise AssertionError(
                f"Failed to add parsed configuration file ({config_file}): {error}"
            ) from error

    def __add_config_dict(self, config_dict, source_file_path=None): # pylint: disable=too-many-locals, too-many-branches
        """Add a configuration dictionary to the list of configuration dictionaries.

        Parameters
        ----------
        config_dict : dict
            A dictionary to validate as a configuration and to add to this Config.
        source_file_path : str, optional
            File path to the file from which the given config_dict came from.

        Raises
        ------
        AssertionError
            If the given config_dict is not a valid configuration dictionary.
            If attempt to update an existing sub step and new and existing sub step implementers
                do not match.
            If sub step does not define a step implementer.
        ValueError
            If duplicative leaf keys when merging global defaults
            If duplicative leaf keys when merging global env defaults
            If step config is not of type dict or list
            If new sub step configuration has duplicative leaf keys to
                existing sub step configuration.
            If new sub step environment configuration has duplicative leaf keys to
                existing sub step environment configuration.
        """

        assert Config.CONFIG_KEY in config_dict, \
            "Failed to add invalid config. " + \
            f"Missing expected top level key ({Config.CONFIG_KEY}): " + \
            f"{config_dict}"

        # if file path given use that as the source when creating ConfigValue objects
        # else use a copy of the given configuration dictionary
        if source_file_path is not None:
            parent_source = source_file_path
        else:
            parent_source = copy.deepcopy(config_dict)

        # convert all the leaves of the configuration dictionary under
        # the Config.CONFIG_KEY to ConfigValue objects
        config_values = ConfigValue.convert_leaves_to_config_values(
            values=copy.deepcopy(config_dict[Config.CONFIG_KEY]),
            parent_source=parent_source,
            path_parts=[Config.CONFIG_KEY]
        )

        for key, value in config_values.items():
            # if global default key
            # else if global env defaults key
            # else assume step config
            if key == Config.CONFIG_KEY_GLOBAL_DEFAULTS:
                try:
                    self.__global_defaults = deep_merge(
                        copy.deepcopy(self.__global_defaults),
                        copy.deepcopy(value)
                    )
                except ValueError as error:
                    raise ValueError(
                        f"Error merging global defaults: {error}"
                    ) from error
            elif key == Config.CONFIG_KEY_GLOBAL_ENVIRONMENT_DEFAULTS:
                for env, env_config in value.items():
                    if env not in self.__global_environment_defaults:
                        self.__global_environment_defaults[env] = {
                            Config.CONFIG_KEY_ENVIRONMENT_NAME: env
                        }

                    try:
                        self.__global_environment_defaults[env] = deep_merge(
                            copy.deepcopy(self.__global_environment_defaults[env]),
                            copy.deepcopy(env_config)
                        )
                    except ValueError as error:
                        raise ValueError(
                            f"Error merging global environment ({env}) defaults: {error}"
                        ) from error
            elif key == Config.CONFIG_KEY_DECRYPTORS:
                config_decryptor_definitions = ConfigValue.convert_leaves_to_values(value)
                Config.parse_and_register_decryptors_definitions(config_decryptor_definitions)
            else:
                step_name = key
                step_config = value

                # if step_config is dict then assume step with single sub step
                if isinstance(step_config, dict):
                    sub_steps = [step_config]
                elif isinstance(step_config, list):
                    sub_steps = step_config
                else:
                    raise ValueError(
                        f"Expected step ({step_name}) to have have step config ({step_config})" +
                        f" of type dict or list but got: {type(step_config)}"
                    )

                for sub_step in sub_steps:
                    assert Config.CONFIG_KEY_STEP_IMPLEMENTER in sub_step, \
                        f"Step ({step_name}) defines a single sub step with values " + \
                        f"({sub_step}) but is missing value for key: " + \
                        f"{Config.CONFIG_KEY_STEP_IMPLEMENTER}"

                    sub_step_implementer_name = \
                        sub_step[Config.CONFIG_KEY_STEP_IMPLEMENTER].value

                    # if sub step name given
                    # else if no sub step name given use step implementer as sub step name
                    if Config.CONFIG_KEY_SUB_STEP_NAME in sub_step:
                        sub_step_name = sub_step[Config.CONFIG_KEY_SUB_STEP_NAME].value
                    else:
                        sub_step_name = sub_step_implementer_name

                    if Config.CONFIG_KEY_SUB_STEP_CONFIG in sub_step:
                        sub_step_config_dict = copy.deepcopy(
                            sub_step[Config.CONFIG_KEY_SUB_STEP_CONFIG])
                    else:
                        sub_step_config_dict = {}

                    if Config.CONFIG_KEY_SUB_STEP_ENVIRONMENT_CONFIG in sub_step:
                        sub_step_env_config = copy.deepcopy(
                            sub_step[Config.CONFIG_KEY_SUB_STEP_ENVIRONMENT_CONFIG])
                    else:
                        sub_step_env_config = {}

                    self.add_or_update_step_config(
                        step_name=step_name,
                        sub_step_name=sub_step_name,
                        sub_step_implementer_name=sub_step_implementer_name,
                        sub_step_config_dict=sub_step_config_dict,
                        sub_step_env_config=sub_step_env_config
                    )

    @staticmethod
    def parse_and_register_decryptors_definitions(decryptors_definitions):
        """Parse decryptor definitions from a list and then register them with the DecryptionUtils.

        Parameters
        ----------
        decryptors_definitions : list of dicts
            List of decryptor definitions. Each element should be a dict with at least an
            'implementer' key with a string value and optionally a 'config' key with a dict value.

        Raises
        ------
        AssertionError
            If decryptors_definitions is not a list.
            If a decryptor definition does not have a
                Config.CONFIG_KEY_DECRYPTOR_IMPLEMENTER key.
        """
        assert isinstance(decryptors_definitions, list), \
            f"Decryptors configuration ({decryptors_definitions}) must be of type " + \
            f"(list) got: {type(decryptors_definitions)}"

        for decryptor_definition in decryptors_definitions:
            assert Config.CONFIG_KEY_DECRYPTOR_IMPLEMENTER in decryptor_definition, \
                "Decryptor configuration is missing key " + \
                f"({Config.CONFIG_KEY_DECRYPTOR_IMPLEMENTER}): {decryptor_definition}"

            decryptor_implementer_name = \
                decryptor_definition[Config.CONFIG_KEY_DECRYPTOR_IMPLEMENTER]

            if Config.CONFIG_KEY_DECRYPTOR_CONFIG in decryptor_definition:
                decryptor_config = decryptor_definition[Config.CONFIG_KEY_DECRYPTOR_CONFIG]
            else:
                decryptor_config = {}

            DecryptionUtils.create_and_register_config_value_decryptor(
                decryptor_implementer_name,
                decryptor_config
            )

    def add_or_update_step_config( # pylint: disable=too-many-arguments
            self,
            step_name,
            sub_step_name,
            sub_step_implementer_name,
            sub_step_config_dict,
            sub_step_env_config):
        """Adds a new step configuration with a single new sub step or
        updates an existing step with new or updated sub step.

        Parameters
        ----------
        step_name : str
            Name of step to create or update.
        sub_step_name : str
            Name of the sub step to add or update on the new or updated step.
        sub_step_implementer_name : str
            Name of the sub step implementer for the sub step being added or updated.
            If updating this can not be different then existing sub step with the same name.
        sub_step_config_dict : dict, optional
            Sub step configuration to add or update for named sub step on the new or updated step.
            If updating this can not have any duplicative leaf keys to the existing
                sub step configuration.
        sub_step_env_config : dict, optional
            Sub step environment configuration to add or update for named sub step on the
                new or updated step.
            If updating this can not have any duplicative leaf keys to the existing
                sub step environment configuration.

        Raises
        ------
        AssertionError
            If attempt to update an existing sub step and new and existing sub step implementers
                do not match.
        ValueError
            If new sub step configuration has duplicative leaf keys to
                existing sub step configuration.
            If new sub step environment configuration has duplicative leaf keys to
                existing sub step environment configuration.
        """

        if step_name not in self.step_configs:
            self.step_configs[step_name] = StepConfig(self, step_name)

        step_config = self.step_configs[step_name]
        step_config.add_or_update_sub_step_config(
            sub_step_name=sub_step_name,
            sub_step_implementer_name=sub_step_implementer_name,
            sub_step_config_dict=sub_step_config_dict,
            sub_step_env_config=sub_step_env_config
        )
