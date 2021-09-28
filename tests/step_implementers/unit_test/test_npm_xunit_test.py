import os
from unittest.mock import patch, call

from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from ploigos_step_runner.step_implementers.unit_test import NpmXunitTest
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any


class BaseTestStepImplementerNpmXunitTest(
    BaseStepImplementerTestCase
):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=NpmXunitTest,
            step_config=step_config,
            step_name='unit-test',
            implementer='NpmXunitTest',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )


@patch("ploigos_step_runner.step_implementers.shared.NpmGeneric.__init__")
class TestStepImplementerNpmXunitTest___init__(BaseStepImplementerTestCase):
    def test_defaults(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        NpmXunitTest(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None,

        )

    def test_given_environment(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        NpmXunitTest(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='mock-env'
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='mock-env'
        )


class TestStepImplementerNpmXunitTest_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            NpmXunitTest.step_implementer_config_defaults(),
            {
                'package-file': 'package.json',
                'npm-test-script': 'test'
            }
        )


class TestStepImplementerNpmXunitTest__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            NpmXunitTest._required_config_or_result_keys(),
            [
                'test-reports-dir'
            ]
        )


@patch.object(NpmXunitTest, '_run_npm_step')
@patch.object(NpmXunitTest, 'write_working_file', return_value='/mock/npm_output.txt')
@patch.object(NpmXunitTest, '_gather_evidence_from_test_report_directory_testsuite_elements')
class TestStepImplementerNpmXunitTest__run_step(
    BaseTestStepImplementerNpmXunitTest
):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=NpmXunitTest,
            step_config=step_config,
            step_name='unit-test',
            implementer='NpmXunitTest',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )
