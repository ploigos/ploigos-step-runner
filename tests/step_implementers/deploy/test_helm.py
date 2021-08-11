import os
import re
from io import IOBase

from pathlib import Path
from unittest.mock import patch

# from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from testfixtures import TempDirectory
from ploigos_step_runner.step_implementers.deploy.helm import Helm


# @patch("ploigos_step_runner.step_implementers.deploy.Helm.__init__")
# class TestStepImplementerMavenTest___init__(BaseStepImplementerTestCase):
#     def test_defaults(self, mock_super_init):
#         workflow_result = WorkflowResult()
#         parent_work_dir_path = '/fake/path'
#         config = {
#             'helm-chart': 'chart name',
#             'helm-release': 'release name'
#         }
#
#         Helm(
#             workflow_result=workflow_result,
#             parent_work_dir_path=parent_work_dir_path,
#             config=config,
#             environment=None
#         )
#
#         mock_super_init.assert_called_once_with(
#             workflow_result,
#             parent_work_dir_path,
#             config,
#             environment=None
#         )
#
#         def test_given_environment(self, mock_super_init):
#             workflow_result = WorkflowResult()
#             parent_work_dir_path = '/fake/path'
#             config = {}
#
#             Helm(
#                 workflow_result=workflow_result,
#                 parent_work_dir_path=parent_work_dir_path,
#                 config=config,
#                 environment='mock-env'
#             )
#
#             mock_super_init.assert_called_once_with(
#                 workflow_result=workflow_result,
#                 parent_work_dir_path=parent_work_dir_path,
#                 config=config,
#                 environment='mock-env'
#             )

class TestStepImplementerDeployHelmBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            parent_work_dir_path='',
            environment=None
    ):
        return self.create_given_step_implementer(
            step_implementer=Helm,
            step_config=step_config,
            step_name='deploy',
            implementer='Helm',
            parent_work_dir_path=parent_work_dir_path,
            environment=environment
        )

class TestStepImplementerMavenTest_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            Helm.step_implementer_config_defaults(),
            {
                'helm-flags': []
            }
        )

class TestStepImplementerMavenTest__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            Helm._required_config_or_result_keys(),
            [
                'helm-chart',
                'helm-release'
            ]
        )

# @patch.object(Helm, '_run_step')
# @patch.object(Helm, 'write_working_file', return_value='/mock/helm_output.txt')
# class TestStepImplementerDeployHelm__run_step(
#     BaseStepImplementerTestCase
# ):
#     def create_step_implementer(
#             self,
#             step_config= {
#                 'helm-chart': 'mock-chart',
#                 'helm-release': 'mock-release'
#             },
#             workflow_result=None,
#             parent_work_dir_path=''
#     ):
#         return self.create_given_step_implementer(
#             step_implementer=Helm,
#             step_config=step_config,
#             step_name='deploy',
#             implementer='Helm',
#             workflow_result=workflow_result,
#             parent_work_dir_path=parent_work_dir_path
#         )

    # def test_success_single_packaged_artifact(
    #         self,
    #         mock_write_working_file,
    #         mock_run_maven_step
    # ):
    #     with TempDirectory() as test_dir:
    #         parent_work_dir_path = os.path.join(test_dir.path, 'working')
    #
    #         pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
    #         step_config = {
    #             'pom-file': pom_file
    #         }
    #         step_implementer = self.create_step_implementer(
    #             step_config=step_config,
    #             parent_work_dir_path=parent_work_dir_path,
    #         )
    #
    #         # setup sideeffects
    #         artifact_parent_dir = os.path.join(test_dir.path, 'target')
    #         package_artifact_names = [
    #             f'my-app.jar'
    #         ]
    #         def run_helm_side_effect(helm_output_file_path):
    #             os.makedirs(artifact_parent_dir, exist_ok=True)
    #             for artifact_name in package_artifact_names:
    #                 artifact_path = os.path.join(
    #                     artifact_parent_dir,
    #                     artifact_name
    #                 )
    #                 Path(artifact_path).touch()
    #
    #         mock_run_maven_step.side_effect = run_maven_side_effect
    #
    #         # run step
    #         actual_step_result = step_implementer._run_step()
    #
    #         # create expected step result
    #         expected_step_result = StepResult(
    #             step_name='deploy',
    #             sub_step_name='Helm',
    #             sub_step_implementer_name='Helm'
    #         )
    #         expected_step_result.add_artifact(
    #             description="Standard out and standard error from maven.",
    #             name='helm-output',
    #             value='/helm/mvn_output.txt'
    #         )
    #         expected_step_result.add_artifact(
    #             name='packages',
    #             value=[{
    #                 'path': os.path.join(artifact_parent_dir, 'my-app.jar')
    #             }]
    #         )
    #
    #         # verify step result
    #         self.assertEqual(
    #             actual_step_result,
    #             expected_step_result
    #         )
    #
    #         mock_write_working_file.assert_called_once()
    #         mock_run_step.assert_called_with(
    #             helm_output_file_path='/mock/helm_output.txt'
    #         )
    #
    # def test_success_multiple_packaged_artifact(
    #         self,
    #         mock_write_working_file,
    #         mock_run_maven_step
    # ):
    #     with TempDirectory() as test_dir:
    #         parent_work_dir_path = os.path.join(test_dir.path, 'working')
    #
    #         pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
    #         step_config = {
    #             'pom-file': pom_file
    #         }
    #         step_implementer = self.create_step_implementer(
    #             step_config=step_config,
    #             parent_work_dir_path=parent_work_dir_path,
    #         )
    #
    #         # setup sideeffects
    #         artifact_parent_dir = os.path.join(test_dir.path, 'target')
    #         package_artifact_names = [
    #             f'my-app.jar',
    #             f'my-app.war'
    #         ]
    #         def run_maven_side_effect(mvn_output_file_path):
    #             os.makedirs(artifact_parent_dir, exist_ok=True)
    #             for artifact_name in package_artifact_names:
    #                 artifact_path = os.path.join(
    #                     artifact_parent_dir,
    #                     artifact_name
    #                 )
    #                 Path(artifact_path).touch()
    #
    #         mock_run_maven_step.side_effect = run_maven_side_effect
    #
    #         # run step
    #         actual_step_result = step_implementer._run_step()
    #
    #         # create expected step result
    #         expected_step_result = StepResult(
    #             step_name='package',
    #             sub_step_name='MavenPackage',
    #             sub_step_implementer_name='MavenPackage'
    #         )
    #         expected_step_result.add_artifact(
    #             description="Standard out and standard error from maven.",
    #             name='maven-output',
    #             value='/mock/mvn_output.txt'
    #         )
    #         expected_step_result.add_artifact(
    #             name='packages',
    #             value=[
    #                 {
    #                     'path': os.path.join(artifact_parent_dir, 'my-app.jar')
    #                 },
    #                 {
    #                     'path': os.path.join(artifact_parent_dir, 'my-app.war')
    #                 }
    #             ]
    #         )
    #
    #         # verify step result
    #         self.assertEqual(
    #             actual_step_result,
    #             expected_step_result
    #         )
    #
    #         mock_write_working_file.assert_called_once()
    #         mock_run_maven_step.assert_called_with(
    #             mvn_output_file_path='/mock/mvn_output.txt'
    #         )
    #
    # def test_fail_maven_run(
    #         self,
    #         mock_write_working_file,
    #         mock_run_maven_step
    # ):
    #     with TempDirectory() as test_dir:
    #         parent_work_dir_path = os.path.join(test_dir.path, 'working')
    #
    #         pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
    #         step_config = {
    #             'pom-file': pom_file
    #         }
    #         step_implementer = self.create_step_implementer(
    #             step_config=step_config,
    #             parent_work_dir_path=parent_work_dir_path,
    #         )
    #
    #         # run step with mock failure
    #         mock_run_maven_step.side_effect = StepRunnerException('Mock error running maven')
    #         actual_step_result = step_implementer._run_step()
    #
    #         # create expected step result
    #         surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
    #         expected_step_result = StepResult(
    #             step_name='package',
    #             sub_step_name='MavenPackage',
    #             sub_step_implementer_name='MavenPackage'
    #         )
    #         expected_step_result.success = False
    #         expected_step_result.message = "Error running 'maven package' to package artifacts. " \
    #                                        "More details maybe found in 'maven-output' report artifact: " \
    #                                        "Mock error running maven"
    #         expected_step_result.add_artifact(
    #             description="Standard out and standard error from maven.",
    #             name='maven-output',
    #             value='/mock/mvn_output.txt'
    #         )
    #
    #         # verify step result
    #         self.assertEqual(
    #             actual_step_result,
    #             expected_step_result
    #         )
    #
    #         mock_write_working_file.assert_called_once()
    #         mock_run_maven_step.assert_called_with(
    #             mvn_output_file_path='/mock/mvn_output.txt'
    #         )
