import os
import re
from io import IOBase
from unittest.mock import call, patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any, create_sh_side_effect
from ploigos_step_runner import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.deploy.argocd import ArgoCD


class TestStepImplementerDeployArgoCDBase(BaseStepImplementerTestCase):
    def create_step_implementer(
        self,
        step_config={},
        results_dir_path='',
        results_file_name='',
        work_dir_path='',
        environment=None
    ):
        return self.create_given_step_implementer(
            step_implementer=ArgoCD,
            step_config=step_config,
            step_name='deploy',
            implementer='ArgoCD',
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path,
            environment=environment
        )
class TestStepImplementerDeployArgoCD_Other(TestStepImplementerDeployArgoCDBase):
    def test_step_implementer_config_defaults(self):
        defaults = ArgoCD.step_implementer_config_defaults()
        expected_defaults = {
            'argocd-sync-timeout-seconds': 60,
            'argocd-auto-sync': True,
            'argocd-skip-tls' : False,
            'deployment-config-helm-chart-path': './',
            'deployment-config-helm-chart-additional-values-files': [],
            'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image_tag',
            'force-push-tags': False,
            'kube-api-skip-tls': False,
            'kube-api-uri': 'https://kubernetes.default.svc',
            'git-name': 'Ploigos Robot'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = ArgoCD._required_config_or_result_keys()
        expected_required_keys = [
            'argocd-username',
            'argocd-password',
            'argocd-api',
            'argocd-skip-tls',
            'deployment-config-repo',
            'deployment-config-helm-chart-path',
            'deployment-config-helm-chart-values-file-image-tag-yq-path',
            'git-email',
            'git-name',
            'container-image-tag'
        ]
        self.assertEqual(required_keys, expected_required_keys)

class TestStepImplementerDeployArgoCD_validate_required_config_or_previous_step_result_artifact_keys(
    TestStepImplementerDeployArgoCDBase
):
    def test_ArgoCD_validate_required_config_or_previous_step_result_artifact_keys_success_ssh(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
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
                'container-image-tag': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_ArgoCD_validate_required_config_or_previous_step_result_artifact_keys_success_https(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
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
                'git-password': 'test-secret'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_ArgoCD_validate_required_config_or_previous_step_result_artifact_keys_fail_https_no_git_username(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
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
                'git-password': 'test-secret'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                "Either 'git-username' or 'git-password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_ArgoCD_validate_required_config_or_previous_step_result_artifact_keys_fail_https_no_git_password(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
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
                'git-username': 'test-git-username'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                "Either 'git-username' or 'git-password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_ArgoCD_validate_required_config_or_previous_step_result_artifact_keys_fail_https_no_git_creds(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
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
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                r"Since provided 'deployment-config-repo'"
                rf" \({step_config['deployment-config-repo']}\) uses"
                r" http/https protical both 'git-username' and 'git-password' must be provided."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_ArgoCD_validate_required_config_or_previous_step_result_artifact_keys_fail_http_no_git_creds(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
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
                'container-image-tag': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                r"Since provided 'deployment-config-repo'"
                rf" \({step_config['deployment-config-repo']}\) uses"
                r" http/https protical both 'git-username' and 'git-password' must be provided."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

# NOTE:
#   Could definitely do some more negative testing of _run_step testing what happens when each
#   and every mocked function throws an error (that can throw an error)
class TestStepImplementerDeployArgoCD_run_step(TestStepImplementerDeployArgoCDBase):
    @patch.object(
        ArgoCD,
        '_ArgoCD__argocd_get_app_manifest',
        return_value='/does/not/matter/manifest.yaml'
    )
    @patch.object(ArgoCD, '_ArgoCD__get_app_name', return_value='test-app-name')
    @patch.object(ArgoCD, '_ArgoCD__update_yaml_file_value')
    @patch.object(ArgoCD, '_ArgoCD__get_deployment_config_repo_tag', return_value='v0.42.0')
    @patch.object(ArgoCD, '_ArgoCD__git_tag_and_push_deployment_config_repo')
    @patch.object(ArgoCD, '_ArgoCD__argocd_add_target_cluster')
    @patch.object(ArgoCD, '_ArgoCD__clone_repo', return_value='/does/not/matter')
    @patch.object(ArgoCD, '_ArgoCD__git_commit_file')
    @patch.object(ArgoCD, '_ArgoCD__argocd_sign_in')
    @patch.object(ArgoCD, '_ArgoCD__argocd_app_create_or_update')
    @patch.object(ArgoCD, '_ArgoCD__argocd_app_sync')
    @patch.object(
        ArgoCD,
        '_ArgoCD__get_deployed_host_urls',
        return_value=['https://fruits.ploigos.xyz']
    )
    @patch.object(
        ArgoCD,
        '_ArgoCD__get_deployment_config_helm_chart_environment_values_file',
        return_value='values-PROD.yaml'
    )
    @patch.object(ArgoCD, '_ArgoCD__get_repo_branch', return_value='feature/test')
    def test_ArgoCD_run_step_success(
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
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
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
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
                environment='PROD'
            )

            actual_step_results = step_implementer._run_step()
            expected_step_result = StepResult(
                step_name='deploy',
                sub_step_name='ArgoCD',
                sub_step_implementer_name='ArgoCD',
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
            self.assertEqual(
                actual_step_results.get_step_result_dict(),
                expected_step_result.get_step_result_dict()
            )

            get_repo_branch_mock.assert_called_once_with()
            get_deployment_config_helm_chart_environment_values_file_mock.assert_called_once_with()
            get_app_name_mock.assert_called_once_with()
            deployment_config_repo_dir = os.path.join(
                work_dir_path,
                'deploy',
                'PROD',
                'deployment-config-repo'
            )
            clone_repo_mock.assert_called_once_with(
                repo_dir=deployment_config_repo_dir,
                repo_url=step_config['deployment-config-repo'],
                repo_branch='feature/test',
                user_email=step_config['git-email'],
                user_name=step_config['git-name']
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
                revision='feature/test',
                path=step_config['deployment-config-helm-chart-path'],
                dest_server='https://kubernetes.default.svc',
                auto_sync=True,
                values_files=['values-PROD.yaml']
            )
            argocd_app_sync_mock.assert_called_once_with(
                argocd_app_name='test-app-name',
                argocd_sync_timeout_seconds=60
            )
            argocd_get_app_manifest_mock.assert_called_once_with(
                argocd_app_name='test-app-name'
            )
            get_deployed_host_urls_mock.assert_called_once_with(
                manifest_path='/does/not/matter/manifest.yaml'
            )

    @patch.object(
        ArgoCD,
        '_ArgoCD__argocd_get_app_manifest',
        return_value='/does/not/matter/manifest.yaml'
    )
    @patch.object(ArgoCD, '_ArgoCD__get_app_name', return_value='test-app-name')
    @patch.object(ArgoCD, '_ArgoCD__update_yaml_file_value')
    @patch.object(ArgoCD, '_ArgoCD__get_deployment_config_repo_tag', return_value='v0.42.0')
    @patch.object(ArgoCD, '_ArgoCD__git_tag_and_push_deployment_config_repo')
    @patch.object(ArgoCD, '_ArgoCD__argocd_add_target_cluster')
    @patch.object(ArgoCD, '_ArgoCD__clone_repo', return_value='/does/not/matter')
    @patch.object(ArgoCD, '_ArgoCD__git_commit_file')
    @patch.object(ArgoCD, '_ArgoCD__argocd_sign_in')
    @patch.object(ArgoCD, '_ArgoCD__argocd_app_create_or_update')
    @patch.object(ArgoCD, '_ArgoCD__argocd_app_sync')
    @patch.object(
        ArgoCD,
        '_ArgoCD__get_deployed_host_urls',
        return_value=['https://fruits.ploigos.xyz']
    )
    @patch.object(
        ArgoCD,
        '_ArgoCD__get_deployment_config_helm_chart_environment_values_file',
        return_value='values-PROD.yaml'
    )
    @patch.object(ArgoCD, '_ArgoCD__get_repo_branch', return_value='feature/test')
    def test_ArgoCD_run_step_fail_clone_config_repo(
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
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
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
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
                environment='PROD'
            )

            clone_repo_mock.side_effect = StepRunnerException('mock failed to clone repo error')

            actual_step_results = step_implementer._run_step()
            expected_step_result = StepResult(
                step_name='deploy',
                sub_step_name='ArgoCD',
                sub_step_implementer_name='ArgoCD',
                environment='PROD'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Error deploying to environment (PROD):' \
                ' mock failed to clone repo error'
            expected_step_result.add_artifact(
                name='argocd-app-name',
                value='test-app-name'
            )

            self.assertEqual(
                actual_step_results.get_step_result_dict(),
                expected_step_result.get_step_result_dict()
            )

            get_repo_branch_mock.assert_called_once_with()
            get_deployment_config_helm_chart_environment_values_file_mock.assert_called_once_with()
            get_app_name_mock.assert_called_once_with()
            deployment_config_repo_dir = os.path.join(
                work_dir_path,
                'deploy',
                'PROD',
                'deployment-config-repo'
            )
            clone_repo_mock.assert_called_once_with(
                repo_dir=deployment_config_repo_dir,
                repo_url=step_config['deployment-config-repo'],
                repo_branch='feature/test',
                user_email=step_config['git-email'],
                user_name=step_config['git-name']
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

class TestStepImplementerDeployArgoCD__get_container_image_version(
    TestStepImplementerDeployArgoCDBase
):
    def test_ArgoCD__get_container_image_version_config_value(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'container-image-version': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            image_version = step_implementer._ArgoCD__get_container_image_version()
            self.assertEqual(image_version, 'v0.42.0')

    def test_ArgoCD__get_container_image_version_no_config_value(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            image_version = step_implementer._ArgoCD__get_container_image_version()
            self.assertEqual(image_version, 'latest')

class TestStepImplementerDeployArgoCD__get_deployment_config_helm_chart_environment_values_file(
    TestStepImplementerDeployArgoCDBase
):
    def test_ArgoCD__get_deployment_config_helm_chart_environment_values_file_config_value(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'deployment-config-helm-chart-environment-values-file': 'values-AWEOMSE.yaml'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            deployment_config_helm_chart_env_value_file = \
                step_implementer._ArgoCD__get_deployment_config_helm_chart_environment_values_file()
            self.assertEqual(
                deployment_config_helm_chart_env_value_file,
                'values-AWEOMSE.yaml'
            )

    def test_ArgoCD__get_deployment_config_helm_chart_environment_values_file_no_config_value_no_env(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )

            deployment_config_helm_chart_env_value_file = \
                step_implementer._ArgoCD__get_deployment_config_helm_chart_environment_values_file()
            self.assertEqual(
                deployment_config_helm_chart_env_value_file,
                'values.yaml'
            )

    def test_ArgoCD__get_deployment_config_helm_chart_environment_values_file_no_config_value_with_env(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
                environment='PROD'
            )

            deployment_config_helm_chart_env_value_file = \
                step_implementer._ArgoCD__get_deployment_config_helm_chart_environment_values_file()
            self.assertEqual(
                deployment_config_helm_chart_env_value_file,
                'values-PROD.yaml'
            )

class TestStepImplementerDeployArgoCD__update_yaml_file_value(TestStepImplementerDeployArgoCDBase):
    @patch('sh.yq', create=True)
    def test_ArgoCD__update_yaml_file_value_success(self, yq_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            updated_file_path = step_implementer._ArgoCD__update_yaml_file_value(
                file='/does/not/matter/chart/values-PROD.yaml',
                yq_path='image.tag',
                value='v0.42.0-abc123'
            )
            self.assertEqual(updated_file_path, '/does/not/matter/chart/values-PROD.yaml')
            yq_script_file_path = os.path.join(
                work_dir_path,
                'deploy',
                'update-yaml-file-yq-script.yaml'
            )
            yq_mock.write.assert_called_once_with(
                '/does/not/matter/chart/values-PROD.yaml',
                f'--script={yq_script_file_path}',
                '--inplace'
            )
            with open(yq_script_file_path, 'r') as yq_script_file:
                actual_yq_script = yq_script_file.read()

                self.assertEqual(
                    actual_yq_script,
                    f"- command: update\n"
                    f"  path: image.tag\n"
                    f"  value:\n"
                    f"    v0.42.0-abc123 # written by ploigos-step-runner\n",
                )

    @patch('sh.yq', create=True)
    def test_ArgoCD__update_yaml_file_value_fail(self, yq_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            yq_mock.write.side_effect = create_sh_side_effect(
                exception=sh.ErrorReturnCode('yq', b'mock out', b'mock yq write error')
            )

            file = '/does/not/matter/chart/values-PROD.yaml'
            yq_path = 'image.tag'
            value = 'v0.42.0-abc123'
            with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    rf"Error updating YAML file \({file}\) target \({yq_path}\)"
                    rf" with value \({value}\):"
                    r".*RAN: yq"
                    r".*STDOUT:"
                    r".*mock out"
                    r".*STDERR:"
                    r".*mock yq write error",
                    re.DOTALL
                )
            ):
                step_implementer._ArgoCD__update_yaml_file_value(
                    file=file,
                    yq_path=yq_path,
                    value=value
                )
                yq_script_file_path = os.path.join(
                    work_dir_path,
                    'deploy',
                    'update-yaml-file-yq-script.yaml'
                )
                yq_mock.write.assert_called_once_with(
                    '/does/not/matter/chart/values-PROD.yaml',
                    f'--script={yq_script_file_path}',
                    '--inplace'
                )
                with open(yq_script_file_path, 'r') as yq_script_file:
                    actual_yq_script = yq_script_file.read()

                    self.assertEqual(
                        actual_yq_script,
                        f"- command: update\n"
                        f"  path: image.tag\n"
                        f"  value:\n"
                        f"    v0.42.0-abc123 # written by ploigos-step-runner\n",
                    )

class TestStepImplementerDeployArgoCD__git_tag_and_push_deployment_config_repo(TestStepImplementerDeployArgoCDBase):
    @patch.object(ArgoCD, '_ArgoCD__git_tag_and_push')
    def test_ArgoCD__git_tag_and_push_deployment_config_repo_http(self, git_tag_and_push_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'git-username': 'test-username',
                'git-password': 'test-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._ArgoCD__git_tag_and_push_deployment_config_repo(
                deployment_config_repo='http://git.ploigos.xys/foo',
                deployment_config_repo_dir='/does/not/matter',
                deployment_config_repo_tag='test-tag',
                force_push_tags=False
            )
            git_tag_and_push_mock.assert_called_once_with(
                repo_dir='/does/not/matter',
                tag='test-tag',
                url='http://test-username:test-password@git.ploigos.xys/foo',
                force_push_tags=False
            )

    @patch.object(ArgoCD, '_ArgoCD__git_tag_and_push')
    def test_ArgoCD__git_tag_and_push_deployment_config_repo_https(self, git_tag_and_push_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'git-username': 'test-username',
                'git-password': 'test-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._ArgoCD__git_tag_and_push_deployment_config_repo(
                deployment_config_repo='https://git.ploigos.xys/foo',
                deployment_config_repo_dir='/does/not/matter',
                deployment_config_repo_tag='test-tag',
                force_push_tags=False
            )
            git_tag_and_push_mock.assert_called_once_with(
                repo_dir='/does/not/matter',
                tag='test-tag',
                url='https://test-username:test-password@git.ploigos.xys/foo',
                force_push_tags=False
            )

    @patch.object(ArgoCD, '_ArgoCD__git_tag_and_push')
    def test_ArgoCD__git_tag_and_push_deployment_config_repo_ssh(self, git_tag_and_push_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'git-username': 'test-username',
                'git-password': 'test-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._ArgoCD__git_tag_and_push_deployment_config_repo(
                deployment_config_repo='git@git.ploigos.xys:foo/bar',
                deployment_config_repo_dir='/does/not/matter',
                deployment_config_repo_tag='test-tag',
                force_push_tags=False
            )
            git_tag_and_push_mock.assert_called_once_with(
                repo_dir='/does/not/matter',
                tag='test-tag',
                force_push_tags=False
            )


class TestStepImplementerDeployArgoCD__get_app_name(TestStepImplementerDeployArgoCDBase):
    @patch.object(ArgoCD, '_ArgoCD__get_repo_branch', return_value='feature/test')
    def test_ArgoCD__get_app_name_no_env_less_then_max_length(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-org',
                'application-name': 'test-app',
                'service-name': 'test-service'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            app_name = step_implementer._ArgoCD__get_app_name()
            self.assertEqual(app_name, 'test-org-test-app-test-service-feature-test')

    @patch.object(ArgoCD, '_ArgoCD__get_repo_branch', return_value='feature/TEST')
    def test_ArgoCD__get_app_name_no_env_less_then_max_length_caps(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            app_name = step_implementer._ArgoCD__get_app_name()
            self.assertEqual(app_name, 'test-org-test-app-test-service-feature-test')

    @patch.object(ArgoCD, '_ArgoCD__get_repo_branch', return_value='feature/test')
    def test_ArgoCD__get_app_name_no_env_more_then_max_length(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-org',
                'application-name': 'test-app',
                'service-name': 'test-service-this-is-really-long-hello-world-foo'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            app_name = step_implementer._ArgoCD__get_app_name()
            self.assertEqual(app_name, 'ice-this-is-really-long-hello-world-foo-feature-test')

    @patch.object(ArgoCD, '_ArgoCD__get_repo_branch', return_value='feature/test')
    def test_ArgoCD__get_app_name_with_env_less_then_max_length(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-org',
                'application-name': 'test-app',
                'service-name': 'test-service'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
                environment='PROD'
            )

            app_name = step_implementer._ArgoCD__get_app_name()
            self.assertEqual(app_name, 'test-org-test-app-test-service-feature-test-prod')

class TestStepImplementerDeployArgoCD__get_deployment_config_repo_tag(TestStepImplementerDeployArgoCDBase):
    def test_ArgoCD__get_deployment_config_repo_tag_use_tag(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'tag': 'v0.42.0-abc123',
                'version': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            deployment_config_repo_tag = step_implementer._ArgoCD__get_deployment_config_repo_tag()
            self.assertEqual(deployment_config_repo_tag, 'v0.42.0-abc123')

    def test_ArgoCD__get_deployment_config_repo_tag_use_version(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'version': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            deployment_config_repo_tag = step_implementer._ArgoCD__get_deployment_config_repo_tag()
            self.assertEqual(deployment_config_repo_tag, 'v0.42.0')


    def test_ArgoCD__get_deployment_config_repo_tag_use_latest(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            deployment_config_repo_tag = step_implementer._ArgoCD__get_deployment_config_repo_tag()
            self.assertEqual(deployment_config_repo_tag, 'latest')

    def test_ArgoCD__get_deployment_config_repo_tag_use_tag_with_env(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'tag': 'v0.42.0-main+abc123',
                'version': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
                environment='PROD'
            )

            deployment_config_repo_tag = step_implementer._ArgoCD__get_deployment_config_repo_tag()
            self.assertEqual(deployment_config_repo_tag, 'v0.42.0-main+abc123.PROD')

class TestStepImplementerDeployArgoCD__get_deployed_host_urls(TestStepImplementerDeployArgoCDBase):
    def __run__ArgoCD__get_deployed_host_urls_test(
        self,
        manifest_contents,
        expected_host_urls
    ):
        with TempDirectory() as temp_dir:
            temp_dir.write('manifest.yaml', bytes(manifest_contents, 'utf-8'))
            manifest_path = os.path.join(temp_dir.path, 'manifest.yaml')

            actual_host_urls = ArgoCD._ArgoCD__get_deployed_host_urls(
                manifest_path=manifest_path
            )

            self.assertEqual(actual_host_urls, expected_host_urls)

    def test_ArgoCD__get_deployed_host_urls_empty_file(self):
        self.__run__ArgoCD__get_deployed_host_urls_test(
            manifest_contents="",
            expected_host_urls=[]
        )

    def test_ArgoCD__get_deployed_host_urls_empty_yaml_doc(self):
        self.__run__ArgoCD__get_deployed_host_urls_test(
            manifest_contents="---",
            expected_host_urls=[]
        )

    def test_ArgoCD__get_deployed_host_urls_yaml_doc_no_kind(self):
        self.__run__ArgoCD__get_deployed_host_urls_test(
            manifest_contents="""
---
foo: test"
""",
            expected_host_urls=[]
        )

    def test_ArgoCD__get_deployed_host_urls_1_http_routes_no_ingress(self):
        self.__run__ArgoCD__get_deployed_host_urls_test(
            manifest_contents="""
---
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"route.openshift.io/v1","kind":"Route","metadata":{"annotations":{},"labels":{"app.kubernetes.io/instance":"s-mvn-jenkins-std-fruit-feature-results-refactor-dev"},"name":"fruit","namespace":"s-mvn-jenkins-std-fruit-feature-results-refactor-dev"},"spec":{"path":"/","port":{"targetPort":"http"},"to":{"kind":"Service","name":"fruit"}}}
    openshift.io/host.generated: "true"
  creationTimestamp: "2020-12-16T22:14:46Z"
  labels:
    app.kubernetes.io/instance: s-mvn-jenkins-std-fruit-feature-results-refactor-dev
  managedFields:
  - apiVersion: route.openshift.io/v1
    fieldsType: FieldsV1
    fieldsV1:
      f:metadata:
        f:annotations:
          .: {}
          f:kubectl.kubernetes.io/last-applied-configuration: {}
        f:labels:
          .: {}
          f:app.kubernetes.io/instance: {}
      f:spec:
        f:path: {}
        f:port:
          .: {}
          f:targetPort: {}
        f:to:
          f:kind: {}
          f:name: {}
          f:weight: {}
        f:wildcardPolicy: {}
    manager: argocd-application-controller
    operation: Update
    time: "2020-12-16T22:14:46Z"
  - apiVersion: route.openshift.io/v1
    fieldsType: FieldsV1
    fieldsV1:
      f:status:
        f:ingress: {}
    manager: openshift-router
    operation: Update
    time: "2020-12-16T22:14:46Z"
  name: fruit
  namespace: s-mvn-jenkins-std-fruit-feature-results-refactor-dev
  resourceVersion: "92938959"
  selfLink: /apis/route.openshift.io/v1/namespaces/s-mvn-jenkins-std-fruit-feature-results-refactor-dev/routes/fruit
  uid: f5d36e42-b894-49d9-9885-64ed7bc438db
spec:
  host: fruit-s-mvn-jenkins-std-fruit-feature-results-refactor-dev.apps.ploigos.xyz
  path: /
  port:
    targetPort: http
  to:
    kind: Service
    name: fruit
    weight: 100
  wildcardPolicy: None
status:
  ingress:
  - conditions:
    - lastTransitionTime: "2020-12-16T22:14:46Z"
      status: "True"
      type: Admitted
    host: fruit-s-mvn-jenkins-std-fruit-feature-results-refactor-dev.apps.ploigos.xyz
    routerCanonicalHostname: apps.ploigos.xyz
    routerName: default
    wildcardPolicy: None
""",
            expected_host_urls=[
                'http://fruit-s-mvn-jenkins-std-fruit-feature-results-refactor-dev.apps.ploigos.xyz'
            ]
        )

    def test_ArgoCD__get_deployed_host_urls_1_https_routes_no_ingress(self):
        self.__run__ArgoCD__get_deployed_host_urls_test(
            manifest_contents="""
---
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"route.openshift.io/v1","kind":"Route","metadata":{"annotations":{},"labels":{"app.kubernetes.io/instance":"s-mvn-jenkins-std-fruit-feature-results-refactor-dev"},"name":"fruit","namespace":"s-mvn-jenkins-std-fruit-feature-results-refactor-dev"},"spec":{"path":"/","port":{"targetPort":"http"},"to":{"kind":"Service","name":"fruit"}}}
    openshift.io/host.generated: "true"
  creationTimestamp: "2020-12-16T22:14:46Z"
  labels:
    app.kubernetes.io/instance: s-mvn-jenkins-std-fruit-feature-results-refactor-dev
  managedFields:
  - apiVersion: route.openshift.io/v1
    fieldsType: FieldsV1
    fieldsV1:
      f:metadata:
        f:annotations:
          .: {}
          f:kubectl.kubernetes.io/last-applied-configuration: {}
        f:labels:
          .: {}
          f:app.kubernetes.io/instance: {}
      f:spec:
        f:path: {}
        f:port:
          .: {}
          f:targetPort: {}
        f:to:
          f:kind: {}
          f:name: {}
          f:weight: {}
        f:wildcardPolicy: {}
    manager: argocd-application-controller
    operation: Update
    time: "2020-12-16T22:14:46Z"
  - apiVersion: route.openshift.io/v1
    fieldsType: FieldsV1
    fieldsV1:
      f:status:
        f:ingress: {}
    manager: openshift-router
    operation: Update
    time: "2020-12-16T22:14:46Z"
  name: fruit
  namespace: s-mvn-jenkins-std-fruit-feature-results-refactor-dev
  resourceVersion: "92938959"
  selfLink: /apis/route.openshift.io/v1/namespaces/s-mvn-jenkins-std-fruit-feature-results-refactor-dev/routes/fruit
  uid: f5d36e42-b894-49d9-9885-64ed7bc438db
spec:
  host: fruit-s-mvn-jenkins-std-fruit-feature-results-refactor-dev.apps.ploigos.xyz
  path: /
  port:
    targetPort: http
  to:
    kind: Service
    name: fruit
    weight: 100
  tls:
    termination: edge
  wildcardPolicy: None
status:
  ingress:
  - conditions:
    - lastTransitionTime: "2020-12-16T22:14:46Z"
      status: "True"
      type: Admitted
    host: fruit-s-mvn-jenkins-std-fruit-feature-results-refactor-dev.apps.ploigos.xyz
    routerCanonicalHostname: apps.ploigos.xyz
    routerName: default
    wildcardPolicy: None
""",
            expected_host_urls=[
                'https://fruit-s-mvn-jenkins-std-fruit-feature-results-refactor-dev.apps.ploigos.xyz'
            ]
        )

    def test_ArgoCD__get_deployed_host_urls_no_routes_1_http_ingress(self):
        self.__run__ArgoCD__get_deployed_host_urls_test(
            manifest_contents="""
---
kind: Ingress
apiVersion: networking.k8s.io/v1
metadata:
  name: test
spec:
  rules:
  - host: foo.apps.ploigos.xyz
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: foo
            port:
              name: http-listener
""",
            expected_host_urls=[
                'http://foo.apps.ploigos.xyz'
            ]
        )

    def test_ArgoCD__get_deployed_host_urls_no_routes_1_http_ingress_with_tls_list(self):
        self.__run__ArgoCD__get_deployed_host_urls_test(
            manifest_contents="""
---
kind: Ingress
apiVersion: networking.k8s.io/v1
metadata:
  name: test
spec:
  tls:
  - hosts:
    - does-not-match.apps.ploigos.xyz
  rules:
  - host: foo.apps.ploigos.xyz
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: foo
            port:
              name: http-listener
""",
            expected_host_urls=[
                'http://foo.apps.ploigos.xyz'
            ]
        )

    def test_ArgoCD__get_deployed_host_urls_no_routes_1_https_ingress(self):
        self.__run__ArgoCD__get_deployed_host_urls_test(
            manifest_contents="""
---
kind: Ingress
apiVersion: networking.k8s.io/v1
metadata:
  name: test
  annotations:
    route.openshift.io/termination: "edge"
spec:
  tls:
  - hosts:
    - foo.apps.ploigos.xyz
  rules:
  - host: foo.apps.ploigos.xyz
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: foo
            port:
              name: http-listener
""",
            expected_host_urls=[
                'https://foo.apps.ploigos.xyz'
            ]
        )

    def test_ArgoCD__get_deployed_host_urls_1_http_route_1_https_route_1_http_ingress_1_https_ingress(self):
        self.__run__ArgoCD__get_deployed_host_urls_test(
            manifest_contents="""
---
kind: Ingress
apiVersion: networking.k8s.io/v1
metadata:
  name: test
spec:
  rules:
  - host: ingress1.apps.ploigos.xyz
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: foo
            port:
              name: http-listener
---
kind: Ingress
apiVersion: networking.k8s.io/v1
metadata:
  name: test
  annotations:
    route.openshift.io/termination: "edge"
spec:
  tls:
  - hosts:
    - ingress2.apps.ploigos.xyz
  rules:
  - host: ingress2.apps.ploigos.xyz
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: foo
            port:
              name: http-listener
---
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"route.openshift.io/v1","kind":"Route","metadata":{"annotations":{},"labels":{"app.kubernetes.io/instance":"s-mvn-jenkins-std-fruit-feature-results-refactor-dev"},"name":"fruit","namespace":"s-mvn-jenkins-std-fruit-feature-results-refactor-dev"},"spec":{"path":"/","port":{"targetPort":"http"},"to":{"kind":"Service","name":"fruit"}}}
    openshift.io/host.generated: "true"
  creationTimestamp: "2020-12-16T22:14:46Z"
  labels:
    app.kubernetes.io/instance: s-mvn-jenkins-std-fruit-feature-results-refactor-dev
  managedFields:
  - apiVersion: route.openshift.io/v1
    fieldsType: FieldsV1
    fieldsV1:
      f:metadata:
        f:annotations:
          .: {}
          f:kubectl.kubernetes.io/last-applied-configuration: {}
        f:labels:
          .: {}
          f:app.kubernetes.io/instance: {}
      f:spec:
        f:path: {}
        f:port:
          .: {}
          f:targetPort: {}
        f:to:
          f:kind: {}
          f:name: {}
          f:weight: {}
        f:wildcardPolicy: {}
    manager: argocd-application-controller
    operation: Update
    time: "2020-12-16T22:14:46Z"
  - apiVersion: route.openshift.io/v1
    fieldsType: FieldsV1
    fieldsV1:
      f:status:
        f:ingress: {}
    manager: openshift-router
    operation: Update
    time: "2020-12-16T22:14:46Z"
  name: fruit
  namespace: s-mvn-jenkins-std-fruit-feature-results-refactor-dev
  resourceVersion: "92938959"
  selfLink: /apis/route.openshift.io/v1/namespaces/s-mvn-jenkins-std-fruit-feature-results-refactor-dev/routes/fruit
  uid: f5d36e42-b894-49d9-9885-64ed7bc438db
spec:
  host: route1.apps.ploigos.xyz
  path: /
  port:
    targetPort: http
  to:
    kind: Service
    name: fruit
    weight: 100
  tls:
    termination: edge
  wildcardPolicy: None
status:
  ingress:
  - conditions:
    - lastTransitionTime: "2020-12-16T22:14:46Z"
      status: "True"
      type: Admitted
    host: route1.apps.ploigos.xyz
    routerCanonicalHostname: apps.ploigos.xyz
    routerName: default
    wildcardPolicy: None
---
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"route.openshift.io/v1","kind":"Route","metadata":{"annotations":{},"labels":{"app.kubernetes.io/instance":"s-mvn-jenkins-std-fruit-feature-results-refactor-dev"},"name":"fruit","namespace":"s-mvn-jenkins-std-fruit-feature-results-refactor-dev"},"spec":{"path":"/","port":{"targetPort":"http"},"to":{"kind":"Service","name":"fruit"}}}
    openshift.io/host.generated: "true"
  creationTimestamp: "2020-12-16T22:14:46Z"
  labels:
    app.kubernetes.io/instance: s-mvn-jenkins-std-fruit-feature-results-refactor-dev
  managedFields:
  - apiVersion: route.openshift.io/v1
    fieldsType: FieldsV1
    fieldsV1:
      f:metadata:
        f:annotations:
          .: {}
          f:kubectl.kubernetes.io/last-applied-configuration: {}
        f:labels:
          .: {}
          f:app.kubernetes.io/instance: {}
      f:spec:
        f:path: {}
        f:port:
          .: {}
          f:targetPort: {}
        f:to:
          f:kind: {}
          f:name: {}
          f:weight: {}
        f:wildcardPolicy: {}
    manager: argocd-application-controller
    operation: Update
    time: "2020-12-16T22:14:46Z"
  - apiVersion: route.openshift.io/v1
    fieldsType: FieldsV1
    fieldsV1:
      f:status:
        f:ingress: {}
    manager: openshift-router
    operation: Update
    time: "2020-12-16T22:14:46Z"
  name: fruit
  namespace: s-mvn-jenkins-std-fruit-feature-results-refactor-dev
  resourceVersion: "92938959"
  selfLink: /apis/route.openshift.io/v1/namespaces/s-mvn-jenkins-std-fruit-feature-results-refactor-dev/routes/fruit
  uid: f5d36e42-b894-49d9-9885-64ed7bc438db
spec:
  host: route2.apps.ploigos.xyz
  path: /
  port:
    targetPort: http
  to:
    kind: Service
    name: fruit
    weight: 100
  wildcardPolicy: None
status:
  ingress:
  - conditions:
    - lastTransitionTime: "2020-12-16T22:14:46Z"
      status: "True"
      type: Admitted
    host: route2.apps.ploigos.xyz.apps.ploigos.xyz
    routerCanonicalHostname: apps.ploigos.xyz
    routerName: default
    wildcardPolicy: None
""",
            expected_host_urls=[
                'http://ingress1.apps.ploigos.xyz',
                'https://ingress2.apps.ploigos.xyz',
                'https://route1.apps.ploigos.xyz',
                'http://route2.apps.ploigos.xyz'
            ]
        )

class TestStepImplementerDeployArgoCD__clone_repo(TestStepImplementerDeployArgoCDBase):
    @patch.object(sh, 'git')
    def test_ArgoCD__clone_repo_success_new_branch(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_url = 'git@git.ploigos.xyz:/foo/test.git'
        repo_branch = 'feature/test'
        user_email = 'test@ploigos.xyz'
        user_name = 'Test Robot'
        ArgoCD._ArgoCD__clone_repo(
            repo_dir=repo_dir,
            repo_url=repo_url,
            repo_branch=repo_branch,
            user_email=user_email,
            user_name=user_name
        )

        git_mock.clone.assert_called_once_with(
            repo_url,
            repo_dir,
            _out=Any(IOBase),
            _err=Any(IOBase)
        )
        git_mock.checkout.assert_called_once_with(
            repo_branch,
            _cwd=repo_dir,
            _out=Any(IOBase),
            _err=Any(IOBase)
        )
        git_mock.config.assert_has_calls([
            call(
                'user.email',
                user_email,
                _cwd=repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            ),
            call(
                'user.name',
                user_name,
                _cwd=repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
        ])

    @patch.object(sh, 'git')
    def test_ArgoCD__clone_repo_success_existing_branch(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_url = 'git@git.ploigos.xyz:/foo/test.git'
        repo_branch = 'feature/test'
        user_email = 'test@ploigos.xyz'
        user_name = 'Test Robot'

        git_mock.checkout.side_effect = [
            sh.ErrorReturnCode('git', b'mock out', b'mock git checkout branch does not exist'),
            None
        ]

        ArgoCD._ArgoCD__clone_repo(
            repo_dir=repo_dir,
            repo_url=repo_url,
            repo_branch=repo_branch,
            user_email=user_email,
            user_name=user_name
        )

        git_mock.clone.assert_called_once_with(
            repo_url,
            repo_dir,
            _out=Any(IOBase),
            _err=Any(IOBase)
        )
        git_mock.checkout.assert_has_calls([
            call(
                repo_branch,
                _cwd=repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            ),
            call(
                '-b',
                repo_branch,
                _cwd=repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
        ])
        git_mock.config.assert_has_calls([
            call(
                'user.email',
                user_email,
                _cwd=repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            ),
            call(
                'user.name',
                user_name,
                _cwd=repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
        ])

    @patch.object(sh, 'git')
    def test_ArgoCD__clone_repo_fail_clone(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_url = 'git@git.ploigos.xyz:/foo/test.git'
        repo_branch = 'feature/test'
        user_email = 'test@ploigos.xyz'
        user_name = 'Test Robot'

        git_mock.clone.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('git', b'mock out', b'mock git clone error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error cloning repository \({repo_url}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git clone error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__clone_repo(
                repo_dir=repo_dir,
                repo_url=repo_url,
                repo_branch=repo_branch,
                user_email=user_email,
                user_name=user_name
            )

            git_mock.clone.assert_called_once_with(
                repo_url,
                repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
            git_mock.checkout.assert_not_called()
            git_mock.config.assert_not_called()

    @patch.object(sh, 'git')
    def test_ArgoCD__clone_repo_fail_existing_branch(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_url = 'git@git.ploigos.xyz:/foo/test.git'
        repo_branch = 'feature/test'
        user_email = 'test@ploigos.xyz'
        user_name = 'Test Robot'

        git_mock.checkout.side_effect = [
            sh.ErrorReturnCode('git', b'mock out', b'mock git checkout branch does not exist'),
            sh.ErrorReturnCode('git', b'mock out', b'mock git checkout new branch error'),
        ]

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Unexpected error checking out new or existing branch \({repo_branch}\)"
                rf" from repository \({repo_url}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git checkout new branch error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__clone_repo(
                repo_dir=repo_dir,
                repo_url=repo_url,
                repo_branch=repo_branch,
                user_email=user_email,
                user_name=user_name
            )

            git_mock.clone.assert_called_once_with(
                repo_url,
                repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
            git_mock.checkout.assert_has_calls([
                call(
                    repo_branch,
                    _cwd=repo_dir,
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                ),
                call(
                    '-b',
                    repo_branch,
                    _cwd=repo_dir,
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                )
            ])
            git_mock.config.assert_not_called()

    @patch.object(sh, 'git')
    def test_ArgoCD__clone_repo_fail_config_email(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_url = 'git@git.ploigos.xyz:/foo/test.git'
        repo_branch = 'feature/test'
        user_email = 'test@ploigos.xyz'
        user_name = 'Test Robot'

        git_mock.config.side_effect = [
            sh.ErrorReturnCode('git', b'mock out', b'mock git config email error'),
            None
        ]

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Unexpected error configuring git user.email \({user_email}\)"
                rf" and user.name \({user_name}\) for repository \({repo_url}\)"
                rf" in directory \({repo_dir}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git config email error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__clone_repo(
                repo_dir=repo_dir,
                repo_url=repo_url,
                repo_branch=repo_branch,
                user_email=user_email,
                user_name=user_name
            )

            git_mock.clone.assert_called_once_with(
                repo_url,
                repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
            git_mock.checkout.assert_has_calls([
                call(
                    repo_branch,
                    _cwd=repo_dir,
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                ),
                call(
                    '-b',
                    repo_branch,
                    _cwd=repo_dir,
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                )
            ])
            git_mock.config.assert_called_once_with(
                'user.email',
                user_email,
                _cwd=repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch.object(sh, 'git')
    def test_ArgoCD__clone_repo_fail_config_name(self, git_mock):
        repo_dir = '/does/not/matter'
        repo_url = 'git@git.ploigos.xyz:/foo/test.git'
        repo_branch = 'feature/test'
        user_email = 'test@ploigos.xyz'
        user_name = 'Test Robot'

        git_mock.config.side_effect = [
            None,
            sh.ErrorReturnCode('git', b'mock out', b'mock git config name error')
        ]

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Unexpected error configuring git user.email \({user_email}\)"
                rf" and user.name \({user_name}\) for repository \({repo_url}\)"
                rf" in directory \({repo_dir}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git config name error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__clone_repo(
                repo_dir=repo_dir,
                repo_url=repo_url,
                repo_branch=repo_branch,
                user_email=user_email,
                user_name=user_name
            )

            git_mock.clone.assert_called_once_with(
                repo_url,
                repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
            git_mock.checkout.assert_has_calls([
                call(
                    repo_branch,
                    _cwd=repo_dir,
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                ),
                call(
                    '-b',
                    repo_branch,
                    _cwd=repo_dir,
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                )
            ])
            git_mock.config.assert_has_calls([
                call(
                    'user.email',
                    user_email,
                    _cwd=repo_dir,
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                ),
                call(
                    'user.name',
                    user_name,
                    _cwd=repo_dir,
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                )
            ])

class TestStepImplementerDeployArgoCD__get_repo_branch(TestStepImplementerDeployArgoCDBase):
    @patch.object(sh, 'git')
    def test_ArgoCD__get_repo_branch_sucecss(self, git_mock):
        git_mock.side_effect = create_sh_side_effect(mock_stdout="feature/test")

        repo_branch = ArgoCD._ArgoCD__get_repo_branch()
        self.assertEqual(repo_branch, 'feature/test')
        git_mock.assert_called_once_with(
            'rev-parse',
            '--abbrev-ref',
            'HEAD'
        )

    @patch.object(sh, 'git')
    def test_ArgoCD__get_repo_branch_fail(self, git_mock):
        git_mock.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('git', b'mock out', b'mock git rev-parse error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Unexpected error getting checkedout git repository branch"
                r" of the working directory."
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git rev-parse error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__get_repo_branch()
            git_mock.assert_called_once_with(
                'rev-parse',
                '--abbrev-ref',
                'HEAD'
            )

class TestStepImplementerDeployArgoCD__git_tag_and_push(TestStepImplementerDeployArgoCDBase):
    @patch.object(sh, 'git')
    def test_ArgoCD__git_tag_and_push_success_ssh(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None
        ArgoCD._ArgoCD__git_tag_and_push(
            repo_dir=repo_dir,
            tag=tag,
            url=url
        )

        git_mock.push.assert_has_calls([
            call(
                _cwd=repo_dir,
                _out=Any(IOBase)
            ),
            call(
                '--tag',
                _cwd=repo_dir,
                _out=Any(IOBase)
            )
        ])
        git_mock.tag.assert_called_once_with(
            tag,
            '-f',
            _cwd=repo_dir,
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch.object(sh, 'git')
    def test_ArgoCD__git_tag_and_push_success_https_url(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = 'https://user:pass@git.ploigos.xyz'
        ArgoCD._ArgoCD__git_tag_and_push(
            repo_dir=repo_dir,
            tag=tag,
            url=url
        )

        git_mock.push.bake().assert_has_calls([
            call(
                _cwd=repo_dir,
                _out=Any(IOBase)
            ),
            call(
                '--tag',
                _cwd=repo_dir,
                _out=Any(IOBase)
            )
        ])
        git_mock.tag.assert_called_once_with(
            tag,
            '-f',
            _cwd=repo_dir,
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch.object(sh, 'git')
    def test_ArgoCD__git_tag_and_push_fail_commit(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None

        git_mock.push.side_effect = [
            sh.ErrorReturnCode('git', b'mock out', b'mock git push error'),
            create_sh_side_effect()
        ]

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error pushing commits from repository directory \({repo_dir}\) to"
                rf" repository \({url}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git push error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__git_tag_and_push(
                repo_dir=repo_dir,
                tag=tag,
                url=url
            )

            git_mock.push.assert_has_calls([
                call(
                    _cwd=repo_dir,
                    _out=Any(IOBase)
                )
            ])

            git_mock.tag.assert_not_called()

    @patch.object(sh, 'git')
    def test_ArgoCD__git_tag_and_push_fail_tag(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None

        git_mock.tag.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock git tag error')

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error tagging repository \({repo_dir}\) with tag \({tag}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git tag error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__git_tag_and_push(
                repo_dir=repo_dir,
                tag=tag,
                url=url
            )

            git_mock.push.assert_called_once_with(
                _cwd=repo_dir,
                _out=Any(IOBase)
            )

            git_mock.tag.assert_called_once_with(
                tag,
                '-f',
                _cwd=repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch.object(sh, 'git')
    def test_ArgoCD__git_tag_and_push_fail_push_tag(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None

        git_mock.push.side_effect = [
            create_sh_side_effect(),
            sh.ErrorReturnCode('git', b'mock out', b'mock git push tag error')
        ]

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error pushing tags from repository directory \({repo_dir}\) to"
                rf" repository \({url}\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git push tag error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__git_tag_and_push(
                repo_dir=repo_dir,
                tag=tag,
                url=url
            )

            git_mock.push.bake().assert_has_calls([
                call(
                    _cwd=repo_dir,
                    _out=Any(IOBase)
                ),
                call(
                    '--tag',
                    _cwd=repo_dir,
                    _out=Any(IOBase)
                )
            ])

            git_mock.tag.assert_called_once_with(
                tag,
                '-f',
                _cwd=repo_dir,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch.object(sh, 'git')
    def test_ArgoCD__git_tag_and_push_override_tls(self, git_mock):
        repo_dir = '/does/not/matter'
        tag = 'v0.42.0'
        url = None
        ArgoCD._ArgoCD__git_tag_and_push(
            repo_dir=repo_dir,
            tag=tag,
            url=url,
            force_push_tags=True
        )

        git_mock.push.assert_has_calls([
            call(
                _cwd=repo_dir,
                _out=Any(IOBase)
            ),
            call(
                '--tag',
                '--force',
                _cwd=repo_dir,
                _out=Any(IOBase)
            )
        ])
        git_mock.tag.assert_called_once_with(
            tag,
            '-f',
            _cwd=repo_dir,
            _out=Any(IOBase),
            _err=Any(IOBase)
        )


class TestStepImplementerDeployArgoCD__git_commit_file(TestStepImplementerDeployArgoCDBase):
    @patch.object(sh, 'git')
    def test_ArgoCD__git_commit_file_success(self, git_mock):
        ArgoCD._ArgoCD__git_commit_file(
            git_commit_message='hello world',
            file_path='charts/foo/values-DEV.yaml',
            repo_dir='/does/not/matter'
        )

        git_mock.add.assert_called_once_with(
            'charts/foo/values-DEV.yaml',
            _cwd='/does/not/matter',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

        git_mock.commit.assert_called_once_with(
            '--allow-empty',
            '--all',
            '--message', 'hello world',
            _cwd='/does/not/matter',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch.object(sh, 'git')
    def test_ArgoCD__git_commit_file_fail_add(self, git_mock):
        git_mock.add.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('git', b'mock out', b'mock git add error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Unexpected error adding file \(charts/foo/values-DEV.yaml\) to commit"
                r" in git repository \(/does/not/matter\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git add error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__git_commit_file(
                git_commit_message='hello world',
                file_path='charts/foo/values-DEV.yaml',
                repo_dir='/does/not/matter'
            )

            git_mock.add.assert_called_once_with(
                'charts/foo/values-DEV.yaml',
                _cwd='/does/not/matter',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.commit.assert_not_called()

    @patch.object(sh, 'git')
    def test_ArgoCD__git_commit_file_fail_commit(self, git_mock):
        git_mock.commit.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('git', b'mock out', b'mock git commit error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Unexpected error commiting file \(charts/foo/values-DEV.yaml\)"
                r" in git repository \(/does/not/matter\):"
                r".*RAN: git"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock git commit error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__git_commit_file(
                git_commit_message='hello world',
                file_path='charts/foo/values-DEV.yaml',
                repo_dir='/does/not/matter'
            )

            git_mock.add.assert_called_once_with(
                'charts/foo/values-DEV.yaml',
                _cwd='/does/not/matter',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.commit.assert_called_once_with(
                '--allow-empty',
                '--all',
                '--message', 'hello world',
                _cwd='/does/not/matter',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

class TestStepImplementerDeployArgoCD__argocd_sign_in(TestStepImplementerDeployArgoCDBase):
    @patch('sh.argocd', create=True)
    def test_ArgoCD__argocd_sign_in_success_not_insecure(self, argocd_mock):
        argocd_api='argo.dev.ploigos.xyz'
        username='test'
        password='secrettest'
        ArgoCD._ArgoCD__argocd_sign_in(
            argocd_api=argocd_api,
            username=username,
            password=password,
            insecure=False
        )

        argocd_mock.login.assert_called_once_with(
            argocd_api,
            f'--username={username}',
            f'--password={password}',
            None,
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch('sh.argocd', create=True)
    def test_ArgoCD__argocd_sign_in_success_insecure(self, argocd_mock):
        argocd_api='argo.dev.ploigos.xyz'
        username='test'
        password='secrettest'
        ArgoCD._ArgoCD__argocd_sign_in(
            argocd_api=argocd_api,
            username=username,
            password=password,
            insecure=True
        )

        argocd_mock.login.assert_called_once_with(
            argocd_api,
            f'--username={username}',
            f'--password={password}',
            '--insecure',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch('sh.argocd', create=True)
    def test_ArgoCD__argocd_sign_in_fail_not_insecure(self, argocd_mock):
        argocd_api='argo.dev.ploigos.xyz'
        username='test'
        password='secrettest'

        argocd_mock.login.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('argocd', b'mock out', b'mock login error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error logging in to ArgoCD:"
                r".*RAN: argocd"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock login error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__argocd_sign_in(
                argocd_api=argocd_api,
                username=username,
                password=password,
                insecure=False
            )

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                f'--username={username}',
                f'--password={password}',
                None,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

class TestStepImplementerDeployArgoCD__argocd_add_target_cluster(TestStepImplementerDeployArgoCDBase):
    @patch('sh.argocd', create=True)
    def test_ArgoCD__argocd_add_target_cluster_default_cluster(self, argocd_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._ArgoCD__argocd_add_target_cluster(
                kube_api='https://kubernetes.default.svc',
                kube_api_skip_tls=False
            )

            argocd_mock.cluster.add.assert_not_called()

    @patch('sh.argocd', create=True)
    def test_ArgoCD__argocd_add_target_cluster_custom_cluster_kube_skip_tls_true(self, argocd_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            expected_config_argocd_cluster_context_file_contents = """---
apiVersion: v1
kind: Config
current-context: https://api.dev.ploigos.xyz-context
clusters:
- cluster:
    kube-api-skip-tls: true
    server: https://api.dev.ploigos.xyz
  name: default-cluster
contexts:
- context:
    cluster: default-cluster
    user: default-user
  name: https://api.dev.ploigos.xyz-context
preferences:
users:
- name: default-user
  user:
    token: abc123
"""

            step_implementer._ArgoCD__argocd_add_target_cluster(
                kube_api='https://api.dev.ploigos.xyz',
                kube_api_token='abc123',
                kube_api_skip_tls=True
            )

            config_argocd_cluster_context_file_path = os.path.join(
                work_dir_path,
                'deploy',
                'config-argocd-cluster-context.yaml'
            )
            argocd_mock.cluster.add.assert_called_once_with(
                '--kubeconfig', config_argocd_cluster_context_file_path,
                'https://api.dev.ploigos.xyz-context',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            with open(config_argocd_cluster_context_file_path, 'r') as \
                    config_argocd_cluster_context_file:
                config_argocd_cluster_context_file_contents = \
                    config_argocd_cluster_context_file.read()


                self.assertEqual(
                    config_argocd_cluster_context_file_contents,
                    expected_config_argocd_cluster_context_file_contents
                )

    @patch('sh.argocd', create=True)
    def test_ArgoCD__argocd_add_target_cluster_custom_cluster_kube_skip_tls_false(self, argocd_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            expected_config_argocd_cluster_context_file_contents = """---
apiVersion: v1
kind: Config
current-context: https://api.dev.ploigos.xyz-context
clusters:
- cluster:
    kube-api-skip-tls: false
    server: https://api.dev.ploigos.xyz
  name: default-cluster
contexts:
- context:
    cluster: default-cluster
    user: default-user
  name: https://api.dev.ploigos.xyz-context
preferences:
users:
- name: default-user
  user:
    token: abc123
"""

            step_implementer._ArgoCD__argocd_add_target_cluster(
                kube_api='https://api.dev.ploigos.xyz',
                kube_api_token='abc123',
                kube_api_skip_tls=False
            )

            config_argocd_cluster_context_file_path = os.path.join(
                work_dir_path,
                'deploy',
                'config-argocd-cluster-context.yaml'
            )
            argocd_mock.cluster.add.assert_called_once_with(
                '--kubeconfig', config_argocd_cluster_context_file_path,
                'https://api.dev.ploigos.xyz-context',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            with open(config_argocd_cluster_context_file_path, 'r') as \
                    config_argocd_cluster_context_file:
                config_argocd_cluster_context_file_contents = \
                    config_argocd_cluster_context_file.read()


                self.assertEqual(
                    config_argocd_cluster_context_file_contents,
                    expected_config_argocd_cluster_context_file_contents
                )

    @patch('sh.argocd', create=True)
    def test_ArgoCD__argocd_add_target_cluster_fail_custom_cluster_kube_skip_tls_true(self, argocd_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            expected_config_argocd_cluster_context_file_contents = """---
apiVersion: v1
kind: Config
current-context: https://api.dev.ploigos.xyz-context
clusters:
- cluster:
    kube-api-skip-tls: true
    server: https://api.dev.ploigos.xyz
  name: default-cluster
contexts:
- context:
    cluster: default-cluster
    user: default-user
  name: https://api.dev.ploigos.xyz-context
preferences:
users:
- name: default-user
  user:
    token: abc123
"""

            argocd_mock.cluster.add.side_effect = create_sh_side_effect(
                exception=sh.ErrorReturnCode('argocd', b'mock out', b'mock cluster add error')
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    rf"Error adding cluster \(https://api.dev.ploigos.xyz\) to ArgoCD:"
                    r".*RAN: argocd"
                    r".*STDOUT:"
                    r".*mock out"
                    r".*STDERR:"
                    r".*mock cluster add error",
                    re.DOTALL
                )
            ):
                step_implementer._ArgoCD__argocd_add_target_cluster(
                    kube_api='https://api.dev.ploigos.xyz',
                    kube_api_token='abc123',
                    kube_api_skip_tls=True
                )

                config_argocd_cluster_context_file_path = os.path.join(
                    work_dir_path,
                    'deploy',
                    'config-argocd-cluster-context.yaml'
                )
                argocd_mock.cluster.add.assert_called_once_with(
                    '--kubeconfig', config_argocd_cluster_context_file_path,
                    'https://api.dev.ploigos.xyz-context',
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                )

                with open(config_argocd_cluster_context_file_path, 'r') as \
                        config_argocd_cluster_context_file:
                    config_argocd_cluster_context_file_contents = \
                        config_argocd_cluster_context_file.read()


                    self.assertEqual(
                        config_argocd_cluster_context_file_contents,
                        expected_config_argocd_cluster_context_file_contents
                    )


class TestStepImplementerDeployArgoCD__argocd_app_create_or_update(TestStepImplementerDeployArgoCDBase):
    @patch('sh.argocd', create=True)
    def test__argocd_app_create_or_update_success_sync_auto_no_extra_values_files(self, argocd_mock):
        argocd_app_name = 'test'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        auto_sync = True
        values_files = []
        ArgoCD._ArgoCD__argocd_app_create_or_update(
            argocd_app_name=argocd_app_name,
            repo=repo,
            revision=revision,
            path=path,
            dest_server=dest_server,
            auto_sync=auto_sync,
            values_files=values_files
        )

        sync_policy = 'automated'
        values_params = None
        argocd_mock.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={argocd_app_name}',
            f'--sync-policy={sync_policy}',
            values_params,
            '--upsert',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch('sh.argocd', create=True)
    def test__argocd_app_create_or_update_success_sync_none_no_extra_values_files(self, argocd_mock):
        argocd_app_name = 'test'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        auto_sync = False
        values_files = []
        ArgoCD._ArgoCD__argocd_app_create_or_update(
            argocd_app_name=argocd_app_name,
            repo=repo,
            revision=revision,
            path=path,
            dest_server=dest_server,
            auto_sync=auto_sync,
            values_files=values_files
        )

        sync_policy = 'none'
        values_params = None
        argocd_mock.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={argocd_app_name}',
            f'--sync-policy={sync_policy}',
            values_params,
            '--upsert',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch('sh.argocd', create=True)
    def test__argocd_app_create_or_update_success_sync_auto_1_values_files(self, argocd_mock):
        argocd_app_name = 'test'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        auto_sync = True
        values_files = ['values-foo.yaml']
        ArgoCD._ArgoCD__argocd_app_create_or_update(
            argocd_app_name=argocd_app_name,
            repo=repo,
            revision=revision,
            path=path,
            dest_server=dest_server,
            auto_sync=auto_sync,
            values_files=values_files
        )

        sync_policy = 'automated'
        values_params = ['--values=values-foo.yaml']
        argocd_mock.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={argocd_app_name}',
            f'--sync-policy={sync_policy}',
            values_params,
            '--upsert',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch('sh.argocd', create=True)
    def test__argocd_app_create_or_update_success_sync_auto_2_values_files(self, argocd_mock):
        argocd_app_name = 'test'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        auto_sync = True
        values_files = ['values-foo.yaml', 'values-DEV.yaml']
        ArgoCD._ArgoCD__argocd_app_create_or_update(
            argocd_app_name=argocd_app_name,
            repo=repo,
            revision=revision,
            path=path,
            dest_server=dest_server,
            auto_sync=auto_sync,
            values_files=values_files
        )

        sync_policy = 'automated'
        values_params = ['--values=values-foo.yaml', '--values=values-DEV.yaml']
        argocd_mock.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={argocd_app_name}',
            f'--sync-policy={sync_policy}',
            values_params,
            '--upsert',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch('sh.argocd', create=True)
    def test__argocd_app_create_or_update_fail_sync_auto_1_values_files(self, argocd_mock):
        argocd_mock.app.create.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('argocd', b'mock out', b'mock create error')
        )

        argocd_app_name = 'test'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        auto_sync = True
        values_files = ['values-foo.yaml']

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error creating or updating ArgoCD app \({argocd_app_name}\):"
                r".*RAN: argocd"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock create error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__argocd_app_create_or_update(
                argocd_app_name=argocd_app_name,
                repo=repo,
                revision=revision,
                path=path,
                dest_server=dest_server,
                auto_sync=auto_sync,
                values_files=values_files
            )

        sync_policy = 'automated'
        values_params = ['--values=values-foo.yaml']
        argocd_mock.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={argocd_app_name}',
            f'--sync-policy={sync_policy}',
            values_params,
            '--upsert',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

class TestStepImplementerDeployArgoCD__argocd_app_sync(TestStepImplementerDeployArgoCDBase):
    @patch('sh.argocd', create=True)
    def test__argocd_app_sync_success(self, argocd_mock):
        ArgoCD._ArgoCD__argocd_app_sync(
            argocd_app_name='test',
            argocd_sync_timeout_seconds=120
        )

        argocd_mock.app.sync.assert_called_once_with(
            '--prune',
            '--timeout', 120,
            'test',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )
        argocd_mock.app.wait.assert_called_once_with(
            '--timeout', 120,
            '--health',
            'test',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

    @patch('sh.argocd', create=True)
    def test__argocd_app_sync_fail_sync(self, argocd_mock):
        argocd_mock.app.sync.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('argocd', b'mock out', b'mock sync error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Error synchronization ArgoCD Application \(test\):"
                r".*RAN: argocd"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock sync error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__argocd_app_sync(
                argocd_app_name='test',
                argocd_sync_timeout_seconds=120
            )

        argocd_mock.app.sync.assert_called_once_with(
            '--prune',
            '--timeout', 120,
            'test',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )
        argocd_mock.app.wait.assert_not_called()

    @patch('sh.argocd', create=True)
    def test__argocd_app_sync_fail_wait(self, argocd_mock):
        argocd_mock.app.wait.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('argocd', b'mock out', b'mock wait error')
        )

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Error waiting for ArgoCD Application \(test\) synchronization:"
                r".*RAN: argocd"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock wait error",
                re.DOTALL
            )
        ):
            ArgoCD._ArgoCD__argocd_app_sync(
                argocd_app_name='test',
                argocd_sync_timeout_seconds=120
            )

        argocd_mock.app.sync.assert_called_once_with(
            '--prune',
            '--timeout', 120,
            'test',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )
        argocd_mock.app.wait.assert_called_once_with(
            '--timeout', 120,
            '--health',
            'test',
            _out=Any(IOBase),
            _err=Any(IOBase)
        )

class TestStepImplementerDeployArgoCD__argocd_get_app_manifest(TestStepImplementerDeployArgoCDBase):
    @patch('sh.argocd', create=True)
    def test___argocd_get_app_manifest_success_live(self, argocd_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            arogcd_app_manifest_file = step_implementer._ArgoCD__argocd_get_app_manifest(
                argocd_app_name='test',
                source='live'
            )

            self.assertIsNotNone(arogcd_app_manifest_file)
            argocd_mock.app.manifests.assert_called_once_with(
                '--source=live',
                'test',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.argocd', create=True)
    def test___argocd_get_app_manifest_success_git(self, argocd_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            arogcd_app_manifest_file = step_implementer._ArgoCD__argocd_get_app_manifest(
                argocd_app_name='test',
                source='git'
            )

            self.assertIsNotNone(arogcd_app_manifest_file)
            argocd_mock.app.manifests.assert_called_once_with(
                '--source=git',
                'test',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.argocd', create=True)
    def test___argocd_get_app_manifest_fail(self, argocd_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config={},
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            argocd_mock.app.manifests.side_effect = create_sh_side_effect(
                exception=sh.ErrorReturnCode('argocd', b'mock out', b'mock error')
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error reading ArgoCD Application \(invalid\) manifest:"
                    r".*RAN: argocd"
                    r".*STDOUT:"
                    r".*mock out"
                    r".*STDERR:"
                    r".*mock error",
                    re.DOTALL
                )
            ):
                arogcd_app_manifest_file = step_implementer._ArgoCD__argocd_get_app_manifest(
                    argocd_app_name='invalid',
                    source='live'
                )

                self.assertIsNotNone(arogcd_app_manifest_file)
                argocd_mock.app.manifests.assert_called_once_with(
                    '--source=live',
                    'invalid',
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                )
