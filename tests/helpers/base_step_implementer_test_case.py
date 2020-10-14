import os
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from tssc.factory import TSSCFactory
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase


def workflow_previous_results(pickle_filename, tssc_results):
    """
    Input a tssc-results and create a pickle file to use for testing.
    "tssc-results": {
      "step1": {
        "sub1": {
            "sub-step-implementer-name": "implementer1",
            "success": true,
            "message": "",
            "artifacts": {
                "artifact1": {
                    "description": "description1",
                    "type": "type1",
                    "value": "value1"
                },
                "artifact4": {
                    "description": "",
                    "type": "bool",
                    "value": false
                }
            }
        }
    }
    """
    wfr = WorkflowResult()
    for results, steps in tssc_results.items():
        for step_name, sub_steps in steps.items():
            for sub_step_name, p_info in sub_steps.items():
                step_implementer = p_info['sub-step-implementer-name']
                # todo: need to create a StepImplementer ... ugh
                step_result = StepResult(step_name=step_name,
                                         sub_step_name=sub_step_name,
                                         sub_step_implementer_name=step_implementer)
                artifacts = p_info['artifacts']
                for artifact, artifact_info in artifacts.items():
                    artifact_name = artifact
                    value = artifact_info['value']
                    step_result.add_artifact(
                        name=artifact_name,
                        value=value)
                    wfr.add_step_result(
                        step_result=step_result
                    )

    wfr.write_to_pickle_file(
        pickle_filename=pickle_filename
    )


class BaseStepImplementerTestCase(BaseTSSCTestCase):

    def run_step_test_with_result_validation(
            self,
            temp_dir,
            step_name,
            config,
            expected_step_results,
            runtime_args=None,
            environment=None,
            expected_stdout=None,
            expected_stderr=None,
            previous_results=None
    ):
        results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
        working_dir_path = os.path.join(temp_dir.path, 'tssc-working')

        if previous_results is not None:
            pickle_filename = os.path.join(temp_dir.path, 'tssc-working/tssc-results.pkl')
            workflow_previous_results(
                pickle_filename=pickle_filename,
                tssc_results=previous_results)

        factory = TSSCFactory(config, results_dir_path, work_dir_path=working_dir_path)
        if runtime_args:
            factory.config.set_step_config_overrides(step_name, runtime_args)

        out = StringIO()
        err = StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            factory.run_step(step_name, environment)

        if expected_stdout is not None:
            self.assertRegex(out.getvalue(), expected_stdout)

        if expected_stderr is not None:
            self.assertRegex(err.getvalue(), expected_stderr)

        pickle = f'{working_dir_path}/tssc-results.pkl'
        workflow_results = WorkflowResult.load_from_pickle_file(pickle)
        actual_step_results = workflow_results.get_step_result(step_name)
        expected_step_results = {
            'tssc-results': expected_step_results
        }

        print(actual_step_results)
        print(expected_step_results)
        self.assertEqual(actual_step_results, expected_step_results)
