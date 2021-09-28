import os
from unittest.mock import patch, call

from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from ploigos_step_runner.step_implementers.shared import NpmXunitGeneric
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any


class BaseTestStepImplementerNpmXunitGeneric(
    BaseStepImplementerTestCase
):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=NpmXunitGeneric,
            step_config=step_config,
            step_name='shared',
            implementer='NpmXunitGeneric',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )


@patch("ploigos_step_runner.step_implementers.shared.NpmGeneric.__init__")
class TestStepImplementerNpmXunitGeneric___init__(BaseStepImplementerTestCase):
    def test_defaults(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        NpmXunitGeneric(
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

        NpmXunitGeneric(
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


class TestStepImplementerNpmXunitGeneric_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            NpmXunitGeneric.step_implementer_config_defaults(),
            {
                'package-file': 'package.json'
            }
        )


class TestStepImplementerNpmXunitGeneric__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            NpmXunitGeneric._required_config_or_result_keys(),
            [
                'test-reports-dir',
                'target-host-env-var-name',
                'npm-test-script'
            ]
        )


@patch.object(NpmXunitGeneric, '_run_npm_step')
@patch.object(NpmXunitGeneric, 'write_working_file', return_value='/mock/npm_output.txt')
@patch.object(NpmXunitGeneric, '_gather_evidence_from_test_report_directory_testsuite_elements')
class TestStepImplementerNpmXunitGeneric__run_step(
    BaseTestStepImplementerNpmXunitGeneric
):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=NpmXunitGeneric,
            step_config=step_config,
            step_name='shared',
            implementer='NpmXunitGeneric',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_success_with_report_dir_deployed_host_urls_list_one_entry(
        self,
        mock_gather_evidence,
        mock_write_working_file,
        mock_run_npm_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'npm-test-script': 'myscript',
                'deployed-host-urls': [
                    'https://mock.ploigos.org/mock-app-1',
                ],
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
                step_name='shared',
                sub_step_name='NpmXunitGeneric',
                sub_step_implementer_name='NpmXunitGeneric'
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
                test_report_dir='/mock/test-results-dir'
            )

            self.assertEqual(step_implementer.npm_args, ['run', 'myscript'])

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
                "target-host-env-var-name": "APP_ROUTE",
                "npm-test-script": "myscript"

            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='shared',
                sub_step_name='NpmXunitGeneric',
                sub_step_implementer_name='NpmXunitGeneric'
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
                test_report_dir='/mock/test-results-dir'
            )

            self.assertEqual(step_implementer.npm_args, ['run', 'myscript'])

    def test_success_with_report_dir_deployed_host_urls_list_multiple_entries(
        self,
        mock_gather_evidence,
        mock_write_working_file,
        mock_run_npm_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            deployed_host_urls = [
                'https://mock.ploigos.org/mock-app-1',
                'https://mock.ploigos.org/mock-app-2'
            ]
            step_config = {
                'npm-test-script': 'myscript',
                'deployed-host-urls': deployed_host_urls,
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
                step_name='shared',
                sub_step_name='NpmXunitGeneric',
                sub_step_implementer_name='NpmXunitGeneric'
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
            expected_step_result.message = f"Given more than one deployed host URL ({deployed_host_urls})," \
                f" targeting first one ({deployed_host_urls[0]}) for test."
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_npm_step.assert_called_once_with(
                npm_output_file_path='/mock/npm_output.txt',
                step_implementer_additional_envs={
                    'APP_ROUTE': 'https://mock.ploigos.org/mock-app-1'}
            )
            mock_gather_evidence.assert_called_once_with(
                step_result=Any(StepResult),
                test_report_dir='/mock/test-results-dir'
            )

    def test_success_with_report_dir_target_host_url(
        self,
        mock_gather_evidence,
        mock_write_working_file,
        mock_run_npm_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'npm-test-script': 'myscript',
                'target-host-url': 'https://mock.ploigos.org/mock-app-1',
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
                step_name='shared',
                sub_step_name='NpmXunitGeneric',
                sub_step_implementer_name='NpmXunitGeneric'
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
                test_report_dir='/mock/test-results-dir'
            )

    def test_error_in_npm(
        self,
        mock_gather_evidence,
        mock_write_working_file,
        mock_run_npm_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'npm-test-script': 'myscript',
                'deployed-host-urls': [
                    'https://mock.ploigos.org/mock-app-1',
                ],
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

            mock_run_npm_step.side_effect = StepRunnerException('mock error')

            # run test
            actual_step_result = step_implementer._run_step()

            self.assertFalse(actual_step_result.success)

            mock_run_npm_step.assert_called_once_with(
                npm_output_file_path='/mock/npm_output.txt',
                step_implementer_additional_envs={
                    'APP_ROUTE': 'https://mock.ploigos.org/mock-app-1'}
            )
            mock_gather_evidence.assert_called_once_with(
                step_result=Any(StepResult),
                test_report_dir='/mock/test-results-dir'
            )
