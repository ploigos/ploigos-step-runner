import os
from unittest.mock import ANY, patch

import sh
from testfixtures import TempDirectory
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import create_sh_side_effect
from ploigos_step_runner.step_implementers.undeploy.argocd_delete import ArgoCDDelete


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


class TestStepImplementerArgoCDDelete_Other(TestStepImplementerDeployArgoCDBase):
    def test_step_implementer_config_defaults(
        self
    ):
        defaults = ArgoCDDelete.step_implementer_config_defaults()
        expected_defaults = {
            'argocd-cascade': True,
            'argocd-propagation-policy': 'foreground',
            'argocd-skip-tls': False,
            'kube-api-skip-tls': False,
            'kube-api-uri': 'https://kubernetes.default.svc'
        }
        self.assertEqual(defaults, expected_defaults)

    def test_required_config_or_result_keys(
        self
    ):
        required_keys = ArgoCDDelete._required_config_or_result_keys()
        expected_required_keys = [
            'application-name',
            'argocd-api',
            'argocd-cascade',
            'argocd-password',
            'argocd-propagation-policy',
            'argocd-skip-tls',
            'argocd-username',
            'branch',
            'kube-api-skip-tls',
            'kube-api-uri',
            'organization',
            'service-name'
        ]
        self.assertEqual(required_keys, expected_required_keys)


class TestStepImplementerArgoCDDelete_run_step(TestStepImplementerDeployArgoCDBase):
    @patch.object(ArgoCDDelete, '_get_app_name', return_value='test-app-name')
    @patch.object(ArgoCDDelete, '_argocd_sign_in')
    @patch('sh.argocd', create=True)
    def test_run_step_success(
            self,
            mock_argocd,
            argocd_sign_in_mock,
            get_app_name_mock
    ):
        with TempDirectory() as temp_dir:
            # Test setup: Test inputs / mocks
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            argocd_cascade = True
            argocd_propagation_policy = 'background'

            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'argocd-cascade': argocd_cascade,
                'argocd-propagation-policy': argocd_propagation_policy
            }

            # Test setup: Expected outputs
            expected_step_result = StepResult(
                step_name='delete',
                sub_step_name='ArgoCDDelete',
                sub_step_implementer_name='ArgoCDDelete',
                environment='PROD'
            )
            expected_step_result.success = True
            expected_step_result.add_artifact(
                name='argocd-app-name',
                value='test-app-name'
            )

            # Test execution
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )
            actual_step_results = step_implementer._run_step()

            # Test verification: Step results
            self.assertEqual(actual_step_results, expected_step_result)

            # Test verification: Mock method calls
            get_app_name_mock.assert_called_once_with()
            argocd_sign_in_mock.assert_called_once_with(
                argocd_api=step_config['argocd-api'],
                username=step_config['argocd-username'],
                password=step_config['argocd-password'],
                insecure=step_config['argocd-skip-tls']
            )
            mock_argocd.app.delete.assert_called_once_with(
                'test-app-name',
                f'--cascade={argocd_cascade}',
                f'--propagation-policy={argocd_propagation_policy}',
                '--yes',
                _out=ANY,
                _err=ANY
            )

    @patch.object(ArgoCDDelete, '_get_app_name', return_value='test-app-name')
    @patch.object(ArgoCDDelete, '_argocd_sign_in')
    @patch('sh.argocd', create=True)
    def test_run_step_failure(
            self,
            mock_argocd,
            argocd_sign_in_mock,
            get_app_name_mock
    ):
        with TempDirectory() as temp_dir:
            # Test setup: Test inputs / mocks
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            argocd_cascade = True
            argocd_propagation_policy = 'background'
            environment = 'PROD'

            step_config = {
                'argocd-username': 'argo-username',
                'argocd-password': 'argo-password',
                'argocd-api': 'https://argo.ploigos.xyz',
                'argocd-skip-tls': False,
                'argocd-cascade': argocd_cascade,
                'argocd-propagation-policy': argocd_propagation_policy
            }

            # Test setup: Expected outputs
            delete_error_return = sh.ErrorReturnCode('argocd', b'mock out', b'mock argocd sign-in failure')
            delete_failure_error_msg = f"Error deleting ArgoCD app (test-app-name): {delete_error_return}"
            delete_exception = StepRunnerException(delete_failure_error_msg)

            expected_step_result = StepResult(
                step_name='delete',
                sub_step_name='ArgoCDDelete',
                sub_step_implementer_name='ArgoCDDelete',
                environment=environment
            )
            expected_step_result.success = False
            expected_step_result.message = f"Error deleting environment ({environment}):" \
                                           f" {str(delete_exception)}"
            expected_step_result.add_artifact(
                name='argocd-app-name',
                value='test-app-name'
            )

            # Test setup: Mock behaviors
            mock_argocd.app.delete.side_effect = create_sh_side_effect(
                exception=delete_error_return
            )

            # Test execution
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )
            actual_step_results = step_implementer._run_step()

            # Test verification: Step results
            self.assertEqual(actual_step_results, expected_step_result)

            # Test verification: Mock method calls
            get_app_name_mock.assert_called_once_with()
            argocd_sign_in_mock.assert_called_once_with(
                argocd_api=step_config['argocd-api'],
                username=step_config['argocd-username'],
                password=step_config['argocd-password'],
                insecure=step_config['argocd-skip-tls']
            )
