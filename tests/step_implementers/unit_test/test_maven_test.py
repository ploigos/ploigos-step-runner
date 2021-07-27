import os
from pathlib import Path
from unittest.mock import Mock, patch

from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from ploigos_step_runner.step_implementers.unit_test import MavenTest
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


@patch("ploigos_step_runner.step_implementers.shared.MavenGeneric.__init__")
class TestStepImplementerMavenTest___init__(BaseStepImplementerTestCase):
    def test_defaults(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenTest(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None,
            maven_phases_and_goals=['test']
        )

    def test_given_environment(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenTest(
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
            maven_phases_and_goals=['test']
        )

class TestStepImplementerMavenTest_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenTest.step_implementer_config_defaults(),
            {
                'pom-file': 'pom.xml',
                'tls-verify': True,
                'maven-profiles': [],
                'maven-additional-arguments': [],
                'maven-no-transfer-progress': True,
                'fail-on-no-tests': True
            }
        )

class TestStepImplementerMavenTest__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenTest._required_config_or_result_keys(),
            [
                'pom-file',
                'fail-on-no-tests'
            ]
        )

@patch.object(MavenTest, '_run_maven_step')
@patch.object(MavenTest, 'write_working_file', return_value='/mock/mvn_output.txt')
class TestStepImplementerMavenTest__run_step(
    BaseStepImplementerTestCase
):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=MavenTest,
            step_config=step_config,
            step_name='unit-test',
            implementer='MavenTest',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    @patch.object(MavenTest, '_get_effective_pom_element', side_effect=['mock surefire element', None])
    def test_success_default_reports_dir(
        self,
        mock_effective_pom_element,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            group_id = 'com.ploigos.app'
            artifact_id = 'my-app'
            surefire_artifact_names = [
                f'{group_id}.{artifact_id}.ClassNameTest.txt',
                f'TEST-{group_id}.{artifact_id}.ClassNameTest.xml'
            ]
            def run_maven_side_effect(mvn_output_file_path):
                os.makedirs(surefire_reports_dir, exist_ok=True)

                for artifact_name in surefire_artifact_names:
                    artifact_path = os.path.join(
                        surefire_reports_dir,
                        artifact_name
                    )
                    Path(artifact_path).touch()

            mock_run_maven_step.side_effect = run_maven_side_effect

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenTest',
                sub_step_implementer_name='MavenTest'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Surefire reports generated by maven.",
                name='surefire-reports',
                value=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt'
            )

    @patch.object(
        MavenTest,
        '_get_effective_pom_element',
        side_effect=['mock surefire element', Mock(text='mock/fake/reports')]
    )
    def test_success_pom_specified_relative_reports_dir(
        self,
        mock_effective_pom_element,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'mock/fake/reports')
            group_id = 'com.ploigos.app'
            artifact_id = 'my-app'
            surefire_artifact_names = [
                f'{group_id}.{artifact_id}.ClassNameTest.txt',
                f'TEST-{group_id}.{artifact_id}.ClassNameTest.xml'
            ]
            def run_maven_side_effect(mvn_output_file_path):
                os.makedirs(surefire_reports_dir, exist_ok=True)

                for artifact_name in surefire_artifact_names:
                    artifact_path = os.path.join(
                        surefire_reports_dir,
                        artifact_name
                    )
                    Path(artifact_path).touch()

            mock_run_maven_step.side_effect = run_maven_side_effect

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenTest',
                sub_step_implementer_name='MavenTest'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Surefire reports generated by maven.",
                name='surefire-reports',
                value=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt'
            )

    @patch.object(MavenTest, '_get_effective_pom_element')
    def test_success_pom_specified_absolute_reports_dir(
        self,
        mock_effective_pom_element,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'mock-abs/fake/reports')
            mock_effective_pom_element.side_effect = [
                'mock surefire element',
                Mock(text=surefire_reports_dir)
            ]
            group_id = 'com.ploigos.app'
            artifact_id = 'my-app'
            surefire_artifact_names = [
                f'{group_id}.{artifact_id}.ClassNameTest.txt',
                f'TEST-{group_id}.{artifact_id}.ClassNameTest.xml'
            ]
            def run_maven_side_effect(mvn_output_file_path):
                os.makedirs(surefire_reports_dir, exist_ok=True)

                for artifact_name in surefire_artifact_names:
                    artifact_path = os.path.join(
                        surefire_reports_dir,
                        artifact_name
                    )
                    Path(artifact_path).touch()

            mock_run_maven_step.side_effect = run_maven_side_effect

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenTest',
                sub_step_implementer_name='MavenTest'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Surefire reports generated by maven.",
                name='surefire-reports',
                value=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt'
            )

    @patch.object(MavenTest, '_get_effective_pom_element', side_effect=[None, None])
    @patch.object(MavenTest, '_get_effective_pom', return_value='mock-effective-pom.xml')
    def test_fail_no_surefire_plugin(
        self,
        mock_effective_pom,
        mock_effective_pom_element,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            group_id = 'com.ploigos.app'
            artifact_id = 'my-app'
            surefire_artifact_names = [
                f'{group_id}.{artifact_id}.ClassNameTest.txt',
                f'TEST-{group_id}.{artifact_id}.ClassNameTest.xml'
            ]
            def run_maven_side_effect(mvn_output_file_path):
                os.makedirs(surefire_reports_dir, exist_ok=True)

                for artifact_name in surefire_artifact_names:
                    artifact_path = os.path.join(
                        surefire_reports_dir,
                        artifact_name
                    )
                    Path(artifact_path).touch()

            mock_run_maven_step.side_effect = run_maven_side_effect

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenTest',
                sub_step_implementer_name='MavenTest'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Unit test dependency "maven-surefire-plugin" ' \
                f'missing from effective pom (mock-effective-pom.xml).'

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_run_maven_step.assert_not_called()

    @patch.object(MavenTest, '_get_effective_pom_element', side_effect=['mock surefire element', None])
    def test_fail_no_tests(
        self,
        mock_effective_pom_element,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenTest',
                sub_step_implementer_name='MavenTest'
            )
            expected_step_result.success = False
            expected_step_result.message = 'No unit tests defined.'
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Surefire reports generated by maven.",
                name='surefire-reports',
                value=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt'
            )

    @patch.object(MavenTest, '_get_effective_pom_element', side_effect=['mock surefire element', None])
    def test_success_but_no_tests(
        self,
        mock_effective_pom_element,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'fail-on-no-tests': False
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenTest',
                sub_step_implementer_name='MavenTest'
            )
            expected_step_result.message = "No unit tests defined, but 'fail-on-no-tests' is False."
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Surefire reports generated by maven.",
                name='surefire-reports',
                value=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt'
            )

    @patch.object(MavenTest, '_get_effective_pom_element', side_effect=['mock surefire element', None])
    def test_fail_maven_run(
        self,
        mock_effective_pom_element,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step with mock failure
            mock_run_maven_step.side_effect = StepRunnerException('Mock error running maven')
            actual_step_result = step_implementer._run_step()

            # create expected step result
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='MavenTest',
                sub_step_implementer_name='MavenTest'
            )
            expected_step_result.success = False
            expected_step_result.message = "Error running 'maven test' to run unit tests. " \
                "More details maybe found in 'maven-output' and `surefire-reports` " \
                f"report artifact: Mock error running maven"
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.add_artifact(
                description="Surefire reports generated by maven.",
                name='surefire-reports',
                value=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt'
            )
