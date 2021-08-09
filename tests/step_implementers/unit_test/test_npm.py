import os
from pathlib import Path
from unittest.mock import Mock, patch
from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult, step_implementer
from ploigos_step_runner.step_implementers.unit_test import Npm
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase

@patch("ploigos_step_runner.step_implementers.shared.NpmGeneric.__init__")
class TestStepImplementerMavenTest___init__(BaseStepImplementerTestCase):
    def test_defaults(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        Npm(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None,
            npm_run_scripts=['test']
        )

class TestStepImplementerMavenTest_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            Npm.step_implementer_config_defaults(),
            {
                'package-file': 'package.json'
            }
        )

class TestStepImplementerMavenTest__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            Npm._required_config_or_result_keys(),
            [
                'package-file'
            ]
        )

@patch('ploigos_step_runner.step_implementers.unit_test.Npm._run_npm_step')
@patch('ploigos_step_runner.step_implementers.unit_test.Npm.write_working_file')
class TestStepImplementerNpm__run_step(BaseStepImplementerTestCase):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):

        return self.create_given_step_implementer(
            step_implementer=Npm,
            step_config=step_config,
            step_name='unit-test',
            implementer='Npm',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )
