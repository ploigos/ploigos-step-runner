import os
import re
from io import IOBase
from unittest.mock import call, patch

from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.deploy import ArgoCDDeploy
from ploigos_step_runner.step_implementers.shared import (ArgoCDGeneric,
                                                          ContainerDeployMixin)
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


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

class TestStepImplementerSharedArgoCDDeploy_Other(TestStepImplementerDeployArgoCDBase):
    @patch.object(ContainerDeployMixin, 'step_implementer_config_defaults', return_value={})
    def test_step_implementer_config_defaults(
        self,
        mock_container_deploy_mixin_step_implementer_config_defaults
    ):
        defaults = ArgoCDDeploy.step_implementer_config_defaults()
        expected_defaults = {
            'argocd-sync-timeout-seconds': 60,
            'argocd-sync-retry-limit': 3,
            'argocd-auto-sync': True,
            'argocd-skip-tls' : False,
            'argocd-sync-prune': True,
            'argocd-project': 'default',
            'deployment-config-helm-chart-path': './',
            'deployment-config-helm-chart-additional-values-files': [],
            'additional-helm-values-files': [],
            'deployment-config-helm-chart-values-file-container-image-address-yq-path': 'image',
            'force-push-tags': False,
            'kube-api-skip-tls': False,
            'kube-api-uri': 'https://kubernetes.default.svc',
            'git-name': 'Ploigos Robot',
            'argocd-add-or-update-target-cluster': True
        }
        self.assertEqual(defaults, expected_defaults)
        mock_container_deploy_mixin_step_implementer_config_defaults.assert_called_once()

    @patch.object(ContainerDeployMixin, '_required_config_or_result_keys', return_value=[])
    def test_required_config_or_result_keys(
        self,
        mock_container_deploy_mixin_required_config_or_result_keys
    ):
        required_keys = ArgoCDDeploy._required_config_or_result_keys()
        expected_required_keys = [
            'argocd-username',
            'argocd-password',
            'argocd-api',
            'argocd-skip-tls',
            'argocd-project',
            'deployment-config-repo',
            'deployment-config-helm-chart-path',
            [
                'deployment-config-helm-chart-values-file-container-image-address-yq-path',
                'deployment-config-helm-chart-values-file-image-tag-yq-path'
            ],
            'git-email',
            'git-name',
            'organization',
            'applciation-name',
            'service-name',
            'branch'
        ]
        self.assertEqual(required_keys, expected_required_keys)
        mock_container_deploy_mixin_required_config_or_result_keys.assert_called_once()
@patch.object(ContainerDeployMixin, '_validate_required_config_or_previous_step_result_artifact_keys')
class TestStepImplementerDeployArgoCD_validate_required_config_or_previous_step_result_artifact_keys(
    TestStepImplementerDeployArgoCDBase
):
    def test_success_ssh_deploy_tag(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'deployment-config-repo': 'git@git.ploigos.xyz:foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'use-container-image-digest': False,
                'container-image-tag': 'v0.42.0',
                'container-image-pull-registry': 'mock-pull-registry.xyz',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
            mock_super_validate.assert_called_once()

    def test_success_ssh_deploy_digest(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'deployment-config-repo': 'git@git.ploigos.xyz:foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'use-container-image-digest': True,
                'container-image-digest': 'sha256:mockabc123',
                'container-image-pull-registry': 'mock-pull-registry.xyz',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
            mock_super_validate.assert_called_once()

    def test_success_deploy_using_container_image_pull_registry_true_provided_container_image_pull_registry_deploy_tag(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'deployment-config-repo': 'git@git.ploigos.xyz:foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'container-image-tag': 'v0.42.0',
                'use-container-image-digest': False,
                'use-container-image-short-address': False,
                'container-image-pull-registry': 'mock-pull-registry.xyz',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
            mock_super_validate.assert_called_once()

    def test_success_deploy_using_container_image_pull_registry_true_provided_container_image_registry_deploy_tag(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'deployment-config-repo': 'git@git.ploigos.xyz:foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'container-image-tag': 'v0.42.0',
                'use-container-image-digest': False,
                'use-container-image-short-address': False,
                'container-image-registry': 'mock-pull-registry.xyz',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
            mock_super_validate.assert_called_once()

    def test_success_deploy_using_container_image_pull_registry_true_provided_container_image_push_registry_deploy_tag(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'deployment-config-repo': 'git@git.ploigos.xyz:foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'container-image-tag': 'v0.42.0',
                'use-container-image-digest': False,
                'use-container-image-short-address': False,
                'container-image-push-registry': 'mock-pull-registry.xyz',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
            mock_super_validate.assert_called_once()

    def test_success_https_deploy_tag(
        self,
        mock_super_validate
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
                'git-username': 'test-git-username',
                'git-password': 'test-secret',
                'use-container-image-digest': False,
                'container-image-pull-registry': 'mock-pull-registry.xyz',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once()

    def test_success_https_deploy_digest(
        self,
        mock_super_validate
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
                'container-image-digest': 'sha256:mockabc123',
                'git-username': 'test-git-username',
                'git-password': 'test-secret',
                'use-container-image-digest': True,
                'container-image-pull-registry': 'mock-pull-registry.xyz',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once()

    def test_fail_https_no_git_username(
        self,
        mock_super_validate
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
                'git-password': 'test-secret',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                "Either 'git-username' or 'git-password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once()

    def test_fail_https_no_git_password(
        self,
        mock_super_validate
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
                'git-username': 'test-git-username',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                "Either 'git-username' or 'git-password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once()

    def test_fail_https_no_git_creds(
        self,
        mock_super_validate
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
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                r"Since provided 'deployment-config-repo'"
                rf" \({step_config['deployment-config-repo']}\) uses"
                r" http/https protical both 'git-username' and 'git-password' must be provided."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once()

    def test_fail_http_no_git_creds(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'deployment-config-repo': 'http://git.ploigos.xyz/foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'container-image-tag': 'v0.42.0',
                'container-image-pull-repository': 'mock-pull-repository'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                r"Since provided 'deployment-config-repo'"
                rf" \({step_config['deployment-config-repo']}\) uses"
                r" http/https protical both 'git-username' and 'git-password' must be provided."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once()

# NOTE:
#   Could definitely do some more negative testing of _run_step testing what happens when each
#   and every mocked function throws an error (that can throw an error)
@patch.object(
    ArgoCDDeploy,
    '_get_deploy_time_container_image_address',
    return_value='mock-deploy-time-container-image-address'
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
class TestStepImplementerArgoCDDeploy_run_step(TestStepImplementerDeployArgoCDBase):
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
            argocd_get_app_manifest_mock,
            get_deploy_time_container_image_address_mock
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
                'container-image-pull-repository': 'mock-org/mock-app/mock-service',
                'container-image-pull-digest': 'sha256:mockabc123',
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
                name='container-image-deployed-address',
                value='mock-deploy-time-container-image-address',
                description='Container image address used to deploy the container.'
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
                value='mock-deploy-time-container-image-address'
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
                dest_namespace='test-app-name',
                auto_sync=True,
                values_files=['values-PROD.yaml'],
                project='default'
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
            get_deploy_time_container_image_address_mock.assert_called_once_with()

    def test_run_step_success_do_not_add_or_update_cluster(
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
            argocd_get_app_manifest_mock,
            get_deploy_time_container_image_address_mock
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'argocd-add-or-update-target-cluster': False,
                'deployment-config-repo': 'https://git.ploigos.xyz/foo/deploy-config',
                'deployment-config-helm-chart-path': 'charts/foo',
                'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image.tag',
                'git-email': 'git@ploigos.xyz',
                'git-name': 'Ploigos',
                'container-image-pull-repository': 'mock-org/mock-app/mock-service',
                'container-image-pull-digest': 'sha256:mockabc123',
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
                name='container-image-deployed-address',
                value='mock-deploy-time-container-image-address',
                description='Container image address used to deploy the container.'
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
                value='mock-deploy-time-container-image-address'
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
            argocd_add_target_cluster_mock.assert_not_called()
            argocd_app_create_or_update_mock.assert_called_once_with(
                argocd_app_name='test-app-name',
                repo=step_config['deployment-config-repo'],
                revision='v0.42.0',
                path=step_config['deployment-config-helm-chart-path'],
                dest_server='https://kubernetes.default.svc',
                dest_namespace='test-app-name',
                auto_sync=True,
                values_files=['values-PROD.yaml'],
                project='default'
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
            get_deploy_time_container_image_address_mock.assert_called_once_with()

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
            argocd_get_app_manifest_mock,
            get_deploy_time_container_image_address_mock
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
                'deployment-namespace': 'best-namespace',
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
                name='container-image-deployed-address',
                value='mock-deploy-time-container-image-address',
                description='Container image address used to deploy the container.'
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
                value='mock-deploy-time-container-image-address'
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
                dest_namespace='best-namespace',
                auto_sync=True,
                values_files=['values-PROD.yaml'],
                project='default'
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
            get_deploy_time_container_image_address_mock.assert_called_once_with()

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
            argocd_get_app_manifest_mock,
            get_deploy_time_container_image_address_mock
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
                name='container-image-deployed-address',
                value='mock-deploy-time-container-image-address',
                description='Container image address used to deploy the container.'
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
                value='mock-deploy-time-container-image-address'
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
                dest_namespace='test-app-name',
                auto_sync=True,
                values_files=['values-PROD.yaml', 'secrets.yaml', 'extra-secrets.yaml'],
                project='default'
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
            get_deploy_time_container_image_address_mock.assert_called_once_with()

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
            argocd_get_app_manifest_mock,
            get_deploy_time_container_image_address_mock
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
            get_deploy_time_container_image_address_mock.assert_not_called()
