# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import yaml
from tssc.factory import TSSCFactory
from tssc.config.config import Config
from tssc.exceptions import StepRunnerException
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult

from .base_tssc_test_case import BaseTSSCTestCase


class BaseStepImplementerTestCase(BaseTSSCTestCase):
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
            Config.TSSC_CONFIG_KEY: {
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
        pickle_filename = os.path.join(work_dir_path, 'tssc-results.pkl')
        workflow_result.write_to_pickle_file(pickle_filename=pickle_filename)
