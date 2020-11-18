from tssc import StepImplementer, StepResult
from tssc.config.config_value import ConfigValue


class FailStepImplementer(StepImplementer):
    @staticmethod
    def step_implementer_config_defaults():
        return {}

    @staticmethod
    def required_runtime_step_config_keys():
        return []

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        step_result.success = False
        return step_result


class FooStepImplementer(StepImplementer):
    @staticmethod
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
        return {}

    @staticmethod
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
        return []

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        return step_result


class RequiredStepConfigStepImplementer(StepImplementer):
    @staticmethod
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
        return {}

    @staticmethod
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
        return [
            'required-config-key'
        ]

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        runtime_step_config = self.config.get_copy_of_runtime_step_config(
            self.environment,
            self.step_implementer_config_defaults())
        for n, v in ConfigValue.convert_leaves_to_values(runtime_step_config).items():
            step_result.add_artifact(name=n, value=v)
        return step_result


class WriteConfigAsResultsStepImplementer(StepImplementer):
    @staticmethod
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
        return {}

    @staticmethod
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
        return []

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        runtime_step_config = self.config.get_copy_of_runtime_step_config(
            self.environment,
            self.step_implementer_config_defaults())

        # copy the key/value pairs into the artifacts
        for name, value in ConfigValue.convert_leaves_to_values(runtime_step_config).items():
            # print(name, value)
            step_result.add_artifact(name, value)
        return step_result


class NotSubClassOfStepImplementer():
    pass
