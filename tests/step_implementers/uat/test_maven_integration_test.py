import os
from unittest.mock import patch, call

from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from ploigos_step_runner.step_implementers.uat import MavenIntegrationTest
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any

class BaseTestStepImplementerMavenIntegrationTest(
    BaseStepImplementerTestCase
):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=MavenIntegrationTest,
            step_config=step_config,
            step_name='unit-test',
            implementer='MavenIntegrationTest',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

@patch("ploigos_step_runner.step_implementers.shared.MavenGeneric.__init__")
class TestStepImplementerMavenIntegrationTest___init__(BaseStepImplementerTestCase):
    def test_defaults(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenIntegrationTest(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None,
            maven_phases_and_goals=['integration-test', 'verify']
        )

    def test_given_environment(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenIntegrationTest(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='mock-env'
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='mock-env',
            maven_phases_and_goals=['integration-test', 'verify']
        )

class TestStepImplementerMavenIntegrationTest_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenIntegrationTest.step_implementer_config_defaults(),
            {
                'pom-file': 'pom.xml',
                'tls-verify': True,
                'maven-profiles': [],
                'maven-additional-arguments': ['-DskipTests'],
                'maven-no-transfer-progress': True
            }
        )

class TestStepImplementerMavenIntegrationTest__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenIntegrationTest._required_config_or_result_keys(),
            [
                'pom-file',
                'target-host-url-maven-argument-name'
            ]
        )

@patch.object(MavenIntegrationTest, '_run_maven_step')
@patch.object(MavenIntegrationTest, 'write_working_file', return_value='/mock/mvn_output.txt')
@patch.object(MavenIntegrationTest, '_MavenIntegrationTest__get_test_report_dir', return_value='/mock/test-results-dir')
@patch.object(MavenIntegrationTest, '_gather_evidence_from_test_report_directory_testsuite_elements')
class TestStepImplementerMavenIntegrationTest__run_step(
    BaseTestStepImplementerMavenIntegrationTest
):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=MavenIntegrationTest,
            step_config=step_config,
            step_name='unit-test',
            implementer='MavenIntegrationTest',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_success_with_report_dir_deployed_host_urls_list_one_entry(
        self,
        mock_gather_evidence,
        mock_get_test_report_dir,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'target-host-url-maven-argument-name': 'mock.target-host-url-param',
                'deployed-host-urls': [
                    'https://mock.ploigos.org/mock-app-1'
                ]
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
                sub_step_name='MavenIntegrationTest',
                sub_step_implementer_name='MavenIntegrationTest'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Test report generated when running unit tests.",
                name='test-report',
                value='/mock/test-results-dir'
            )
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    '-Dmock.target-host-url-param=https://mock.ploigos.org/mock-app-1'
                ]
            )
            mock_gather_evidence.assert_called_once_with(
                step_result=Any(StepResult),
                test_report_dir='/mock/test-results-dir'
            )

    def test_success_with_report_dir_deployed_host_urls_list_multiple_entries(
        self,
        mock_gather_evidence,
        mock_get_test_report_dir,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'target-host-url-maven-argument-name': 'mock.target-host-url-param',
                'deployed-host-urls': [
                    'https://mock.ploigos.org/mock-app-1',
                    'https://mock.ploigos.org/mock-app-2'
                ]
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
                sub_step_name='MavenIntegrationTest',
                sub_step_implementer_name='MavenIntegrationTest'
            )
            expected_step_result.message = \
                f"Given more then one deployed host URL ({step_config['deployed-host-urls']})," \
                f" targeting first one (https://mock.ploigos.org/mock-app-1) for user acceptance test (UAT)."
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Test report generated when running unit tests.",
                name='test-report',
                value='/mock/test-results-dir'
            )
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    '-Dmock.target-host-url-param=https://mock.ploigos.org/mock-app-1'
                ]
            )
            mock_gather_evidence.assert_called_once_with(
                step_result=Any(StepResult),
                test_report_dir='/mock/test-results-dir'
            )

    def test_success_with_report_dir_deployed_host_urls_single(
        self,
        mock_gather_evidence,
        mock_get_test_report_dir,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'target-host-url-maven-argument-name': 'mock.target-host-url-param',
                'deployed-host-urls': 'https://mock.ploigos.org/mock-app-1'
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
                sub_step_name='MavenIntegrationTest',
                sub_step_implementer_name='MavenIntegrationTest'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Test report generated when running unit tests.",
                name='test-report',
                value='/mock/test-results-dir'
            )
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    '-Dmock.target-host-url-param=https://mock.ploigos.org/mock-app-1'
                ]
            )
            mock_gather_evidence.assert_called_once_with(
                step_result=Any(StepResult),
                test_report_dir='/mock/test-results-dir'
            )

    def test_success_with_report_dir_target_host_url(
        self,
        mock_gather_evidence,
        mock_get_test_report_dir,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'target-host-url-maven-argument-name': 'mock.target-host-url-param',
                'target-host-url': 'https://mock.ploigos.org/mock-app-1'
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
                sub_step_name='MavenIntegrationTest',
                sub_step_implementer_name='MavenIntegrationTest'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Test report generated when running unit tests.",
                name='test-report',
                value='/mock/test-results-dir'
            )
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    '-Dmock.target-host-url-param=https://mock.ploigos.org/mock-app-1'
                ]
            )
            mock_gather_evidence.assert_called_once_with(
                step_result=Any(StepResult),
                test_report_dir='/mock/test-results-dir'
            )

    def test_success_no_report_dir_deployed_host_urls_list_one_entry(
        self,
        mock_gather_evidence,
        mock_get_test_report_dir,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'target-host-url-maven-argument-name': 'mock.target-host-url-param',
                'deployed-host-urls': [
                    'https://mock.ploigos.org/mock-app-1'
                ]
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup mocks
            mock_get_test_report_dir.return_value = None

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenIntegrationTest',
                sub_step_implementer_name='MavenIntegrationTest'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    '-Dmock.target-host-url-param=https://mock.ploigos.org/mock-app-1'
                ]
            )
            mock_gather_evidence.asssert_not_called()

    def test_fail_with_report_dir(
        self,
        mock_gather_evidence,
        mock_get_test_report_dir,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'target-host-url-maven-argument-name': 'mock.target-host-url-param',
                'deployed-host-urls': [
                    'https://mock.ploigos.org/mock-app-1'
                ]
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup mocks
            mock_run_maven_step.side_effect = StepRunnerException('mock error')

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenIntegrationTest',
                sub_step_implementer_name='MavenIntegrationTest'
            )
            expected_step_result.success = False
            expected_step_result.message = "Error running maven. " \
                "More details maybe found in report artifacts: " \
                "mock error"
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Test report generated when running unit tests.",
                name='test-report',
                value='/mock/test-results-dir'
            )
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    '-Dmock.target-host-url-param=https://mock.ploigos.org/mock-app-1'
                ]
            )
            mock_gather_evidence.assert_called_once_with(
                step_result=Any(StepResult),
                test_report_dir='/mock/test-results-dir'
            )

    def test_fail_no_report_dir(
        self,
        mock_gather_evidence,
        mock_get_test_report_dir,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'target-host-url-maven-argument-name': 'mock.target-host-url-param',
                'deployed-host-urls': [
                    'https://mock.ploigos.org/mock-app-1'
                ]
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup mocks
            mock_run_maven_step.side_effect = StepRunnerException('mock error')
            mock_get_test_report_dir.return_value = None

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenIntegrationTest',
                sub_step_implementer_name='MavenIntegrationTest'
            )
            expected_step_result.success = False
            expected_step_result.message = "Error running maven. " \
                "More details maybe found in report artifacts: " \
                "mock error"
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    '-Dmock.target-host-url-param=https://mock.ploigos.org/mock-app-1'
                ]
            )
            mock_gather_evidence.assert_not_called()

@patch.object(MavenIntegrationTest, '_attempt_get_test_report_directory')
class TestStepImplementerMavenIntegrationTest___get_test_report_dir(
    BaseTestStepImplementerMavenIntegrationTest
):
    def test_user_given_test_reports_dir(self, mock_attempt_get_test_report_directory):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'test-reports-dir': '/mock/user-given/test-reports-dir'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            actual_test_report_dir = step_implementer._MavenIntegrationTest__get_test_report_dir()

            # verify results
            self.assertEqual(actual_test_report_dir, '/mock/user-given/test-reports-dir')
            mock_attempt_get_test_report_directory.assert_not_called()

    def test_dynamically_determined_test_reports_dir_failsafe(self, mock_attempt_get_test_report_directory):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup mocks
            mock_attempt_get_test_report_directory.return_value = \
                '/mock/dynamically-determined/failsafe/test-reports-dir'

            # run test
            actual_test_report_dir = step_implementer._MavenIntegrationTest__get_test_report_dir()

            # verify results
            self.assertEqual(
                actual_test_report_dir,
                '/mock/dynamically-determined/failsafe/test-reports-dir'
            )
            mock_attempt_get_test_report_directory.assert_called_once_with(
                plugin_name='maven-failsafe-plugin',
                configuration_key='reportsDirectory',
                default='target/failsafe-reports'
            )

    def test_dynamically_determined_test_reports_dir_surefire(self, mock_attempt_get_test_report_directory):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup mocks
            mock_attempt_get_test_report_directory.side_effect = [
                StepRunnerException('mock error getting failsafe plugin'),
                '/mock/dynamically-determined/surefire/test-reports-dir'
            ]

            # run test
            actual_test_report_dir = step_implementer._MavenIntegrationTest__get_test_report_dir()

            # verify results
            self.assertEqual(
                actual_test_report_dir,
                '/mock/dynamically-determined/surefire/test-reports-dir'
            )
            mock_attempt_get_test_report_directory.assert_has_calls([
                call(
                    plugin_name='maven-failsafe-plugin',
                    configuration_key='reportsDirectory',
                    default='target/failsafe-reports'
                ),
                call(
                    plugin_name='maven-surefire-plugin',
                    configuration_key='reportsDirectory',
                    default='target/surefire-reports',
                    require_phase_execution_config=True
                )
            ])

    def test_dynamically_determined_test_reports_dir_errors(self, mock_attempt_get_test_report_directory):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup mocks
            mock_attempt_get_test_report_directory.side_effect = StepRunnerException('mock error')

            # run test
            actual_test_report_dir = step_implementer._MavenIntegrationTest__get_test_report_dir()

            # verify results
            self.assertEqual(actual_test_report_dir, None)
            mock_attempt_get_test_report_directory.assert_has_calls([
                call(
                    plugin_name='maven-failsafe-plugin',
                    configuration_key='reportsDirectory',
                    default='target/failsafe-reports'
                ),
                call(
                    plugin_name='maven-surefire-plugin',
                    configuration_key='reportsDirectory',
                    default='target/surefire-reports',
                    require_phase_execution_config=True
                )
            ])
