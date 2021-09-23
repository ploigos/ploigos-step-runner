import os
import re
from io import IOBase
from unittest.mock import call, patch
from testfixtures import TempDirectory
from ploigos_step_runner import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.step_implementers.deploy.argocd_delete import ArgoCDDelete

class TestStepImplementerDeployArgoCDBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            parent_work_dir_path='',
            environment=None
    ):
        return self.create_given_step_implementer(
            step_implementer=ArgoCDDelete,
            step_config=step_config,
            step_name='delete',
            implementer='ArgoCDDelete',
            parent_work_dir_path=parent_work_dir_path,
            environment=environment
        )

class TestStepImplementerArgoCDDelete_run_step(TestStepImplementerDeployArgoCDBase):
    # @patch.object(
    #     ArgoCDDelete,
    #     '_argocd_get_app_manifest',
    #     return_value='/does/not/matter/manifest.yaml'
    # )
    # @patch.object(
    #     ArgoCDDelete,
    #     '_get_deployment_config_helm_chart_environment_values_file',
    #     return_value='values-PROD.yaml'
    # )
    # @patch.object(ArgoCDDelete, '_get_app_name', return_value='test-app-name')
    # @patch.object(ArgoCDDelete, '_update_yaml_file_value')
    # @patch.object(ArgoCDDelete, '_get_deployment_config_repo_tag', return_value='v0.42.0')
    # @patch.object(ArgoCDDelete, '_git_tag_and_push_deployment_config_repo')
    @patch.object(ArgoCDDelete, '_argocd_add_target_cluster')
    # @patch.object(ArgoCDDelete, '_clone_repo', return_value='/does/not/matter')
    # @patch.object(ArgoCDDelete, '_git_commit_file')
    @patch.object(ArgoCDDelete, '_argocd_sign_in')
    # @patch.object(ArgoCDDelete, '_argocd_app_create_or_update')
    # @patch.object(ArgoCDDelete, '_argocd_app_sync')
    # @patch.object(
    #     ArgoCDDelete,
    #     '_get_deployed_host_urls',
    #     return_value=['https://fruits.ploigos.xyz']
    # )
    # @patch.object(ArgoCDDelete, '_get_repo_branch', return_value='feature/test')
    @patch.object(ArgoCDDelete, '_get_argocd_propagation_policy', return_value=True)
    @patch.object(ArgoCDDelete, '_get_argocd_cascade', return_value=True )
    # @patch.object(ArgoCDDelete, '_get_kube_api_uri')
    # @patch.object(ArgoCDDelete, '_get_kube_api_token')
    # @patch.object(ArgoCDDelete, '_get_kube_api_skip_tls')
    def test_run_step_success(
            self,
            get_argocd_cascade_mock,
            get_argocd_propagation_policy_mock,
            argocd_sign_in_mock,
            argocd_add_target_cluster_mock
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
                'argocd_cascade': True,
                'argocd_propagation_policy': True
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )

            actual_step_results = step_implementer._run_step()
            expected_step_result = StepResult(
                step_name='delete',
                sub_step_name='ArgoCDDelete',
                sub_step_implementer_name='ArgoCDDelete',
                environment='PROD'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Error deploying to environment (PROD):' \
                                           ' mock failed to clone repo error'
            expected_step_result.add_artifact(
                name='argocd-app-name',
                value='test-app-name'
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
            # get_app_name_mock.assert_called_once_with()
            # get_argocd_propagation_policy_mock.assert_called_once_with()
            # get_argocd_cascade_mock.assert_called_once_with()
            # get_argocd_propagation_policy_mock.assert_called_once_with()
            # get_kube_api_skip_tls_mock.assert_called_once_with()
            # get_kube_api_token_mock.assert_called_once_with()
            # get_kube_api_uri_mock.assert_called_once_with()
