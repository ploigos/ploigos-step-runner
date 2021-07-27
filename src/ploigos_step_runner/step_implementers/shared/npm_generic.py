import os
from unittest.main import main

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
            self.get_value('author')
        )
        package_author_email = ConfigValue.convert_leaves_to_values(
            self.get_value('author-email')
        )
        package_license = ConfigValue.convert_leaves_to_values(
            self.get_value('license')
        )

        return generate_package_json(
            working_dir=self.work_dir_path,
            author=package_author,
            author_email=package_author_email,
            license=package_license
        )
