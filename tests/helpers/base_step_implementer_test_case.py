import os
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import yaml
from tssc import TSSCFactory
from tssc.config.config import Config

from .base_tssc_test_case import BaseTSSCTestCase


class BaseStepImplementerTestCase(BaseTSSCTestCase):
    def create_given_step_implementer(
        self,
        step_implementer,
        step_config={},
        results_dir_path='',
        results_file_name='',
        work_dir_path='',
    ):
        config = Config({
            Config.TSSC_CONFIG_KEY: {
                'test': [
                    {
                        'implementer': 'OpenSCAP',
                        'config': step_config
                    }
                ]

            }
        })
        step_config = config.get_step_config('test')
        sub_step_config = step_config.get_sub_step('OpenSCAP')

        step_implementer = step_implementer(
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path,
            config=sub_step_config
        )

        return step_implementer

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

        results_file_name = "tssc-results.yml"
        with open(os.path.join(results_dir_path, results_file_name), 'r') as step_results_file:
            actual_step_results = yaml.safe_load(step_results_file.read())

            self.assertEqual(actual_step_results, expected_step_results)
