import os
from unittest.mock import patch, call

from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from ploigos_step_runner.step_implementers.uat import NpmXunitIntegrationTest
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any


class BaseTestStepImplementerNpmXunitIntegrationTest(
    BaseStepImplementerTestCase
):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=NpmXunitIntegrationTest,
            step_config=step_config,
            step_name='unit-test',
            implementer='NpmXunitIntegrationTest',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )


@patch("ploigos_step_runner.step_implementers.shared.NpmGeneric.__init__")
class TestStepImplementerNpmXunitIntegrationTest___init__(BaseStepImplementerTestCase):
    def test_defaults(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        NpmXunitIntegrationTest(
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

        NpmXunitIntegrationTest(
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


class TestStepImplementerNpmXunitIntegrationTest_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            NpmXunitIntegrationTest.step_implementer_config_defaults(),
            {
                'package-file': 'package.json',
                'npm-test-script': 'test:uat'
            }
        )


class TestStepImplementerNpmXunitIntegrationTest__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            NpmXunitIntegrationTest._required_config_or_result_keys(),
            [
                'test-reports-dir',
                'target-host-env-var-name'
            ]
        )


@patch.object(NpmXunitIntegrationTest, '_run_npm_step')
@patch.object(NpmXunitIntegrationTest, 'write_working_file', return_value='/mock/npm_output.txt')
@patch.object(NpmXunitIntegrationTest, '_gather_evidence_from_test_report_directory_testsuite_elements')
class TestStepImplementerNpmXunitIntegrationTest__run_step(
    BaseTestStepImplementerNpmXunitIntegrationTest
):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=NpmXunitIntegrationTest,
            step_config=step_config,
            step_name='unit-test',
            implementer='NpmXunitIntegrationTest',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_success_with_report_dir_deployed_host_urls_not_list(
        self,
        mock_gather_evidence,
        mock_write_working_file,
        mock_run_npm_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'deployed-host-urls': 'https://mock.ploigos.org/mock-app-1',
                'npm-envs':
                {
                    'VAR1': 'VAL1',
                    'VAR2': 'VAL2'
                },
                'test-reports-dir': '/mock/test-results-dir',
                "target-host-env-var-name": "APP_ROUTE"

            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='NpmXunitIntegrationTest',
                sub_step_implementer_name='NpmXunitIntegrationTest'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from npm.",
                name='npm-output',
                value='/mock/npm_output.txt'
            )
            expected_step_result.add_artifact(
                description="Test report generated when running tests.",
                name='test-report',
                value='/mock/test-results-dir'
            )
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_npm_step.assert_called_once_with(
                npm_output_file_path='/mock/npm_output.txt',
                step_implementer_additional_envs={
                    'APP_ROUTE': 'https://mock.ploigos.org/mock-app-1'}
            )
            mock_gather_evidence.assert_called_once_with(
                step_result=Any(StepResult),
                test_report_dirs='/mock/test-results-dir'
            )

            self.assertEqual(step_implementer.npm_args, ['run', 'test:uat'])
