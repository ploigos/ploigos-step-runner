# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import yaml
from ploigos_step_runner.step_runner import StepRunner
from ploigos_step_runner.config.config import Config
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_result import StepResult
from ploigos_step_runner.workflow_result import WorkflowResult

from .base_test_case import BaseTestCase


class BaseStepImplementerTestCase(BaseTestCase):
    def create_given_step_implementer(
        self,
        step_implementer,
        step_config={},
        step_name='',
        environment=None,
        implementer='',
        results_dir_path='',
        results_file_name='',
        work_dir_path='',
    ):
        config = Config({
            Config.CONFIG_KEY: {
                step_name: [
                    {
                        'implementer': implementer,
                        'config': step_config
                    }
                ]

            }
        })
        step_config = config.get_step_config(step_name)
        sub_step_config = step_config.get_sub_step(implementer)

        step_implementer = step_implementer(
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path,
            config=sub_step_config,
            environment=environment
        )

        return step_implementer

    def setup_previous_result(
        self,
        work_dir_path,
        artifact_config={}
    ):
        step_result = StepResult(
            step_name='test-step',
            sub_step_name='test-sub-step-name',
            sub_step_implementer_name='test-step-implementer-name'
        )
        for key1, val1 in artifact_config.items():
            description = ''
            value = ''
            for key2, val2 in val1.items():
                if key2 == 'description':
                    description = val2
                elif key2 == 'value':
                    value = val2
                else:
                    raise StepRunnerException(f'Given field is not apart of an artifact: {key2}')
            step_result.add_artifact(
                name=key1,
                value=value,
                description=description,
            )
        workflow_result = WorkflowResult()
        workflow_result.add_step_result(step_result=step_result)
        pickle_filename = os.path.join(work_dir_path, 'step-runner-results.pkl')
        workflow_result.write_to_pickle_file(pickle_filename=pickle_filename)
