"""`StepImplementer` for the `static-code-analysis` step using tox and pylint

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default          | Description
-----------------------------|-----------|------------------|-----------
`tox-config`                 | Yes       | `'tox.ini'`      | tox.ini file for reference app.
`quiet`                      | No        | `True`           | disable quiet mode during execution.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`tox-output`        | Path to Stdout and Stderr from invoking Tox.
"""


from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.shared.tox_generic import ToxGeneric
from ploigos_step_runner.exceptions import StepRunnerException


class ToxLint(ToxGeneric):
    """`StepImplementer` for the `lint` step using tox and pylint.
    """

    def __init__(self, workflow_result, parent_work_dir_path, config, environment):
        super().__init__(
            workflow_result,
            parent_work_dir_path,
            config,
            environment=environment,
            tox_env='lint'
        )

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
        return []

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        tox_output_file_path = self.write_working_file('tox_lint_output.txt')

        try:
            self._run_tox_step(
                tox_output_file_path=tox_output_file_path
            )

        except StepRunnerException as error:
            step_result.message = "Lint failures. See 'tox-output'" \
                f" report artifacts for details: {error}"
            step_result.success = False
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from 'tox lint'.",
                name='tox-output',
                value=tox_output_file_path
            )

        return step_result
