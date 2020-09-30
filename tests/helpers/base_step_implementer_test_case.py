import os
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import yaml
from tssc import TSSCFactory, StepResult, WorkflowResult

from .base_tssc_test_case import BaseTSSCTestCase

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
        expected_stderr=None
    ):
        results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
        working_dir_path = os.path.join(temp_dir.path, 'tssc-working')

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
        results_file_name = "tssc-results.yml"
        expected_step_results = {
            'tssc-results': expected_step_results
        }

        print(actual_step_results)
        print(expected_step_results)
        self.assertEqual(actual_step_results, expected_step_results)
