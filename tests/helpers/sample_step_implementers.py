from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.config.config_value import ConfigValue


class FailStepImplementer(StepImplementer):
    @staticmethod
    def step_implementer_config_defaults():
        return {}

    @staticmethod
    def _required_config_or_result_keys():
        return []

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        step_result.success = False
        return step_result


class FooStepImplementer(StepImplementer):
    @staticmethod
    def step_implementer_config_defaults():
        return {}

    @staticmethod
    def _required_config_or_result_keys():
        return []

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        return step_result

class FooStepImplementer2(StepImplementer):
    @staticmethod
    def step_implementer_config_defaults():
        return {}

    @staticmethod
    def _required_config_or_result_keys():
        return []

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        return step_result

class FooStepImplementerWithDefaults(StepImplementer):
    @staticmethod
    def step_implementer_config_defaults():
        return {
            'foo-config-1': 'foo-default1',
            'foo-config-2': 'foo-default2'
        }

    @staticmethod
    def _required_config_or_result_keys():
        return []

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        return step_result

class RequiredStepConfigStepImplementer(StepImplementer):
    @staticmethod
    def step_implementer_config_defaults():
        return {}

    @staticmethod
    def _required_config_or_result_keys():
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

class RequiredStepConfigMultipleOptionsStepImplementer(StepImplementer):
    @staticmethod
    def step_implementer_config_defaults():
        return {}

    @staticmethod
    def _required_config_or_result_keys():
        return [
            ['new-required-key', 'old-required-key']
        ]

    def _run_step(self):
        step_result = StepResult.from_step_implementer(self)
        runtime_step_config = self.config.get_copy_of_runtime_step_config(
            self.environment,
            self.step_implementer_config_defaults())
        for n, v in ConfigValue.convert_leaves_to_values(runtime_step_config).items():
            step_result.add_artifact(name=n, value=v)
        return step_result

class RequiredStepConfigMultipleOptionsWithDefaultStepImplementer(StepImplementer):
    @staticmethod
    def step_implementer_config_defaults():
        return {
            'new-required-key': 'mock-default-value'
        }

    @staticmethod
    def _required_config_or_result_keys():
        return [
            ['new-required-key', 'old-required-key']
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
        return {}

    @staticmethod
    def _required_config_or_result_keys():
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
