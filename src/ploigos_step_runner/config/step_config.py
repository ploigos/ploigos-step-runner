"""Representation of an individual step's step configuration.
"""

import copy

from ploigos_step_runner.config.sub_step_config import SubStepConfig


class StepConfig:
    """Representation of an individual step's step configuration.

    Parameters
    ----------
    parent_config : Config
        Parent configuration containing this step configuration.
    step_name : str
        Name of the step.

    Attributes
    ----------
    __parent_config : Config
    __step_name : str
    __sub_steps : list of SubStepConfig
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
        Config
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
        list of SubStepConfig
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
        SubStepConfig
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
            sub_step_config_dict=None,
            sub_step_env_config=None):
        """Add a new or update an existing sub step configuration for this step.

        Parameters
        ----------
        sub_step_name : str
            Name of the sub step to add or update.
        sub_step_implementer_name : str
            Name of the sub step implementer for the sub step being added or updated.
            If updating this can not be different then existing sub step with the same name.
        sub_step_config_dict : dict, optional
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

        existing_sub_step_config = None
        for sub_step_config in self.sub_steps:
            if sub_step_config.sub_step_name == sub_step_name:
                existing_sub_step_config = sub_step_config
                break

        if existing_sub_step_config is None:
            sub_step_config = SubStepConfig(
                parent_step_config=self,
                sub_step_name=sub_step_name,
                sub_step_implementer_name=sub_step_implementer_name,
                sub_step_config_dict=sub_step_config_dict,
                sub_step_env_config=sub_step_env_config
            )
            self.sub_steps.append(sub_step_config)
        else:
            assert sub_step_implementer_name == sub_step_config.sub_step_implementer_name, \
                f"Step ({self.step_name}) failed to update sub step ({sub_step_name})" + \
                " with new config due to new sub step implementer" + \
                f" ({sub_step_implementer_name}) not matching existing sub step implementer" + \
                f" ({sub_step_config.sub_step_implementer_name})."

            sub_step_config.merge_sub_step_config(sub_step_config_dict)
            sub_step_config.merge_sub_step_env_config(sub_step_env_config)
