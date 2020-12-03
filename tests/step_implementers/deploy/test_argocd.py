from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tssc.step_implementers.deploy.argocd import ArgoCD

class TestStepImplementerDeployArgoCD(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Git,
            step_config=step_config,
            step_name='deploy',
            implementer='ArgoCD',
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = ArgoCD.step_implementer_config_defaults()
        expected_defaults = {
            'values-yaml-directory': './cicd/Deployment',
            'values-yaml-template': 'values.yaml.j2',
            'argocd-sync-timeout-seconds': 60,
            'argocd-auto-sync': 'false',
            'insecure-skip-tls-verify': 'true',
            'kube-api-uri': 'https://kubernetes.default.svc',
            'argocd-helm-chart-path': './',
            'git-friendly-name': 'TSSC'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = ArgoCD._required_config_or_result_keys()
        expected_required_keys = [
            'argocd-username',
            'argocd-password',
            'argocd-api',
            'helm-config-repo',
            'git-email',
            'container-image-uri',
            'tag'
        ]
        self.assertEqual(required_keys, expected_required_keys)
