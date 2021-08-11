"""`StepImplementer` for the `deploy` step using `helm secrets upgrade --install` so that it works for both an initial \
upgrade of a preinstalled helm chart.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default | Description
-----------------------------|-----------|---------|-----------
`helm-chart`                 | Yes       |         | The chart argument can be either: a chart \
                                                     reference('example/mariadb'), a path to a chart directory, a \
                                                     packaged chart, or a fully qualified URL.
`helm-release`               | Yes       |         | Release tag.
`helm-flags`                 | No        | `[]`    | Use flags to customize the installation behavior.
"""  # pylint: disable=line-too-long


import sys
import sh

from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback

DEFAULT_CONFIG = {
    'helm-flags': []
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'helm-chart',
    'helm-release'
]

class Helm(StepImplementer):
    """`StepImplementer` for the `deploy` step using Helm.
    """

    def __init__(  # pylint: disable=too-many-arguments
            self,
            workflow_result,
            parent_work_dir_path,
            config,
            environment=None
    ):

        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment
        )

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
        return DEFAULT_CONFIG

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

    def _run_step(self): # pylint: disable=too-many-locals
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # install the helm chart
        helm_output_file_path = self.write_working_file('helm_output.txt')
        try:
            # execute helm step (params come from config)
            with open(helm_output_file_path, 'w') as helm_output_file:
                sh.helm( # pylint: disable=no-member
                    'secrets', 'upgrade', '--install',
                    self.get_value('helm-chart'),
                    self.get_value('helm-release'),
                    *self.get_value('helm-flags'),
                    _out=create_sh_redirect_to_multiple_streams_fn_callback([
                        sys.stdout,
                        helm_output_file
                    ]),
                    _err=create_sh_redirect_to_multiple_streams_fn_callback([
                        sys.stderr,
                        helm_output_file
                    ])
                )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running helm. " \
                                  f"More details maybe found in 'helm-output' report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from helm.",
                name='helm-output',
                value=helm_output_file_path
            )

        return step_result
