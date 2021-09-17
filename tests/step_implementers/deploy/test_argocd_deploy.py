import os
import re
from io import IOBase
from unittest.mock import call, patch
from testfixtures import TempDirectory
from ploigos_step_runner import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.step_implementers.shared.argocd_generic import ArgoCDGeneric
from ploigos_step_runner.step_implementers.deploy.argocd_deploy import ArgoCDDeploy

class TestStepImplementerDeployArgoCDBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            parent_work_dir_path='',
            environment=None
    ):
        return self.create_given_step_implementer(
            step_implementer=ArgoCDDeploy,
            step_config=step_config,
            step_name='deploy',
            implementer='ArgoCDDeploy',
            parent_work_dir_path=parent_work_dir_path,
            environment=environment
        )


# NOTE:
#   Could definitely do some more negative testing of _run_step testing what happens when each
#   and every mocked function throws an error (that can throw an error)
class TestStepImplementerSharedArgoCDDeploy_run_step(TestStepImplementerDeployArgoCDBase):
    @patch.object(
        ArgoCDDeploy,
        '_argocd_get_app_manifest',
        return_value='/does/not/matter/manifest.yaml'
    )
    @patch.object(ArgoCDDeploy, '_get_app_name', return_value='test-app-name')
    @patch.object(ArgoCDDeploy, '_update_yaml_file_value')
    @patch.object(ArgoCDDeploy, '_get_deployment_config_repo_tag', return_value='v0.42.0')
    @patch.object(ArgoCDDeploy, '_git_tag_and_push_deployment_config_repo')
    @patch.object(ArgoCDDeploy, '_argocd_add_target_cluster')
    @patch.object(ArgoCDGeneric, '_clone_repo', return_value='/does/not/matter')
    @patch.object(ArgoCDGeneric, '_git_commit_file')
    @patch.object(ArgoCDGeneric, '_argocd_sign_in')
    @patch.object(ArgoCDGeneric, '_argocd_app_create_or_update')
    @patch.object(ArgoCDGeneric, '_argocd_app_sync')
    @patch.object(
        ArgoCDGeneric,
        '_get_deployed_host_urls',
        return_value=['https://fruits.ploigos.xyz']
    )
    @patch.object(
        ArgoCDDeploy,
        '_get_deployment_config_helm_chart_environment_values_file',
        return_value='values-PROD.yaml'
    )
    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/test')
    def test_run_step_success(
            self,
            get_repo_branch_mock,
            get_deployment_config_helm_chart_environment_values_file_mock,
            get_deployed_host_urls_mock,
            argocd_app_sync_mock,
            argocd_app_create_or_update_mock,
            argocd_sign_in_mock,
            git_commit_file_mock,
            clone_repo_mock,
            argocd_add_target_cluster_mock,
            git_tag_and_push_deployment_config_repo_mock,
            get_deployment_config_repo_tag_mock,
            update_yaml_file_value_mock,
            get_app_name_mock,
            argocd_get_app_manifest_mock
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'deployment-config-repo': 'https://git.ploigos.xyz/foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'container-image-tag': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )

            actual_step_results = step_implementer._run_step()
            expected_step_result = StepResult(
                step_name='deploy',
                sub_step_name='ArgoCDDeploy',
                sub_step_implementer_name='ArgoCDDeploy',
                environment='PROD'
            )
            expected_step_result.add_artifact(
                name='argocd-app-name',
                value='test-app-name'
            )
            expected_step_result.add_artifact(
                name='config-repo-git-tag',
                value='v0.42.0'
            )
            expected_step_result.add_artifact(
                name='argocd-deployed-manifest',
                value='/does/not/matter/manifest.yaml'
            )
            expected_step_result.add_artifact(
                name='deployed-host-urls',
                value=['https://fruits.ploigos.xyz']
            )
            self.assertEqual(actual_step_results, expected_step_result)

            get_repo_branch_mock.assert_called_once_with()
            get_deployment_config_helm_chart_environment_values_file_mock.assert_called_once_with()
            get_app_name_mock.assert_called_once_with()
            deployment_config_repo_dir = os.path.join(
                step_implementer.work_dir_path,
                'deployment-config-repo'
            )
            clone_repo_mock.assert_called_once_with(
                repo_dir=deployment_config_repo_dir,
                repo_url=step_config['deployment-config-repo'],
                repo_branch='feature/test',
                git_email=step_config['git-email'],
                git_name=step_config['git-name'],
                username=None,
                password=None
            )
            update_yaml_file_value_mock.assert_called_once_with(
                file='/does/not/matter/charts/foo/values-PROD.yaml',
                yq_path=step_config['deployment-config-helm-chart-values-file-image-tag-yq-path'],
                value=step_config['container-image-tag']
            )
            git_commit_file_mock.assert_called_once_with(
                git_commit_message='Updating values for deployment to PROD',
                file_path='charts/foo/values-PROD.yaml',
                repo_dir='/does/not/matter'
            )
            get_deployment_config_repo_tag_mock.assert_called_once_with()
            git_tag_and_push_deployment_config_repo_mock.assert_called_once_with(
                deployment_config_repo=step_config['deployment-config-repo'],
                deployment_config_repo_dir='/does/not/matter',
                deployment_config_repo_tag='v0.42.0',
                force_push_tags=False
            )
            argocd_sign_in_mock.assert_called_once_with(
                argocd_api=step_config['argocd-api'],
                username=step_config['argocd-username'],
                password=step_config['argocd-password'],
                insecure=step_config['argocd-skip-tls']
            )
            argocd_add_target_cluster_mock.assert_called_once_with(
                kube_api='https://kubernetes.default.svc',
                kube_api_token=None,
                kube_api_skip_tls=False
            )
            argocd_app_create_or_update_mock.assert_called_once_with(
                argocd_app_name='test-app-name',
                repo=step_config['deployment-config-repo'],
                revision='v0.42.0',
                path=step_config['deployment-config-helm-chart-path'],
                dest_server='https://kubernetes.default.svc',
                auto_sync=True,
                values_files=['values-PROD.yaml']
            )
            argocd_app_sync_mock.assert_called_once_with(
                argocd_app_name='test-app-name',
                argocd_sync_timeout_seconds=60,
                argocd_sync_retry_limit=3,
                argocd_sync_prune=True
            )
            argocd_get_app_manifest_mock.assert_called_once_with(
                argocd_app_name='test-app-name'
            )
            get_deployed_host_urls_mock.assert_called_once_with(
                manifest_path='/does/not/matter/manifest.yaml'
            )

    @patch.object(
        ArgoCDDeploy,
        '_argocd_get_app_manifest',
        return_value='/does/not/matter/manifest.yaml'
    )
    @patch.object(ArgoCDDeploy, '_get_app_name', return_value='test-app-name')
    @patch.object(ArgoCDDeploy, '_update_yaml_file_value')
    @patch.object(ArgoCDDeploy, '_get_deployment_config_repo_tag', return_value='v0.42.0')
    @patch.object(ArgoCDDeploy, '_git_tag_and_push_deployment_config_repo')
    @patch.object(ArgoCDDeploy, '_argocd_add_target_cluster')
    @patch.object(ArgoCDGeneric, '_clone_repo', return_value='/does/not/matter')
    @patch.object(ArgoCDGeneric, '_git_commit_file')
    @patch.object(ArgoCDGeneric, '_argocd_sign_in')
    @patch.object(ArgoCDGeneric, '_argocd_app_create_or_update')
    @patch.object(ArgoCDGeneric, '_argocd_app_sync')
    @patch.object(
        ArgoCDGeneric,
        '_get_deployed_host_urls',
        return_value=['https://fruits.ploigos.xyz']
    )
    @patch.object(
        ArgoCDDeploy,
        '_get_deployment_config_helm_chart_environment_values_file',
        return_value='values-PROD.yaml'
    )
    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/test')
    def test_run_step_success_no_prune(
            self,
            get_repo_branch_mock,
            get_deployment_config_helm_chart_environment_values_file_mock,
            get_deployed_host_urls_mock,
            argocd_app_sync_mock,
            argocd_app_create_or_update_mock,
            argocd_sign_in_mock,
            git_commit_file_mock,
            clone_repo_mock,
            argocd_add_target_cluster_mock,
            git_tag_and_push_deployment_config_repo_mock,
            get_deployment_config_repo_tag_mock,
            update_yaml_file_value_mock,
            get_app_name_mock,
            argocd_get_app_manifest_mock
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'argocd-sync-prune': False,
                'deployment-config-repo': 'https://git.ploigos.xyz/foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'container-image-tag': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )

            actual_step_results = step_implementer._run_step()
            expected_step_result = StepResult(
                step_name='deploy',
                sub_step_name='ArgoCDDeploy',
                sub_step_implementer_name='ArgoCDDeploy',
                environment='PROD'
            )
            expected_step_result.add_artifact(
                name='argocd-app-name',
                value='test-app-name'
            )
            expected_step_result.add_artifact(
                name='config-repo-git-tag',
                value='v0.42.0'
            )
            expected_step_result.add_artifact(
                name='argocd-deployed-manifest',
                value='/does/not/matter/manifest.yaml'
            )
            expected_step_result.add_artifact(
                name='deployed-host-urls',
                value=['https://fruits.ploigos.xyz']
            )
            self.assertEqual(actual_step_results, expected_step_result)

            get_repo_branch_mock.assert_called_once_with()
            get_deployment_config_helm_chart_environment_values_file_mock.assert_called_once_with()
            get_app_name_mock.assert_called_once_with()
            deployment_config_repo_dir = os.path.join(
                step_implementer.work_dir_path,
                'deployment-config-repo'
            )
            clone_repo_mock.assert_called_once_with(
                repo_dir=deployment_config_repo_dir,
                repo_url=step_config['deployment-config-repo'],
                repo_branch='feature/test',
                git_email=step_config['git-email'],
                git_name=step_config['git-name'],
                username=None,
                password=None
            )
            update_yaml_file_value_mock.assert_called_once_with(
                file='/does/not/matter/charts/foo/values-PROD.yaml',
                yq_path=step_config['deployment-config-helm-chart-values-file-image-tag-yq-path'],
                value=step_config['container-image-tag']
            )
            git_commit_file_mock.assert_called_once_with(
                git_commit_message='Updating values for deployment to PROD',
                file_path='charts/foo/values-PROD.yaml',
                repo_dir='/does/not/matter'
            )
            get_deployment_config_repo_tag_mock.assert_called_once_with()
            git_tag_and_push_deployment_config_repo_mock.assert_called_once_with(
                deployment_config_repo=step_config['deployment-config-repo'],
                deployment_config_repo_dir='/does/not/matter',
                deployment_config_repo_tag='v0.42.0',
                force_push_tags=False
            )
            argocd_sign_in_mock.assert_called_once_with(
                argocd_api=step_config['argocd-api'],
                username=step_config['argocd-username'],
                password=step_config['argocd-password'],
                insecure=step_config['argocd-skip-tls']
            )
            argocd_add_target_cluster_mock.assert_called_once_with(
                kube_api='https://kubernetes.default.svc',
                kube_api_token=None,
                kube_api_skip_tls=False
            )
            argocd_app_create_or_update_mock.assert_called_once_with(
                argocd_app_name='test-app-name',
                repo=step_config['deployment-config-repo'],
                revision='v0.42.0',
                path=step_config['deployment-config-helm-chart-path'],
                dest_server='https://kubernetes.default.svc',
                auto_sync=True,
                values_files=['values-PROD.yaml']
            )
            argocd_app_sync_mock.assert_called_once_with(
                argocd_app_name='test-app-name',
                argocd_sync_timeout_seconds=60,
                argocd_sync_retry_limit=3,
                argocd_sync_prune=False
            )
            argocd_get_app_manifest_mock.assert_called_once_with(
                argocd_app_name='test-app-name'
            )
            get_deployed_host_urls_mock.assert_called_once_with(
                manifest_path='/does/not/matter/manifest.yaml'
            )

    @patch.object(
        ArgoCDDeploy,
        '_argocd_get_app_manifest',
        return_value='/does/not/matter/manifest.yaml'
    )
    @patch.object(ArgoCDDeploy, '_get_app_name', return_value='test-app-name')
    @patch.object(ArgoCDDeploy, '_update_yaml_file_value')
    @patch.object(ArgoCDDeploy, '_get_deployment_config_repo_tag', return_value='v0.42.0')
    @patch.object(ArgoCDDeploy, '_git_tag_and_push_deployment_config_repo')
    @patch.object(ArgoCDDeploy, '_argocd_add_target_cluster')
    @patch.object(ArgoCDGeneric, '_clone_repo', return_value='/does/not/matter')
    @patch.object(ArgoCDGeneric, '_git_commit_file')
    @patch.object(ArgoCDGeneric, '_argocd_sign_in')
    @patch.object(ArgoCDGeneric, '_argocd_app_create_or_update')
    @patch.object(ArgoCDGeneric, '_argocd_app_sync')
    @patch.object(
        ArgoCDGeneric,
        '_get_deployed_host_urls',
        return_value=['https://fruits.ploigos.xyz']
    )
    @patch.object(
        ArgoCDDeploy,
        '_get_deployment_config_helm_chart_environment_values_file',
        return_value='values-PROD.yaml'
    )
    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/test')
    def test_run_step_success_additional_helm_values_files(
            self,
            get_repo_branch_mock,
            get_deployment_config_helm_chart_environment_values_file_mock,
            get_deployed_host_urls_mock,
            argocd_app_sync_mock,
            argocd_app_create_or_update_mock,
            argocd_sign_in_mock,
            git_commit_file_mock,
            clone_repo_mock,
            argocd_add_target_cluster_mock,
            git_tag_and_push_deployment_config_repo_mock,
            get_deployment_config_repo_tag_mock,
            update_yaml_file_value_mock,
            get_app_name_mock,
            argocd_get_app_manifest_mock
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'deployment-config-repo': 'https://git.ploigos.xyz/foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'container-image-tag': 'v0.42.0',
                'additional-helm-values-files': ['secrets.yaml', 'extra-secrets.yaml']
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )

            actual_step_results = step_implementer._run_step()
            expected_step_result = StepResult(
                step_name='deploy',
                sub_step_name='ArgoCDDeploy',
                sub_step_implementer_name='ArgoCDDeploy',
                environment='PROD'
            )
            expected_step_result.add_artifact(
                name='argocd-app-name',
                value='test-app-name'
            )
            expected_step_result.add_artifact(
                name='config-repo-git-tag',
                value='v0.42.0'
            )
            expected_step_result.add_artifact(
                name='argocd-deployed-manifest',
                value='/does/not/matter/manifest.yaml'
            )
            expected_step_result.add_artifact(
                name='deployed-host-urls',
                value=['https://fruits.ploigos.xyz']
            )
            self.assertEqual(actual_step_results, expected_step_result)

            get_repo_branch_mock.assert_called_once_with()
            get_deployment_config_helm_chart_environment_values_file_mock.assert_called_once_with()
            get_app_name_mock.assert_called_once_with()
            deployment_config_repo_dir = os.path.join(
                step_implementer.work_dir_path,
                'deployment-config-repo'
            )
            clone_repo_mock.assert_called_once_with(
                repo_dir=deployment_config_repo_dir,
                repo_url=step_config['deployment-config-repo'],
                repo_branch='feature/test',
                git_email=step_config['git-email'],
                git_name=step_config['git-name'],
                username=None,
                password=None
            )
            update_yaml_file_value_mock.assert_called_once_with(
                file='/does/not/matter/charts/foo/values-PROD.yaml',
                yq_path=step_config['deployment-config-helm-chart-values-file-image-tag-yq-path'],
                value=step_config['container-image-tag']
            )
            git_commit_file_mock.assert_called_once_with(
                git_commit_message='Updating values for deployment to PROD',
                file_path='charts/foo/values-PROD.yaml',
                repo_dir='/does/not/matter'
            )
            get_deployment_config_repo_tag_mock.assert_called_once_with()
            git_tag_and_push_deployment_config_repo_mock.assert_called_once_with(
                deployment_config_repo=step_config['deployment-config-repo'],
                deployment_config_repo_dir='/does/not/matter',
                deployment_config_repo_tag='v0.42.0',
                force_push_tags=False
            )
            argocd_sign_in_mock.assert_called_once_with(
                argocd_api=step_config['argocd-api'],
                username=step_config['argocd-username'],
                password=step_config['argocd-password'],
                insecure=step_config['argocd-skip-tls']
            )
            argocd_add_target_cluster_mock.assert_called_once_with(
                kube_api='https://kubernetes.default.svc',
                kube_api_token=None,
                kube_api_skip_tls=False
            )
            argocd_app_create_or_update_mock.assert_called_once_with(
                argocd_app_name='test-app-name',
                repo=step_config['deployment-config-repo'],
                revision='v0.42.0',
                path=step_config['deployment-config-helm-chart-path'],
                dest_server='https://kubernetes.default.svc',
                auto_sync=True,
                values_files=['values-PROD.yaml', 'secrets.yaml', 'extra-secrets.yaml']
            )
            argocd_app_sync_mock.assert_called_once_with(
                argocd_app_name='test-app-name',
                argocd_sync_timeout_seconds=60,
                argocd_sync_retry_limit=3,
                argocd_sync_prune=True
            )
            argocd_get_app_manifest_mock.assert_called_once_with(
                argocd_app_name='test-app-name'
            )
            get_deployed_host_urls_mock.assert_called_once_with(
                manifest_path='/does/not/matter/manifest.yaml'
            )

    @patch.object(
        ArgoCDDeploy,
        '_argocd_get_app_manifest',
        return_value='/does/not/matter/manifest.yaml'
    )
    @patch.object(ArgoCDDeploy, '_get_app_name', return_value='test-app-name')
    @patch.object(ArgoCDDeploy, '_update_yaml_file_value')
    @patch.object(ArgoCDDeploy, '_get_deployment_config_repo_tag', return_value='v0.42.0')
    @patch.object(ArgoCDDeploy, '_git_tag_and_push_deployment_config_repo')
    @patch.object(ArgoCDDeploy, '_argocd_add_target_cluster')
    @patch.object(ArgoCDGeneric, '_clone_repo', return_value='/does/not/matter')
    @patch.object(ArgoCDGeneric, '_git_commit_file')
    @patch.object(ArgoCDGeneric, '_argocd_sign_in')
    @patch.object(ArgoCDGeneric, '_argocd_app_create_or_update')
    @patch.object(ArgoCDGeneric, '_argocd_app_sync')
    @patch.object(
        ArgoCDGeneric,
        '_get_deployed_host_urls',
        return_value=['https://fruits.ploigos.xyz']
    )
    @patch.object(
        ArgoCDDeploy,
        '_get_deployment_config_helm_chart_environment_values_file',
        return_value='values-PROD.yaml'
    )
    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/test')
    def test_run_step_fail_clone_config_repo(
            self,
            get_repo_branch_mock,
            get_deployment_config_helm_chart_environment_values_file_mock,
            get_deployed_host_urls_mock,
            argocd_app_sync_mock,
            argocd_app_create_or_update_mock,
            argocd_sign_in_mock,
            git_commit_file_mock,
            clone_repo_mock,
            argocd_add_target_cluster_mock,
            git_tag_and_push_deployment_config_repo_mock,
            get_deployment_config_repo_tag_mock,
            update_yaml_file_value_mock,
            get_app_name_mock,
            argocd_get_app_manifest_mock
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'deployment-config-repo': 'https://git.ploigos.xyz/foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'container-image-tag': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )

            clone_repo_mock.side_effect = StepRunnerException('mock failed to clone repo error')

            actual_step_results = step_implementer._run_step()
            expected_step_result = StepResult(
                step_name='deploy',
                sub_step_name='ArgoCDDeploy',
                sub_step_implementer_name='ArgoCDDeploy',
                environment='PROD'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Error deploying to environment (PROD):' \
                                           ' mock failed to clone repo error'
            expected_step_result.add_artifact(
                name='argocd-app-name',
                value='test-app-name'
            )

            self.assertEqual(actual_step_results, expected_step_result)

            get_repo_branch_mock.assert_called_once_with()
            get_deployment_config_helm_chart_environment_values_file_mock.assert_called_once_with()
            get_app_name_mock.assert_called_once_with()
            deployment_config_repo_dir = os.path.join(
                step_implementer.work_dir_path,
                'deployment-config-repo'
            )
            clone_repo_mock.assert_called_once_with(
                repo_dir=deployment_config_repo_dir,
                repo_url=step_config['deployment-config-repo'],
                repo_branch='feature/test',
                git_email=step_config['git-email'],
                git_name=step_config['git-name'],
                username=None,
                password=None
            )
            update_yaml_file_value_mock.assert_not_called()
            git_commit_file_mock.assert_not_called()
            get_deployment_config_repo_tag_mock.assert_not_called()
            git_tag_and_push_deployment_config_repo_mock.assert_not_called()
            argocd_sign_in_mock.assert_not_called()
            argocd_add_target_cluster_mock.assert_not_called()
            argocd_app_create_or_update_mock.assert_not_called()
            argocd_app_sync_mock.assert_not_called()
            argocd_get_app_manifest_mock.assert_not_called()
            get_deployed_host_urls_mock.assert_not_called()
