"""`StepImplementer` for the `unit-test` step using tox
"""

from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.shared.tox_generic import ToxGeneric
from ploigos_step_runner.exceptions import StepRunnerException


class ToxTest(ToxGeneric):
    """`StepImplementer` for the `unit-test` step using tox.
    """

    def __init__(self, workflow_result, parent_work_dir_path, config, environment):
        super().__init__(
            workflow_result,
            parent_work_dir_path,
            config,
            environment=environment,
            tox_env='test'
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

        tox_output_file_path = self.write_working_file('tox_test_output.txt')

        try:
            self._run_tox_step(
                tox_output_file_path=tox_output_file_path
            )

        except StepRunnerException as error:
            step_result.message = "Unit test failures. See 'tox-output'" \
                f" report artifacts for details: {error}"
            step_result.success = False
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from 'tox test'.",
                name='tox-output',
                value=tox_output_file_path
            )

        return step_result
