import os
from pathlib import Path
from unittest.mock import patch

from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from ploigos_step_runner.step_implementers.create_container_image import MavenJKubeK8sBuild
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


@patch("ploigos_step_runner.step_implementers.shared.MavenGeneric.__init__")
class TestStepImplementerMavenJKubeK8sBuild___init__(BaseStepImplementerTestCase):
    def test_defaults(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenJKubeK8sBuild(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None,
            maven_phases_and_goals=['k8s:build']
        )

    def test_given_environment(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenJKubeK8sBuild(
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
            maven_phases_and_goals=['k8s:build']
        )

class TestStepImplementerMavenJKubeK8sBuild_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenJKubeK8sBuild.step_implementer_config_defaults(),
            {
                'pom-file': 'pom.xml',
                'tls-verify': True,
                'maven-profiles': [],
                'maven-additional-arguments': [],
                'maven-no-transfer-progress': True,
                'maven-additional-arguments': [
                    '-Dmaven.install.skip=true',
                    '-Dmaven.test.skip=true'
                ]
            }
        )

class TestStepImplementerMavenJKubeK8sBuild__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenJKubeK8sBuild._required_config_or_result_keys(),
            [
                'pom-file'
            ]
        )

@patch('ploigos_step_runner.step_implementers.create_container_image.maven_jkube_k8sbuild.determine_container_image_build_tag_info')
@patch.object(MavenJKubeK8sBuild, '_run_maven_step')
@patch.object(
    MavenJKubeK8sBuild,
    'write_working_file',
    return_value='/mock/mvn_k8s_build_output.txt'
)
class TestStepImplementerMavenJKubeK8sBuild__run_step(
    BaseStepImplementerTestCase
):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=MavenJKubeK8sBuild,
            step_config=step_config,
            step_name='create-container-image',
            implementer='MavenJKubeK8sBuild',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_success_given_version(
        self,
        mock_write_working_file,
        mock_run_maven_step,
        mock_determine_container_image_build_tag_info
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app',
                'container-image-version': '1.0-123abc'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            artifact_parent_dir = os.path.join(test_dir.path, 'target')
            package_artifact_names = [
                f'my-app.jar'
            ]
            def run_maven_side_effect(mvn_output_file_path, step_implementer_additional_arguments):
                os.makedirs(artifact_parent_dir, exist_ok=True)
                for artifact_name in package_artifact_names:
                    artifact_path = os.path.join(
                        artifact_parent_dir,
                        artifact_name
                    )
                    Path(artifact_path).touch()
            mock_run_maven_step.side_effect = run_maven_side_effect

            mock_determine_container_image_build_tag_info.return_value=[
                'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                'mock-org/mock-app-mock-service:1.0-123abc',
                'localhost',
                'mock-app-mock-service',
                '1.0-123abc'
            ]

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='MavenJKubeK8sBuild',
                sub_step_implementer_name='MavenJKubeK8sBuild'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven to " \
                    "create container image.",
                name='maven-jkube-output',
                value='/mock/mvn_k8s_build_output.txt'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='localhost',
                description='Registry URI poriton of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='mock-org',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='mock-app-mock-service',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='mock-app-mock-service',
                description='Another way to reference the' \
                    ' repository portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='1.0-123abc',
                description='Version portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='localhost/mock-org/mock-app-mock-service:1.0-123abc',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='mock-org/mock-app-mock-service:1.0-123abc',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_k8s_build_output.txt',
                step_implementer_additional_arguments=[
                    '-Djkube.generator.name=localhost/mock-org/mock-app-mock-service:1.0-123abc'
                ]
            )
            mock_determine_container_image_build_tag_info.assert_called_once_with(
                image_version='1.0-123abc',
                organization='mock-org',
                application_name='mock-app',
                service_name='mock-service'
            )

    def test_success_default_version(
        self,
        mock_write_working_file,
        mock_run_maven_step,
        mock_determine_container_image_build_tag_info
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            artifact_parent_dir = os.path.join(test_dir.path, 'target')
            package_artifact_names = [
                f'my-app.jar'
            ]
            def run_maven_side_effect(mvn_output_file_path, step_implementer_additional_arguments):
                os.makedirs(artifact_parent_dir, exist_ok=True)
                for artifact_name in package_artifact_names:
                    artifact_path = os.path.join(
                        artifact_parent_dir,
                        artifact_name
                    )
                    Path(artifact_path).touch()
            mock_run_maven_step.side_effect = run_maven_side_effect

            mock_determine_container_image_build_tag_info.return_value=[
                'localhost/mock-org/mock-app-mock-service:mock-default-version',
                'mock-org/mock-app-mock-service:mock-default-version',
                'localhost',
                'mock-app-mock-service',
                'mock-default-version'
            ]

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='MavenJKubeK8sBuild',
                sub_step_implementer_name='MavenJKubeK8sBuild'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven to " \
                    "create container image.",
                name='maven-jkube-output',
                value='/mock/mvn_k8s_build_output.txt'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='localhost',
                description='Registry URI poriton of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='mock-org',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='mock-app-mock-service',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='mock-app-mock-service',
                description='Another way to reference the' \
                    ' repository portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='mock-default-version',
                description='Version portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='localhost/mock-org/mock-app-mock-service:mock-default-version',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='mock-org/mock-app-mock-service:mock-default-version',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_k8s_build_output.txt',
                step_implementer_additional_arguments=[
                    '-Djkube.generator.name=localhost/mock-org/mock-app-mock-service:mock-default-version'
                ]
            )
            mock_determine_container_image_build_tag_info.assert_called_once_with(
                image_version=None,
                organization='mock-org',
                application_name='mock-app',
                service_name='mock-service'
            )

    def test_fail_maven_run(
        self,
        mock_write_working_file,
        mock_run_maven_step,
        mock_determine_container_image_build_tag_info
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            step_config = {
                'pom-file': pom_file,
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app',
                'container-image-version': '1.0-123abc',
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # set up mocks
            mock_determine_container_image_build_tag_info.return_value=[
                'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                'mock-org/mock-app-mock-service:1.0-123abc',
                'localhost',
                'mock-app-mock-service',
                '1.0-123abc'
            ]

            # run step with mock failure
            mock_run_maven_step.side_effect = StepRunnerException('Mock error running maven')
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='MavenJKubeK8sBuild',
                sub_step_implementer_name='MavenJKubeK8sBuild'
            )
            expected_step_result.success = False
            expected_step_result.message = \
                "Error running 'maven k8s:build' to create container image. " \
                "More details maybe found in 'maven-jkube-output' report artifact: " \
                "Mock error running maven"
            expected_step_result.add_artifact(
                description="Standard out and standard error from running maven to " \
                    "create container image.",
                name='maven-jkube-output',
                value='/mock/mvn_k8s_build_output.txt'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='localhost',
                description='Registry URI poriton of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='mock-org',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='mock-app-mock-service',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='mock-app-mock-service',
                description='Another way to reference the' \
                    ' repository portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='1.0-123abc',
                description='Version portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='localhost/mock-org/mock-app-mock-service:1.0-123abc',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='mock-org/mock-app-mock-service:1.0-123abc',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/mvn_k8s_build_output.txt',
                step_implementer_additional_arguments=[
                    '-Djkube.generator.name=localhost/mock-org/mock-app-mock-service:1.0-123abc'
                ]
            )
            mock_determine_container_image_build_tag_info.assert_called_once_with(
                image_version='1.0-123abc',
                organization='mock-org',
                application_name='mock-app',
                service_name='mock-service'
            )
