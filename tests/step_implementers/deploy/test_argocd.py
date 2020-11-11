import shutil
import tempfile
import types
import unittest
from io import IOBase
from unittest.mock import MagicMock, patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.test_utils import *
from tssc.config.config import Config
from tssc.step_implementers.deploy import ArgoCD


class TestStepImplementerDeployArgoCD(BaseStepImplementerTestCase):
    @staticmethod
    def __create_git_rev_parse_side_effect(abbreviated_ref):
        def git_rev_parse_side_effect(*args, **kwargs):
            if (args[0] == 'rev-parse') and (args[1] == '--abbrev-ref') and (args[2] == 'HEAD'):
                return abbreviated_ref

        return git_rev_parse_side_effect

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_login_error(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
            )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            argocd_mock.login.side_effect = sh.ErrorReturnCode('argocd', b'stdout', b'stderror')

            with self.assertRaises(RuntimeError):
                self.run_step_test_with_result_validation(temp_dir, 'deploy', config, expected_step_results, runtime_args, environment_name)

    def test_deploy_git_username_missing(self):

        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : 'admin',
                            'argocd-password' : 'password',
                            'argocd-api' : 'http://argocd.example.com',
                            'helm-config-repo' : 'http://gitrepo.com/helm-confg-repo.git',
                            'git-email' : 'nappspo+tssc@redhat.com'
                        }
                    }
                }
            }

            expected_step_results = {}

            runtime_args = {
                'git-password': 'unit_test_password'
            }

            with self.assertRaisesRegex(
                AssertionError,
                r"Either username or password is not set. Neither or both must be set."):
                self.run_step_test_with_result_validation(temp_dir, 'deploy', config, expected_step_results, runtime_args)

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_image_url_missing(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            with self.assertRaisesRegex(
                AssertionError,
                r'Can not determine container image repository uri.'
            ):
                self.run_step_test_with_result_validation(temp_dir, 'deploy', config, expected_step_results, runtime_args, environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_runtime_image_url_and_version(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password',
                'container-image-uri': image_url,
                'container-image-version': image_tag
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            self.run_step_test_with_result_validation(
                temp_dir,
                'deploy',
                config,
                expected_step_results,
                runtime_args,
                environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('shutil.copyfile', create=True)
    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_copyfile_error(self, argocd_mock, git_mock, shutil_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            shutil_mock.side_effect = OSError

            with self.assertRaises(RuntimeError):
                self.run_step_test_with_result_validation(
                    temp_dir=temp_dir,
                    step_name='deploy',
                    config=config,
                    expected_step_results=expected_step_results,
                    runtime_args=runtime_args,
                    environment=environment_name)

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_app_missing_no_sync(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'
        argocd_helm_chart_path = './'
        kube_api_uri = 'https://kubernetes.default.svc'
        deployment_namespace = 'dev'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            argocd_mock.app.get.side_effect = sh.ErrorReturnCode_1('argocd', b'stdout', b'stderror')

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='deploy',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args,
                environment=environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            argocd_mock.app.get.assert_called_once_with(
               organization_name + '-' + application_name + '-' + service_name + '-testbranch-' + environment_name,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
            argocd_mock.app.create.assert_called_once_with(
                organization_name + '-' + application_name + '-' + service_name + '-testbranch-' + environment_name,
                '--repo=' + helm_config_repo,
                '--revision=testbranch',
                '--path=' + argocd_helm_chart_path,
                '--dest-server=' + kube_api_uri,
                '--dest-namespace=' + organization_name + '-' + application_name + '-' + service_name + '-testbranch-' + environment_name,
                '--sync-policy=none',
                '--values=values-{env}.yaml'.format(env=environment_name),
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.clone.assert_called_once()

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_git_checkout_error(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'
        argocd_helm_chart_path = './'
        kube_api_uri = 'https://kubernetes.default.svc'
        deployment_namespace = 'dev'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : kube_app_domain,
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy' :{
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}',
                            'config-repo-git-tag':  f'{git_tag}.HASH'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect

            git_mock.checkout.side_effect = [sh.ErrorReturnCode('git', b'stdout', b'stderror'), None]

            self.run_step_test_with_result_validation(
                temp_dir,
                'deploy',
                config,
                expected_step_results,
                runtime_args,
                environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.clone.assert_called_once()


    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_url_no_tag(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'latest'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                    container-image-version: {image_tag}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url,
                        'container-image-version' : image_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            print("EXPECTED RESULTS\n" + str(expected_step_results))

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password',
                'git-url': 'http://git.repo.com/repo.git'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            self.run_step_test_with_result_validation(
                temp_dir,
                'deploy',
                config,
                expected_step_results,
                runtime_args,
                environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.clone.assert_called_once()

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_commit_error(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'

                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            git_mock.commit.side_effect = sh.ErrorReturnCode('git', b'stdout', b'stderror')

            with self.assertRaises(RuntimeError):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'deploy',
                    config,
                    expected_step_results,
                    runtime_args,
                    environment_name)

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_push_no_git_password(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'env-name' : environment_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': ''
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            with self.assertRaisesRegex(
                ValueError,
                'Both username and password must have non-empty value in the runtime step configuration'):
                self.run_step_test_with_result_validation(temp_dir, 'deploy', config, expected_step_results, runtime_args)

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_push_no_git_creds(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            with self.assertRaisesRegex(
                    ValueError,
                    'For a http:// git url, you need to also provide username/password pair'):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'deploy',
                    config,
                    expected_step_results,
                    runtime_args,
                    environment_name)

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_push_no_git_creds_https(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'https://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            with self.assertRaisesRegex(
                    ValueError,
                    'For a https:// git url, you need to also provide username/password pair'):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'deploy',
                    config,
                    expected_step_results,
                    runtime_args,
                    environment_name)


    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_sync_missing(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'
        argocd_sync_timeout_seconds = '60'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect

            self.run_step_test_with_result_validation(
                temp_dir,
                'deploy',
                config,
                expected_step_results,
                runtime_args,
                environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.clone.assert_called_once()

            argocd_mock.app.sync.assert_called_once_with(
                '--timeout',
                argocd_sync_timeout_seconds,
                organization_name + '-' + application_name + '-' + service_name + '-testbranch-' + environment_name,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_push_http(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'
        argocd_sync_timeout_seconds = '60'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            self.run_step_test_with_result_validation(
                temp_dir,
                'deploy',
                config,
                expected_step_results,
                runtime_args,
                environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.clone.assert_called_once()
            git_mock.checkout.assert_called_once()
            git_mock.push.bake.assert_called()

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_push_https(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'https://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            self.run_step_test_with_result_validation(
                temp_dir,
                'deploy',
                config,
                expected_step_results,
                runtime_args,
                environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.clone.assert_called_once()
            git_mock.checkout.assert_called_once()
            git_mock.push.bake.assert_called()

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_push_no_http(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'
        argocd_sync_timeout_seconds = '60'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            self.run_step_test_with_result_validation(
                temp_dir,
                'deploy',
                config,
                expected_step_results,
                runtime_args,
                environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.clone.assert_called_once()
            git_mock.checkout.assert_called_once()
            git_mock.push.assert_called()

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_push_error(self, argocd_mock, git_mock):

        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'git@gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {

            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            git_mock.push.side_effect = sh.ErrorReturnCode('git', b'stdout', b'stderror')

            with self.assertRaises(RuntimeError):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'deploy',
                    config,
                    expected_step_results,
                    runtime_args,
                    environment_name)

    @staticmethod
    def git_rev_parse_side_effect(*args, **kwargs):
        if (args[1] == '--abbrev-ref'):
            return 'testbranch'
        else:
            return 'HASH'

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_argo_create_cluster_norminal(self, argocd_mock, git_mock):
        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'https://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : 'apps.tssc.rht-set.com',
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path,
                            'kube-api-uri': "customcluster.ocp.com",
                            'kube-api-token': "token"
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            self.run_step_test_with_result_validation(
                temp_dir,
                'deploy',
                config,
                expected_step_results,
                runtime_args,
                environment_name)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

            git_mock.clone.assert_called_once()
            git_mock.checkout.assert_called_once()
            git_mock.push.bake.assert_called()

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_argo_create_cluster_add_failure(self, argocd_mock, git_mock):
        application_name = 'app-name'
        service_name = 'service-name'
        organization_name = 'org-name'
        environment_name = 'env-name'
        kube_app_domain = 'apps.tssc.rht-set.com'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'https://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    container-image-uri: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name,
                        'kube-app-domain' : kube_app_domain,
                        'git-email' : 'nappspo+tssc@redhat.com'
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'helm-config-repo' : helm_config_repo,
                            'argocd-sync-timeout-seconds' : '60',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path,
                            'kube-api-uri': "customcluster.ocp.com",
                            'kube-api-token': "token"
                        }
                    }
                }
            }

            repo_branch_name = 'testbranch'
            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'container-image-version' : image_tag
                    },
                    'push-container-image' : {
                        'container-image-uri' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'result': {
                            'success': True,
                            'message': 'deploy step completed - see report-artifacts',
                            'argocd-app-name' : f'{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}',
                            'config-repo-git-tag' :  f'{git_tag}.HASH',
                            'deploy-endpoint-url': f'http://{service_name}.{organization_name}-{application_name}-{service_name}-{repo_branch_name}-{environment_name}.{kube_app_domain}'
                        },
                        'report-artifacts': [
                        {
                            'name' : 'argocd-result-set',
                            'path': f'file://{temp_dir.path}/tssc-working/deploy/deploy_argocd_manifests.yml'
                        }
                        ]
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            git_mock.side_effect=self.git_rev_parse_side_effect
            argocd_mock.cluster.add.side_effect = sh.ErrorReturnCode('argocd', b'stdout', b'stderror')

            with self.assertRaises(RuntimeError):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'deploy',
                    config,
                    expected_step_results,
                    runtime_args,
                    environment_name)

    def __create_argocd_step_implementer(
        self,
        argocd_mock,
        git_mock,
        step_config={},
        environment=None
    ):
        config = Config({
            Config.TSSC_CONFIG_KEY: {
                'deploy': [
                    {
                        'implementer': 'ArgoCD',
                        'config': step_config
                    }
                ]

            }
        })

        step_config = config.get_step_config('deploy')
        sub_step_config = step_config.get_sub_step('ArgoCD')

        argocd_step = ArgoCD(
            results_dir_path="",
            results_file_name="",
            work_dir_path="",
            config=sub_step_config,
            environment=environment
        )

        return argocd_step

    def __run__get_app_name_test(
        self,
        argocd_mock,
        git_mock,
        git_branch,
        expected_result,
        step_config={},
        environment=None
    ):
        git_mock.side_effect = \
            TestStepImplementerDeployArgoCD.__create_git_rev_parse_side_effect(
                abbreviated_ref=git_branch
            )

        argocd_step = self.__create_argocd_step_implementer(
            argocd_mock=argocd_mock,
            git_mock=git_mock,
            step_config=step_config,
            environment=environment
        )

        self.assertEqual(
            expected_result,
            argocd_step._get_app_name()
        )

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test__get_app_name_less_then_63(self, argocd_mock, git_mock):
        self.__run__get_app_name_test(
            argocd_mock=argocd_mock,
            git_mock=git_mock,
            git_branch='repo_branch',
            expected_result='org_name-app_name-srv_name-repo_branch',
            step_config={
                'organization' : 'org_name',
                'application-name' : 'app_name',
                'service-name' : 'srv_name'
            }
        )

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test__get_app_name_greater_then_53(self, argocd_mock, git_mock):
        self.__run__get_app_name_test(
            argocd_mock=argocd_mock,
            git_mock=git_mock,
            git_branch='repository_branch_very_long',
            expected_result='cation_name-service_name-repository_branch_very_long',
            step_config={
                'organization' : 'organization_name',
                'application-name' : 'application_name',
                'service-name' : 'service_name'
            }
        )

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test__get_app_name_invalid_starting_char(self, argocd_mock, git_mock):
        self.__run__get_app_name_test(
            argocd_mock=argocd_mock,
            git_mock=git_mock,
            git_branch='repo_branch',
            expected_result='org_name-app_name-srv_name-repo_branch',
            step_config={
                'organization' : '--org_name',
                'application-name' : 'app_name',
                'service-name' : 'srv_name'
            }
        )

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test__get_app_name_invalid_end_char(self, argocd_mock, git_mock):
        self.__run__get_app_name_test(
            argocd_mock=argocd_mock,
            git_mock=git_mock,
            git_branch='repo_branch--',
            expected_result='org_name-app_name-srv_name-repo_branch',
            step_config={
                'organization' : 'org_name',
                'application-name' : 'app_name',
                'service-name' : 'srv_name'
            }
        )

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test__get_app_name_branch_name_with_slash(self, argocd_mock, git_mock):
        self.__run__get_app_name_test(
            argocd_mock=argocd_mock,
            git_mock=git_mock,
            git_branch='feature/foo42',
            expected_result='org_name-app_name-srv_name-feature-foo42',
            step_config={
                'organization' : 'org_name',
                'application-name' : 'app_name',
                'service-name' : 'srv_name'
            }
        )

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test__get_app_name_with_env_less_then_63(self, argocd_mock, git_mock):
        self.__run__get_app_name_test(
            argocd_mock=argocd_mock,
            git_mock=git_mock,
            git_branch='repo_branch',
            expected_result='org_name-app_name-srv_name-repo_branch-test',
            step_config={
                'organization' : 'org_name',
                'application-name' : 'app_name',
                'service-name' : 'srv_name'
            },
            environment='test'
        )

    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test__get_app_name_with_env_greater_then_53(self, argocd_mock, git_mock):
        self.__run__get_app_name_test(
            argocd_mock=argocd_mock,
            git_mock=git_mock,
            git_branch='repository_branch_very_long',
            expected_result='n_name-service_name-repository_branch_very_long-test',
            step_config={
                'organization' : 'organization_name',
                'application-name' : 'application_name',
                'service-name' : 'service_name'
            },
            environment='test'
        )
