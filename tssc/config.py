"""
Configuration for TSSC workflow.
"""

import copy
import glob
import os.path

from .utils.file import parse_yaml_or_json_file
from .utils.dict import deep_merge

class TSSCConfig:
    """Representation of configuration for TSSC workflow.

    Parameters
    ----------
    config : dict, list, str (file or directory), optional
        A dictionary that is a valid TSSC configuration,
        a string that is a path to a YAML or JSON file that is
        a valid TSSC configuration,
        a string that is a path to a directory containing one or more
        files that are valid YAML or JSON files that are valid
        configurations,
        or a list of any of the former.

    Attributes
    ----------
    __global_defaults : dict
    __global_environment_defaults : dict
    __tssc_step_configs : dict of str (step names) to TSSCStepConfig

    Raises
    ------
    ValueError
        If given config is not of expected type.
    AssertionError
        If given config contains any invalid TSSC configurations.
    """
    TSSC_CONFIG_KEY = 'tssc-config'
    TSSC_CONFIG_KEY_GLOBAL_DEFAULTS = 'global-defaults'
    TSSC_CONFIG_KEY_GLOBAL_ENVIRONMENT_DEFAULTS = 'global-environment-defaults'
    TSSC_CONFIG_KEY_ENVIRONMENT_NAME = 'environment-name'
    TSSC_CONFIG_KEY_STEP_IMPLEMENTER = 'implementer'
    TSSC_CONFIG_KEY_SUB_STEP_NAME = 'name'
    TSSC_CONFIG_KEY_SUB_STEP_CONFIG = 'config'
    TSSC_CONFIG_KEY_SUB_STEP_ENVIRONMENT_CONFIG = 'environment-config'

    def __init__(self, config=None):
        self.__global_defaults = {}
        self.__global_environment_defaults = {}
        self.__tssc_step_configs = {}

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
        list of TSSCStepConfig
        """
        return self.__tssc_step_configs

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
        TSSCStepConfig
            Step configuration for the given step name or None if does not exist
        """
        if step_name in self.step_configs:
            step_config = self.step_configs[step_name]
        else:
            step_config = None

        return step_config

    def get_sub_step_configs(self, step_name):
        """Gets lit of configured TSSC sub step configurations for a TSSC step with the given name.

        Parameters
        ----------
        step_name : str
            Name of TSSC step to get configured sub steps for.

        Returns
        -------
        list of TSSCSubStepConfig
            List of configured TSSC sub step configurations for the TSSC step with the given name.
        """

        if step_name in self.step_configs:
            sub_step_configs = self.step_configs[step_name].sub_steps
        else:
            sub_step_configs = []

        return sub_step_configs

    def add_config(self, config):
        """Parses, validates, and adds a given config to this TSSCConfig.

        Parameters
        ----------
        config : dict, list, str (file or directory)
            A dictionary that is a valid TSSC configuration,
            a string that is a path to a YAML or JSON file that is
            a valid TSSC configuration,
            a string that is a path to a directory containing one or more
            files that are valid YAML or JSON files that are valid
            configurations,
            or a list of any of the former.

        Raises
        ------
        ValueError
            If given config is not of expected type.
        AssertionError
            If given config contains any invalid TSSC configurations.
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
            self.step_configs[step_name] = TSSCStepConfig(self, step_name)

        self.step_configs[step_name].step_config_overrides = step_config_overrides

    def __add_config_file(self, config_file):
        """Adds a JSON or YAML file as config to this TSSCConfig.

        Parameters
        ----------
        config_file : str (file path)
            A string that is a path to an existing YAML or JSON file to
            parse and validate as a TSSC configuration to add to this TSSCConfig.

        Raises
        ------
        ValueError
            If can not parse given file as YAML or JSON
        AssertionError
            If dictionary parsed from given YAML or JSON file is not a valid TSSC config.
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
            self.__add_config_dict(parsed_config_file)
        except AssertionError as error:
            raise AssertionError(
                f"Failed to add parsed configuration file ({config_file}): {error}"
            ) from error

    def __add_config_dict(self, config_dict): # pylint: disable=too-many-locals, too-many-branches
        """Add a TSSC configuration dictionary to the list of TSSC configuration dictionaries.

        Parameters
        ----------
        config_dict : dict
            A dictionary to validate as a TSSC configuration and to add to this TSSCConfig.

        Raises
        ------
        AssertionError
            If the given config_dict is not a valid TSSC configuration dictionary.
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

        assert TSSCConfig.TSSC_CONFIG_KEY in config_dict, \
            "Failed to add invalid TSSC config. " + \
            f"Missing expected top level key ({TSSCConfig.TSSC_CONFIG_KEY}): " + \
            f"{config_dict}"

        tssc_config = config_dict[TSSCConfig.TSSC_CONFIG_KEY]
        for key, value in tssc_config.items():
            # if global default key
            # else if global env defaults key
            # else assume step config
            if key == TSSCConfig.TSSC_CONFIG_KEY_GLOBAL_DEFAULTS:
                try:
                    self.__global_defaults = deep_merge(
                        copy.deepcopy(self.__global_defaults),
                        copy.deepcopy(value)
                    )
                except ValueError as error:
                    raise ValueError(
                        f"Error merging global defaults: {error}"
                    ) from error
            elif key == TSSCConfig.TSSC_CONFIG_KEY_GLOBAL_ENVIRONMENT_DEFAULTS:
                for env, env_config in value.items():
                    if env not in self.__global_environment_defaults:
                        self.__global_environment_defaults[env] = {
                            TSSCConfig.TSSC_CONFIG_KEY_ENVIRONMENT_NAME: env
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
                    assert TSSCConfig.TSSC_CONFIG_KEY_STEP_IMPLEMENTER in sub_step, \
                        f"Step ({step_name}) defines a single sub step with values " + \
                        f"({sub_step}) but is missing value for key: " + \
                        f"{TSSCConfig.TSSC_CONFIG_KEY_STEP_IMPLEMENTER}"

                    sub_step_implementer_name = \
                        sub_step[TSSCConfig.TSSC_CONFIG_KEY_STEP_IMPLEMENTER]

                    # if sub step name given
                    # else if no sub step name given use step implementer as sub step name
                    if TSSCConfig.TSSC_CONFIG_KEY_SUB_STEP_NAME in sub_step:
                        sub_step_name = sub_step[TSSCConfig.TSSC_CONFIG_KEY_SUB_STEP_NAME]
                    else:
                        sub_step_name = sub_step_implementer_name

                    if TSSCConfig.TSSC_CONFIG_KEY_SUB_STEP_CONFIG in sub_step:
                        sub_step_config = copy.deepcopy(
                            sub_step[TSSCConfig.TSSC_CONFIG_KEY_SUB_STEP_CONFIG])
                    else:
                        sub_step_config = {}

                    if TSSCConfig.TSSC_CONFIG_KEY_SUB_STEP_ENVIRONMENT_CONFIG in sub_step:
                        sub_step_env_config = copy.deepcopy(
                            sub_step[TSSCConfig.TSSC_CONFIG_KEY_SUB_STEP_ENVIRONMENT_CONFIG])
                    else:
                        sub_step_env_config = {}

                    self.add_or_update_step_config(
                        step_name=step_name,
                        sub_step_name=sub_step_name,
                        sub_step_implementer_name=sub_step_implementer_name,
                        sub_step_config=sub_step_config,
                        sub_step_env_config=sub_step_env_config
                    )

    def add_or_update_step_config( # pylint: disable=too-many-arguments
            self,
            step_name,
            sub_step_name,
            sub_step_implementer_name,
            sub_step_config,
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
        sub_step_config : dict, optional
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
            self.step_configs[step_name] = TSSCStepConfig(self, step_name)

        tssc_step_config = self.step_configs[step_name]
        tssc_step_config.add_or_update_sub_step_config(
            sub_step_name=sub_step_name,
            sub_step_implementer_name=sub_step_implementer_name,
            sub_step_config=sub_step_config,
            sub_step_env_config=sub_step_env_config
        )

class TSSCStepConfig:
    """Representation of a TSSC step configuration.

    Parameters
    ----------
    parent_config : TSSCConfig
        Parent TSSC configuration containing this step configuration.
    step_name : str
        Name of the TSSC step.

    Attributes
    ----------
    __parent_config : TSSCConfig
    __step_name : str
    __sub_steps : list of TSSCSubStepConfig
    __sub_step_config_overrides : dict
    """

    def __init__(self, parent_config, step_name):
        self.__parent_config = parent_config
        self.__step_name = step_name
        self.__sub_steps = []
        self.__step_config_overrides = {}

    @property
    def parent_config(self):
        """
        Returns
        -------
        TSSCConfig
        """
        return self.__parent_config

    @property
    def step_name(self):
        """
        Returns
        -------
        str
            Name of this step.
        """
        return self.__step_name

    @property
    def sub_steps(self):
        """
        Returns
        -------
        list of TSSCSubStepConfig
            Sub steps of this step.
        """
        return self.__sub_steps

    def get_sub_step(self, sub_step_name):
        """Get sub step of this step with a given name if one exists.

        Parameters
        ----------
        sub_step_name : str
            Name of the sub step of this step to get.

        Returns
        -------
        TSSCSubStepConfig
            Sub step of this step with the given name or
            None if no sub step with given name exists as part of this step.
        """
        for sub_step in self.sub_steps:
            if sub_step_name == sub_step.sub_step_name:
                return sub_step

        return None

    @property
    def step_config_overrides(self):
        """Gets a deep copy of the step configuration overrides.

        Returns
        -------
        dict
            Deep copy of the step configuration overrides.
        """
        return copy.deepcopy(self.__step_config_overrides)

    @step_config_overrides.setter
    def step_config_overrides(self, step_config_overrides):
        """Sets the step configuration overrides.

        Parameters
        ----------
        step_config_overrides : dict
            New step configuration overrides.
        """
        self.__step_config_overrides = step_config_overrides if step_config_overrides else {}

    def add_or_update_sub_step_config(
            self,
            sub_step_name,
            sub_step_implementer_name,
            sub_step_config=None,
            sub_step_env_config=None):
        """Add a new or update an existing sub step configuration for this step.

        Parameters
        ----------
        sub_step_name : str
            Name of the sub step to add or update.
        sub_step_implementer_name : str
            Name of the sub step implementer for the sub step being added or updated.
            If updating this can not be different then existing sub step with the same name.
        sub_step_config : dict, optional
            Sub step configuration to add or update for named sub step.
            If updating this can not have any duplicative leaf keys to the existing
                sub step configuration.
        sub_step_env_config : dict, optional
            Sub step environment configuration to add or update for named sub step.
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

        existing_tssc_sub_step_config = None
        for tssc_sub_step_config in self.sub_steps:
            if tssc_sub_step_config.sub_step_name == sub_step_name:
                existing_tssc_sub_step_config = tssc_sub_step_config
                break

        if existing_tssc_sub_step_config is None:
            tssc_sub_step_config = TSSCSubStepConfig(
                parent_step_config=self,
                sub_step_name=sub_step_name,
                sub_step_implementer_name=sub_step_implementer_name,
                sub_step_config=sub_step_config,
                sub_step_env_config=sub_step_env_config
            )
            self.sub_steps.append(tssc_sub_step_config)
        else:
            assert sub_step_implementer_name == tssc_sub_step_config.sub_step_implementer_name, \
                f"Step ({self.step_name}) failed to update sub step ({sub_step_name})" + \
                " with new config due to new sub step implementer" + \
                f" ({sub_step_implementer_name}) not matching existing sub step implementer" + \
                f" ({tssc_sub_step_config.sub_step_implementer_name})."

            tssc_sub_step_config.merge_sub_step_config(sub_step_config)
            tssc_sub_step_config.merge_sub_step_env_config(sub_step_env_config)

class TSSCSubStepConfig:
    """Representation of a TSSC sub step configuration.

    Parameters
    ----------
    parent_step_config : TSSCStepConfig
        Parent TSSC step config to this sub step coonfig.
    sub_step_name : str
        Name of this sub step.
    sub_step_implementer_name : str
        Step implementer for this sub step.
    sub_step_config : dict, optional
        Configuration specific to this sub step.
    sub_step_env_config : dict, optional
        Environment specific configuration specific to this sub step.

    Attributes
    ----------
    __parent_step_config : TSSCStepConfig
    __sub_step_name : str
    __sub_step_implementer_name : str
    __sub_step_config : dict
    __sub_step_env_config : dict
    """

    def __init__( # pylint: disable=too-many-arguments
            self,
            parent_step_config,
            sub_step_name,
            sub_step_implementer_name,
            sub_step_config=None,
            sub_step_env_config=None):

        self.__parent_step_config = parent_step_config
        self.__sub_step_name = sub_step_name
        self.__sub_step_implementer_name = sub_step_implementer_name

        if sub_step_config is None:
            sub_step_config = {}
        self.__sub_step_config = sub_step_config

        if sub_step_env_config is None:
            sub_step_env_config = {}
        self.__sub_step_env_config = sub_step_env_config

    @property
    def parent_config(self):
        """
        Returns
        -------
        TSSCConfig
            Parent TSSC config.
        """
        return self.parent_step_config.parent_config

    @property
    def parent_step_config(self):
        """
        Returns
        -------
        TSSCStepConfig
            Parent TSSC step config.
        """
        return self.__parent_step_config

    @property
    def step_name(self):
        """Convenience function to get parent TSSC step name.

        Returns
        -------
        str
            Parent TSSC step name.
        """
        return self.parent_step_config.step_name

    @property
    def step_config_overrides(self):
        """Convenience function to get step config overrides

        Returns
        -------
        str
            Parent TSSC step config overrides
        """
        return self.parent_step_config.step_config_overrides

    @property
    def sub_step_name(self):
        """
        Returns
        -------
        str
            TSSC sub step name.
        """
        return self.__sub_step_name

    @property
    def sub_step_implementer_name(self):
        """
        Returns
        -------
        str
            TSSC implementer name.
        """
        return self.__sub_step_implementer_name

    @property
    def sub_step_config(self):
        """Get a deep copy of the sub step configuration.

        Returns
        -------
        dict
            Deep copy of the sub step configuration.
        """
        return copy.deepcopy(self.__sub_step_config)

    @property
    def global_defaults(self):
        """Convince function for getting the global defaults from the parent config.

        Returns
        -------
        dict
            Deep copy of the global defaults
        """
        return self.parent_config.global_defaults

    @property
    def sub_step_env_config(self):
        """Gets the environment specific configuration for all environments for this sub step.

        Returns
        -------
        dict
            The environment specific configuration for all environments for this sub step.
        """
        return copy.deepcopy(self.__sub_step_env_config)

    def get_global_environment_defaults(self, env):
        """Convince function for getting the global environment defaults from the parent config.

        Parameters
        ----------
        env : str
            Environment to get the global environment configuration for.

        Returns
        -------
        dict
            Deep copy of the global defaults for a given environment
        """
        return self.parent_config.get_global_environment_defaults_for_environment(env)

    def get_sub_step_env_config(self, env):
        """Get the sub step environment configuration for an environment.

        Parameters
        ----------
        env : str
            Environment to get the sub step configuration for.

        Returns
        -------
        dict
            Environment specific sub step configuration.
            Empty dict if no environment specific sub step configuration.
        """
        if env in self.sub_step_env_config:
            sub_step_env_config = self.sub_step_env_config[env]
        else:
            sub_step_env_config = {}

        return sub_step_env_config

    def merge_sub_step_config(self, new_sub_step_config):
        """Merge new sub step configuration into the existing sub step configuration.

        Parameters
        ----------
        new_sub_step_config : dict
            New sub step configuration to merge into the existing sub step configuration.

        Raises
        ------
        ValueError
            If new sub step configuration has duplicative leaf keys to
                existing sub step configuration.
        """

        if new_sub_step_config is not None:
            try:
                self.__sub_step_config = deep_merge(
                    self.sub_step_config,
                    copy.deepcopy(new_sub_step_config)
                )
            except ValueError as error:
                raise ValueError(
                    "Error merging new sub step configuration" +
                    " into existing sub step configuration" +
                    f" for sub step ({self.sub_step_name}) of step ({self.step_name}): {error}"
                ) from error

    def merge_sub_step_env_config(self, new_sub_step_env_config):
        """Merge new sub step environment configuration into the existing
        sub step environment configuration.

        Parameters
        ----------
        new_sub_step_env_config : dict
            New sub step environment configuration to merge into
                the existing sub step environment configuration.

        Raises
        ------
        ValueError
            If new sub step environment configuration has duplicative leaf keys to
                existing sub step environment configuration.
        """

        if new_sub_step_env_config is not None:
            try:
                self.__sub_step_env_config = deep_merge(
                    self.__sub_step_env_config,
                    copy.deepcopy(new_sub_step_env_config)
                )
            except ValueError as error:
                raise ValueError(
                    "Error merging new sub step environment configuration" +
                    " into existing sub step environment configuration" +
                    f" for sub step ({self.sub_step_name}) of step ({self.step_name}): {error}"
                ) from error

    def get_runtime_step_config(self, environment=None, defaults=None):
        """Take all of the context about this sub step merges together a single dictionary
        with all of the configuration for a given step.

        From least precedence to highest precedence.

            1. defaults
            2. Global Configuration Defaults (self.global_config_defaults)
            3. Global Environment Configuration Defaults (self.global_environment_config_defaults)
            4. Step Configuration ( self.step_config)
            5. Step Environment Configuration (self.step_environment_config)
            6. Step Configuration Runtime Overrides (step_config_runtime_overrides)

        Parameters
        ----------
        environment : str, optional
            Environment to get the runtime step configuration for
        defaults : dict, optional
            Defaults to use if no other configuration specified from any other source
            for each given key.

        Returns
        -------
        dict
            TODO
        """
        defaults = defaults if defaults else {}

        return copy.deepcopy({
            **defaults,
            **self.global_defaults,
            **self.get_global_environment_defaults(environment),
            **self.sub_step_config,
            **self.get_sub_step_env_config(environment),
            **self.step_config_overrides,
        })
