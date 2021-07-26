import os

from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.step_implementer import StepImplementer

from ploigos_step_runner.utils.npm import generate_package_json

class NpmGeneric(StepImplementer):
    """Abstract parent class for StepImplementers that use npm.
    """

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        return super()._validate_required_config_or_previous_step_result_artifact_keys()

        package_file = self.get_value('package-file')

    def _generate_package_json(self):
        package_author = ConfigValue.convert_leaves_to_values(
            self.get_value('package-params.author')
        )
        package_license = ConfigValue.convert_leaves_to_values(
            self.get_value('package-params.license')
        )

        print(self.work_dir_path,
        package_author,
        package_license)

