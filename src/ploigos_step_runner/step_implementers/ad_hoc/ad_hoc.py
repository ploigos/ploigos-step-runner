"""`StepImplementer` for the `ad-hoc` step using AdHoc.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key             | Required? | Default                  | Description
------------------------------|-----------|--------------------------|-----------
`command`                     | Yes       |                          | Command to execute

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key    | Description
-----------------------|------------
`stdout`               | stdout from the command run
`stderr`               | stderr from the command run
"""# pylint: disable=line-too-long

import re
import sys

import sh

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback

DEFAULT_CONFIG = {}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'command'
]

class AdHoc(StepImplementer):  # pylint: disable=too-few-public-methods
    """
    StepImplementer for the ad-hoc step for AdHoc.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

        Returns
        -------
        dict
            Default values to use for step configuration values.

        Notes
        -----
        These are the lowest precedence configuration values.

        """
        return {**DEFAULT_CONFIG}

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

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        command = self.get_value('command')
        step_result = StepResult.from_step_implementer(self)
        output_file_path = self.write_working_file('ad_hoc_output.txt')
        result = None
        try:
            with open('./output', 'w', encoding='utf-8') as output_file:
                out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stdout,
                    output_file
                ])
                err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stderr,
                    output_file
                ])

                result = sh.bash(  # pylint: disable=no-member
                    '-c',
                    command,
                    _out=out_callback,
                    _err=err_callback
                )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error running command. {error}"
            ) from error
        # except StepRunnerException as error:
        #     step_result.success = False
        #     step_result.message = str(error)
        #     return step_result

        # import pdb ; pdb.set_trace()
        # TODO: Add artifact stdout, stderr, and return code

        step_result.add_artifact(
            description="Standard out and standard error from ad-hoc command run.",
            name='command-output',
            value=output_file_path
        )

        step_result.add_artifact(
            name='exit_code',
            value=result.exit_code
        )

        return step_result
