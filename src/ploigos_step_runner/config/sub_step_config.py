"""Representation of a sub step configuration.
"""

import copy

from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.utils.dict import deep_merge


class SubStepConfig:
    """Representation of a sub step configuration.

    Parameters
    ----------
    parent_step_config : StepConfig
        Parent StepConfig to this sub step coonfig.
    sub_step_name : str
        Name of this sub step.
    sub_step_implementer_name : str
        Step implementer for this sub step.
    sub_step_config_dict : dict, optional
        Configuration specific to this sub step.
    sub_step_env_config : dict, optional
        Environment specific configuration specific to this sub step.

    Attributes
    ----------
    __parent_step_config : StepConfig
    __sub_step_name : str
    __sub_step_implementer_name : str
    __sub_step_config_dict : dict
    __sub_step_env_config : dict
    """

    def __init__( # pylint: disable=too-many-arguments
            self,
            parent_step_config,
            sub_step_name,
            sub_step_implementer_name,
            sub_step_config_dict=None,
            sub_step_env_config=None):

        self.__parent_step_config = parent_step_config
        self.__sub_step_name = sub_step_name
        self.__sub_step_implementer_name = sub_step_implementer_name

        if sub_step_config_dict is None:
            sub_step_config_dict = {}
        self.__sub_step_config_dict = sub_step_config_dict

        if sub_step_env_config is None:
            sub_step_env_config = {}
        self.__sub_step_env_config = sub_step_env_config

    @property
    def parent_config(self):
        """
        Returns
        -------
        Config
            Parent Config.
        """
        return self.parent_step_config.parent_config

    @property
    def parent_step_config(self):
        """
        Returns
        -------
        StepConfig
            Parent StepConfig.
        """
        return self.__parent_step_config

    @property
    def step_name(self):
        """Convenience function to get parent step name.

        Returns
        -------
        str
            Parent step name.
        """
        return self.parent_step_config.step_name

    @property
    def step_config_overrides(self):
        """Convenience function to get step config overrides

        Returns
        -------
        str
            Parent step config overrides
        """
        return self.parent_step_config.step_config_overrides

    @property
    def sub_step_name(self):
        """
        Returns
        -------
        str
            Sub step name.
        """
        return self.__sub_step_name

    @property
    def sub_step_implementer_name(self):
        """
        Returns
        -------
        str
            Step implementer name.
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
        return copy.deepcopy(self.__sub_step_config_dict)

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
                self.__sub_step_config_dict = deep_merge(
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

    def get_config_value(self, key, environment=None, defaults=None):
        """Get the configuration value for a given configuration key from the
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
        runtime_step_config = self.__merge_runtime_step_config(environment, defaults)

        if key in runtime_step_config:
            if isinstance(runtime_step_config[key], ConfigValue):
                value = runtime_step_config[key].value
            else:
                value = copy.deepcopy(runtime_step_config[key])
        else:
            value = None

        return value

    def get_copy_of_runtime_step_config(self, environment=None, defaults=None):
        """Take all of the context about this sub step merges together a single dictionary
        with all of the configuration for a given step.

        From least precedence to highest precedence.

            1. defaults
            2. Global Configuration Defaults (self.global_config_defaults)
            3. Global Environment Configuration Defaults (self.global_environment_config_defaults)
            4. Step Configuration ( self.step_config)
            5. Step Environment Configuration (self.step_environment_config)
            6. Step Configuration Runtime Overrides (step_config_runtime_overrides)

        Also See
        --------
        get_config_value

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
            A deep copy of the merged runtime step configuration
        """
        defaults = defaults if defaults else {}

        return copy.deepcopy(self.__merge_runtime_step_config(environment, defaults))

    def __merge_runtime_step_config(self, environment=None, defaults=None):
        """Take all of the context about this sub step merges together a single dictionary
        with all of the configuration for a given step.

        From least precedence to highest precedence.

            1. defaults
            2. Global Configuration Defaults (self.global_config_defaults)
            3. Global Environment Configuration Defaults (self.global_environment_config_defaults)
            4. Step Configuration ( self.step_config)
            5. Step Environment Configuration (self.step_environment_config)
            6. Step Configuration Runtime Overrides (step_config_runtime_overrides)

        Notes
        -----
        This is not intended to be accessed outside of this class since it gives direct access
        to the underlying dictionaries which could in theory be changed, which would not be the
        intended use.

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
            Merged runtime step configuration
        """
        defaults = defaults if defaults else {}

        return {
            **defaults,
            **self.global_defaults,
            **self.get_global_environment_defaults(environment),
            **self.sub_step_config,
            **self.get_sub_step_env_config(environment),
            **self.step_config_overrides,
        }
