
import os
from unittest.mock import PropertyMock, patch

from ploigos_step_runner import StepResult, WorkflowResult, StepRunnerException
from ploigos_step_runner.step_implementers.push_artifacts import MavenDeploy
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


@patch("ploigos_step_runner.step_implementers.shared.MavenGeneric.__init__")
class TestStepImplementerMavenDeploy___init__(BaseStepImplementerTestCase):
    def test_defaults(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenDeploy(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None,
            maven_phases_and_goals=['deploy']
        )

    def test_given_environment(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenDeploy(
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
            maven_phases_and_goals=['deploy']
        )

class TestStepImplementerMavenDeploy_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenDeploy.step_implementer_config_defaults(),
            {
                'pom-file': 'pom.xml',
                'tls-verify': True,
                'maven-profiles': [],
                'maven-additional-arguments': [],
                'maven-no-transfer-progress': True,
                'maven-additional-arguments': [
                    '-Dmaven.install.skip=true',
                    '-Dmaven.test.skip=true'
                    '-DskipTests',
                    '-DskipITs'
                ]
            }
        )

class TestStepImplementerMavenDeploy__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenDeploy._required_config_or_result_keys(),
            [
                'pom-file',
                'maven-push-artifact-repo-url',
                'maven-push-artifact-repo-id',
                'version'
            ]
        )

@patch('ploigos_step_runner.step_implementers.push_artifacts.maven_deploy.run_maven')
@patch.object(MavenDeploy, '_run_maven_step')
@patch.object(
    MavenDeploy,
    'write_working_file',
    side_effect=['/mock/mvn_versions_set_output.txt', '/mock/mvn_deploy_output.txt']
)
@patch.object(
    MavenDeploy,
    'maven_settings_file',
    new_callable=PropertyMock,
    return_value='/fake/settings.xml'
)
class TestStepImplementerMavenDeploy__run_step(
    BaseStepImplementerTestCase
):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=MavenDeploy,
            step_config=step_config,
            step_name='deploy',
            implementer='MavenDeploy',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_success(
        self,
        mock_settings_file,
        mock_write_working_file,
        mock_run_maven_step,
        mock_run_maven
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            maven_push_artifact_repo_id = 'mock-repo-id'
            maven_push_artifact_repo_url = 'https://mock-repo.ploigos.com'
            version = '0.42.0-mock'
            step_config = {
                'pom-file': pom_file,
                'maven-push-artifact-repo-id': maven_push_artifact_repo_id,
                'maven-push-artifact-repo-url': maven_push_artifact_repo_url,
                'version': version
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='deploy',
                sub_step_name='MavenDeploy',
                sub_step_implementer_name='MavenDeploy'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven to update version.",
                name='maven-update-version-output',
                value='/mock/mvn_versions_set_output.txt'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven to " \
                    "push artifacts to repository.",
                name='maven-push-artifacts-output',
                value='/mock/mvn_deploy_output.txt'
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called()
            mock_run_maven.assert_called_with(
                mvn_output_file_path='/mock/mvn_versions_set_output.txt',
                settings_file='/fake/settings.xml',
                pom_file=pom_file,
                phases_and_goals=['versions:set'],
                additional_arguments=[
                    f'-DnewVersion={version}'
                ]
            )
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_deploy_output.txt',
                step_implementer_additional_arguments=[
                    '-DaltDeploymentRepository=' \
                    f'{maven_push_artifact_repo_id}::default::{maven_push_artifact_repo_url}'
                ]
            )

    def test_fail_set_version(
        self,
        mock_settings_file,
        mock_write_working_file,
        mock_run_maven_step,
        mock_run_maven
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            maven_push_artifact_repo_id = 'mock-repo-id'
            maven_push_artifact_repo_url = 'https://mock-repo.ploigos.com'
            version = '0.42.0-mock'
            step_config = {
                'pom-file': pom_file,
                'maven-push-artifact-repo-id': maven_push_artifact_repo_id,
                'maven-push-artifact-repo-url': maven_push_artifact_repo_url,
                'version': version
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step with mvn version:set failure
            mock_run_maven.side_effect = StepRunnerException('mock error setting new pom version')
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='deploy',
                sub_step_name='MavenDeploy',
                sub_step_implementer_name='MavenDeploy'
            )
            expected_step_result.success = False
            expected_step_result.message = "Error running 'maven deploy' to push artifacts. " \
                "More details maybe found in 'maven-output' report artifact: " \
                "mock error setting new pom version"
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven to update version.",
                name='maven-update-version-output',
                value='/mock/mvn_versions_set_output.txt'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven to " \
                    "push artifacts to repository.",
                name='maven-push-artifacts-output',
                value='/mock/mvn_deploy_output.txt'
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called()
            mock_run_maven.assert_called_with(
                mvn_output_file_path='/mock/mvn_versions_set_output.txt',
                settings_file='/fake/settings.xml',
                pom_file=pom_file,
                phases_and_goals=['versions:set'],
                additional_arguments=[
                    f'-DnewVersion={version}'
                ]
            )
            mock_run_maven_step.assert_not_called()

    def test_fail_mvn_depoy(
        self,
        mock_settings_file,
        mock_write_working_file,
        mock_run_maven_step,
        mock_run_maven
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            maven_push_artifact_repo_id = 'mock-repo-id'
            maven_push_artifact_repo_url = 'https://mock-repo.ploigos.com'
            version = '0.42.0-mock'
            step_config = {
                'pom-file': pom_file,
                'maven-push-artifact-repo-id': maven_push_artifact_repo_id,
                'maven-push-artifact-repo-url': maven_push_artifact_repo_url,
                'version': version
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step with mvn deploy failure
            mock_run_maven_step.side_effect = StepRunnerException('mock error running mvn deploy')
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='deploy',
                sub_step_name='MavenDeploy',
                sub_step_implementer_name='MavenDeploy'
            )
            expected_step_result.success = False
            expected_step_result.message = "Error running 'maven deploy' to push artifacts. " \
                "More details maybe found in 'maven-output' report artifact: " \
                "mock error running mvn deploy"
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven to update version.",
                name='maven-update-version-output',
                value='/mock/mvn_versions_set_output.txt'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven to " \
                    "push artifacts to repository.",
                name='maven-push-artifacts-output',
                value='/mock/mvn_deploy_output.txt'
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called()
            mock_run_maven.assert_called_with(
                mvn_output_file_path='/mock/mvn_versions_set_output.txt',
                settings_file='/fake/settings.xml',
                pom_file=pom_file,
                phases_and_goals=['versions:set'],
                additional_arguments=[
                    f'-DnewVersion={version}'
                ]
            )
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_deploy_output.txt',
                step_implementer_additional_arguments=[
                    '-DaltDeploymentRepository=' \
                    f'{maven_push_artifact_repo_id}::default::{maven_push_artifact_repo_url}'
                ]
            )
