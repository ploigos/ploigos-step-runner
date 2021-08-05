"""`StepImplementer` for the `unit-test` step using npm 

"""
import os
from posixpath import abspath
import sys
# from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.step_implementers.shared.npm_generic import NpmGeneric
from ploigos_step_runner.utils.io import create_sh_redirect_to_multiple_streams_fn_callback

import sh
from ploigos_step_runner import StepResult

DEFAULT_CONFIG = {
    'package-file': 'package.json'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'package-file'
]
class Npm(NpmGeneric):
    """`StepImplementer` for the `unit-test` step using npm.
    """

    def __init__(self, workflow_result, parent_work_dir_path, config, environment):
        super().__init__(workflow_result, parent_work_dir_path, config, environment=environment, npm_targets=['test'])

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

        Notes
        -----
        These are the lowest precedence configuration values.

        Returns
        -------
        dict
            Default values to use for step configuration values.
        """
        return {**NpmGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

    @staticmethod
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
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS

    # def _validate_required_config_or_previous_step_result_artifact_keys(self):
    #     """Validates that the required configuration keys or previous step result artifacts
    #     are set and have valid values.

    #     Validates that:
    #     * required configuration is given
    #     * given 'package-file' exists

    #     Raises
    #     ------
    #     AssertionError
    #         If step configuration or previous step result artifacts have invalid required values
    #     """
    #     super()._validate_required_config_or_previous_step_result_artifact_keys()

    #     package_file = self.get_value('package-file')
    #     assert os.path.exists(package_file), \
    #         f'Given npm package file (package-file) does not exist: {package_file}'

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        npm_output_file_path = self.write_working_file('npm_test_output.txt')
        try:
            self._run_npm_step(
                npm_output_file_path=npm_output_file_path
            )

        except sh.ErrorReturnCode as error:
            step_result.message = "Unit test failures. See 'npm-output'" \
                f" report artifacts for details: {error}"
            step_result.success = False
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from 'npm test'.",
                name='npm-output',
                value=npm_output_file_path
            )

            return step_result
