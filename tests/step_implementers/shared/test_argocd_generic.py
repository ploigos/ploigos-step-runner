import os
import re
from unittest.mock import ANY, call, patch

import sh

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared.argocd_generic import \
    ArgoCDGeneric
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import (create_sh_side_effect,
                                      create_sh_side_effects)


class MockArgoCDGenericImpl(ArgoCDGeneric):
    @staticmethod
    def step_implementer_config_defaults():
        return []

    @staticmethod
    def _required_config_or_result_keys():
        return []

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        pass

    def _run_step(self):
        pass


class TestStepImplementerSharedArgoCDBase(BaseStepImplementerTestCase):
    def create_step_implementer(
        self,
        step_config={},
        parent_work_dir_path='',
        environment=None
    ):
        return self.create_given_step_implementer(
            step_implementer=MockArgoCDGenericImpl,
            step_config=step_config,
            step_name='deploy',
            implementer='MockArgoCDGenericImpl',
            parent_work_dir_path=parent_work_dir_path,
            environment=environment
        )


class TestStepImplementerSharedArgoCDGenericget_deployment_config_helm_chart_environment_values_file(
    TestStepImplementerSharedArgoCDBase
):
    def test_get_deployment_config_helm_chart_environment_values_file_config_value(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'deployment-config-helm-chart-environment-values-file': 'values-AWESOME.yaml'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            deployment_config_helm_chart_env_value_file = \
                step_implementer._get_deployment_config_helm_chart_environment_values_file()
            self.assertEqual(
                deployment_config_helm_chart_env_value_file,
                'values-AWESOME.yaml'
            )

    def test_get_deployment_config_helm_chart_environment_values_file_no_config_value_no_env(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path
            )

            deployment_config_helm_chart_env_value_file = \
                step_implementer._get_deployment_config_helm_chart_environment_values_file()
            self.assertEqual(
                deployment_config_helm_chart_env_value_file,
                'values.yaml'
            )

    def test_get_deployment_config_helm_chart_environment_values_file_no_config_value_with_env(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )

            deployment_config_helm_chart_env_value_file = \
                step_implementer._get_deployment_config_helm_chart_environment_values_file()
            self.assertEqual(
                deployment_config_helm_chart_env_value_file,
                'values-PROD.yaml'
            )


class TestStepImplementerSharedArgoCDGenericupdate_yaml_file_value(TestStepImplementerSharedArgoCDBase):
    @patch('sh.yq', create=True)
    def test_update_yaml_file_value_success(self, yq_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            updated_file_path = step_implementer._update_yaml_file_value(
                file='/does/not/matter/chart/values-PROD.yaml',
                yq_path='image.tag',
                value='v0.42.0-abc123'
            )
            self.assertEqual(updated_file_path, '/does/not/matter/chart/values-PROD.yaml')
            yq_script_file_path = os.path.join(
                step_implementer.work_dir_path,
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
    def test_update_yaml_file_value_fail(self, yq_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
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
                step_implementer._update_yaml_file_value(
                    file=file,
                    yq_path=yq_path,
                    value=value
                )
                yq_script_file_path = os.path.join(
                    step_implementer.work_dir_path,
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


class TestStepImplementerSharedArgoCDGenericgit_tag_and_push_deployment_config_repo(TestStepImplementerSharedArgoCDBase):
    @patch('ploigos_step_runner.step_implementers.shared.argocd_generic.git_tag_and_push')
    def test_git_tag_and_push_deployment_config_repo_http(self, git_tag_and_push_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'git-username': 'test-username',
                'git-password': 'test-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._git_tag_and_push_deployment_config_repo(
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

    @patch('ploigos_step_runner.step_implementers.shared.argocd_generic.git_tag_and_push')
    def test_git_tag_and_push_deployment_config_repo_https(self, git_tag_and_push_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'git-username': 'test-username',
                'git-password': 'test-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._git_tag_and_push_deployment_config_repo(
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

    @patch('ploigos_step_runner.step_implementers.shared.argocd_generic.git_tag_and_push')
    def test_git_tag_and_push_deployment_config_repo_ssh(self, git_tag_and_push_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'git-username': 'test-username',
                'git-password': 'test-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._git_tag_and_push_deployment_config_repo(
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


class TestStepImplementerSharedArgoCDGenericget_app_name(TestStepImplementerSharedArgoCDBase):
    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/test')
    def test_get_app_name_no_env_less_then_max_length(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-org',
                'application-name': 'test-app',
                'service-name': 'test-service'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            app_name = step_implementer._get_app_name()
            self.assertEqual(app_name, 'test-org-test-app-test-service-feature-test')

    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/TEST')
    def test_get_app_name_no_env_less_then_max_length_caps(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            app_name = step_implementer._get_app_name()
            self.assertEqual(app_name, 'test-org-test-app-test-service-feature-test')

    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/test')
    def test_get_app_name_no_env_more_then_max_length(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-org',
                'application-name': 'test-app',
                'service-name': 'test-service-this-is-really-long-hello-world-foo'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            app_name = step_implementer._get_app_name()
            self.assertEqual(app_name, 'ice-this-is-really-long-hello-world-foo-feature-test')

    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/test')
    def test_get_app_name_with_env_less_then_max_length(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-org',
                'application-name': 'test-app',
                'service-name': 'test-service'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )

            app_name = step_implementer._get_app_name()
            self.assertEqual(app_name, 'test-org-test-app-test-service-feature-test-prod')

    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/v0.1.2')
    def test_get_app_name_branch_with_dots_chars(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-org',
                'application-name': 'test-app',
                'service-name': 'test-service'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            app_name = step_implementer._get_app_name()
            self.assertEqual(app_name, 'test-org-test-app-test-service-feature-v0-1-2')

    @patch.object(ArgoCDGeneric, '_get_repo_branch', return_value='feature/v0.1.2...')
    def test_get_app_name_branch_with_bad_chars_end(self, get_repo_branch_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-org',
                'application-name': 'test-app',
                'service-name': 'test-service'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            app_name = step_implementer._get_app_name()
            self.assertEqual(app_name, 'test-org-test-app-test-service-feature-v0-1-2')


class TestStepImplementerSharedArgoCDGenericget_deployment_config_repo_tag(TestStepImplementerSharedArgoCDBase):
    def test_get_deployment_config_repo_tag_use_tag(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'tag': 'v0.42.0-abc123',
                'version': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            deployment_config_repo_tag = step_implementer._get_deployment_config_repo_tag()
            self.assertEqual(deployment_config_repo_tag, 'v0.42.0-abc123')

    def test_get_deployment_config_repo_tag_use_version(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'version': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            deployment_config_repo_tag = step_implementer._get_deployment_config_repo_tag()
            self.assertEqual(deployment_config_repo_tag, 'v0.42.0')


    def test_get_deployment_config_repo_tag_use_latest(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            deployment_config_repo_tag = step_implementer._get_deployment_config_repo_tag()
            self.assertEqual(deployment_config_repo_tag, 'latest')

    def test_get_deployment_config_repo_tag_use_tag_with_env(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'tag': 'v0.42.0-main+abc123',
                'version': 'v0.42.0'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                environment='PROD'
            )

            deployment_config_repo_tag = step_implementer._get_deployment_config_repo_tag()
            self.assertEqual(deployment_config_repo_tag, 'v0.42.0-main+abc123.PROD')


class TestStepImplementerSharedArgoCDGenericget_deployed_host_urls(TestStepImplementerSharedArgoCDBase):
    def __run__get_deployed_host_urls_test(
        self,
        manifest_contents,
        expected_host_urls
    ):
        with TempDirectory() as temp_dir:
            temp_dir.write('manifest.yaml', bytes(manifest_contents, 'utf-8'))
            manifest_path = os.path.join(temp_dir.path, 'manifest.yaml')

            actual_host_urls = ArgoCDGeneric._get_deployed_host_urls(
                manifest_path=manifest_path
            )

            self.assertEqual(actual_host_urls, expected_host_urls)

    def test_get_deployed_host_urls_empty_file(self):
        self.__run__get_deployed_host_urls_test(
            manifest_contents="",
            expected_host_urls=[]
        )

    def test_get_deployed_host_urls_empty_yaml_doc(self):
        self.__run__get_deployed_host_urls_test(
            manifest_contents="---",
            expected_host_urls=[]
        )

    def test_get_deployed_host_urls_yaml_doc_no_kind(self):
        self.__run__get_deployed_host_urls_test(
            manifest_contents="""
---
foo: test"
""",
            expected_host_urls=[]
        )

    def test_get_deployed_host_urls_1_http_routes_no_ingress(self):
        self.__run__get_deployed_host_urls_test(
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

    def test_get_deployed_host_urls_1_https_routes_no_ingress(self):
        self.__run__get_deployed_host_urls_test(
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

    def test_get_deployed_host_urls_no_routes_1_http_ingress(self):
        self.__run__get_deployed_host_urls_test(
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

    def test_get_deployed_host_urls_no_routes_1_http_ingress_with_tls_list(self):
        self.__run__get_deployed_host_urls_test(
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

    def test_get_deployed_host_urls_no_routes_1_https_ingress(self):
        self.__run__get_deployed_host_urls_test(
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

    def test_get_deployed_host_urls_1_http_route_1_https_route_1_http_ingress_1_https_ingress(self):
        self.__run__get_deployed_host_urls_test(
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


class TestStepImplementerSharedArgoCDGenericget_repo_branch(TestStepImplementerSharedArgoCDBase):
    def test_get_repo_branch_success(self):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-org',
                'application-name': 'test-app',
                'service-name': 'test-service',
                'branch': 'feature/test'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            repo_branch = step_implementer._get_repo_branch()

            # validate
            self.assertEqual(repo_branch, 'feature/test')


class TestStepImplementerSharedArgoCDGenericArgoCD_sign_in(TestStepImplementerSharedArgoCDBase):
    @patch('sh.argocd', create=True)
    def test_argocd_sign_in_success_not_insecure(self, mock_argocd):
        argocd_api='argo.dev.ploigos.xyz'
        username='test'
        password='secrettest'
        ArgoCDGeneric._argocd_sign_in(
            argocd_api=argocd_api,
            username=username,
            password=password,
            insecure=False
        )

        mock_argocd.login.assert_called_once_with(
            argocd_api,
            f'--username={username}',
            f'--password={password}',
            None,
            _out=ANY,
            _err=ANY
        )

    @patch('sh.argocd', create=True)
    def test_argocd_sign_in_success_insecure(self, mock_argocd):
        argocd_api='argo.dev.ploigos.xyz'
        username='test'
        password='secrettest'
        ArgoCDGeneric._argocd_sign_in(
            argocd_api=argocd_api,
            username=username,
            password=password,
            insecure=True
        )

        mock_argocd.login.assert_called_once_with(
            argocd_api,
            f'--username={username}',
            f'--password={password}',
            '--insecure',
            _out=ANY,
            _err=ANY
        )

    @patch('sh.argocd', create=True)
    def test_argocd_sign_in_fail_not_insecure(self, mock_argocd):
        argocd_api='argo.dev.ploigos.xyz'
        username='test'
        password='secrettest'

        mock_argocd.login.side_effect = create_sh_side_effect(
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
            ArgoCDGeneric._argocd_sign_in(
                argocd_api=argocd_api,
                username=username,
                password=password,
                insecure=False
            )

            mock_argocd.login.assert_called_once_with(
                argocd_api,
                f'--username={username}',
                f'--password={password}',
                None,
                _out=ANY,
                _err=ANY
            )


class TestStepImplementerSharedArgoCDGenericArgoCD_add_target_cluster(TestStepImplementerSharedArgoCDBase):
    @patch('sh.argocd', create=True)
    def test_argocd_add_target_cluster_default_cluster(self, mock_argocd):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._argocd_add_target_cluster(
                kube_api='https://kubernetes.default.svc',
                kube_api_skip_tls=False
            )

            mock_argocd.cluster.add.assert_not_called()

    @patch('sh.argocd', create=True)
    def test_argocd_add_target_cluster_custom_cluster_kube_skip_tls_true(self, mock_argocd):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                parent_work_dir_path=parent_work_dir_path,
            )
            expected_config_argocd_cluster_context_file_contents = """---
apiVersion: v1
kind: Config
current-context: https://api.dev.ploigos.xyz-context
clusters:
- cluster:
    insecure-skip-tls-verify: true
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

            step_implementer._argocd_add_target_cluster(
                kube_api='https://api.dev.ploigos.xyz',
                kube_api_token='abc123',
                kube_api_skip_tls=True
            )

            config_argocd_cluster_context_file_path = os.path.join(
                step_implementer.work_dir_path,
                'config-argocd-cluster-context.yaml'
            )
            mock_argocd.cluster.add.assert_called_once_with(
                '--kubeconfig', config_argocd_cluster_context_file_path,
                'https://api.dev.ploigos.xyz-context',
                _out=ANY,
                _err=ANY
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
    def test_argocd_add_target_cluster_custom_cluster_kube_skip_tls_false(self, mock_argocd):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                parent_work_dir_path=parent_work_dir_path,
            )
            expected_config_argocd_cluster_context_file_contents = """---
apiVersion: v1
kind: Config
current-context: https://api.dev.ploigos.xyz-context
clusters:
- cluster:
    insecure-skip-tls-verify: false
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

            step_implementer._argocd_add_target_cluster(
                kube_api='https://api.dev.ploigos.xyz',
                kube_api_token='abc123',
                kube_api_skip_tls=False
            )

            config_argocd_cluster_context_file_path = os.path.join(
                step_implementer.work_dir_path,
                'config-argocd-cluster-context.yaml'
            )
            mock_argocd.cluster.add.assert_called_once_with(
                '--kubeconfig', config_argocd_cluster_context_file_path,
                'https://api.dev.ploigos.xyz-context',
                _out=ANY,
                _err=ANY
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
    def test_argocd_add_target_cluster_fail_custom_cluster_kube_skip_tls_true(self, mock_argocd):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                parent_work_dir_path=parent_work_dir_path,
            )
            expected_config_argocd_cluster_context_file_contents = """---
apiVersion: v1
kind: Config
current-context: https://api.dev.ploigos.xyz-context
clusters:
- cluster:
    insecure-skip-tls-verify: true
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

            mock_argocd.cluster.add.side_effect = create_sh_side_effect(
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
                step_implementer._argocd_add_target_cluster(
                    kube_api='https://api.dev.ploigos.xyz',
                    kube_api_token='abc123',
                    kube_api_skip_tls=True
                )

                config_argocd_cluster_context_file_path = os.path.join(
                    step_implementer.work_dir_path,
                    'config-argocd-cluster-context.yaml'
                )
                mock_argocd.cluster.add.assert_called_once_with(
                    '--kubeconfig', config_argocd_cluster_context_file_path,
                    'https://api.dev.ploigos.xyz-context',
                    _out=ANY,
                    _err=ANY
                )

                with open(config_argocd_cluster_context_file_path, 'r') as \
                        config_argocd_cluster_context_file:
                    config_argocd_cluster_context_file_contents = \
                        config_argocd_cluster_context_file.read()


                    self.assertEqual(
                        config_argocd_cluster_context_file_contents,
                        expected_config_argocd_cluster_context_file_contents
                    )


class TestStepImplementerSharedArgoCDGenericArgoCD_app_create_or_update(TestStepImplementerSharedArgoCDBase):
    @patch('sh.argocd', create=True)
    def testargocd_app_create_or_update_success_sync_auto_no_extra_values_files(self, mock_argocd):
        argocd_app_name = 'test'
        project = 'myproject'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        dest_namespace = 'my-namespace'
        auto_sync = True
        values_files = []
        ArgoCDGeneric._argocd_app_create_or_update(
            argocd_app_name=argocd_app_name,
            project=project,
            repo=repo,
            revision=revision,
            path=path,
            dest_server=dest_server,
            dest_namespace=dest_namespace,
            auto_sync=auto_sync,
            values_files=values_files
        )

        sync_policy = 'automated'
        values_params = None
        mock_argocd.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={dest_namespace}',
            f'--sync-policy={sync_policy}',
            f'--project={project}',
            values_params,
            '--upsert',
            _out=ANY,
            _err=ANY
        )

    @patch('sh.argocd', create=True)
    def testargocd_app_create_or_update_success_sync_none_no_extra_values_files(self, mock_argocd):
        argocd_app_name = 'test'
        project = 'myproject'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        dest_namespace = 'my-namespace'
        auto_sync = False
        values_files = []
        ArgoCDGeneric._argocd_app_create_or_update(
            argocd_app_name=argocd_app_name,
            project=project,
            repo=repo,
            revision=revision,
            path=path,
            dest_server=dest_server,
            dest_namespace=dest_namespace,
            auto_sync=auto_sync,
            values_files=values_files
        )

        sync_policy = 'none'
        values_params = None
        mock_argocd.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={dest_namespace}',
            f'--sync-policy={sync_policy}',
            f'--project={project}',
            values_params,
            '--upsert',
            _out=ANY,
            _err=ANY
        )

    @patch('sh.argocd', create=True)
    def testargocd_app_create_or_update_success_sync_auto_1_values_files(self, mock_argocd):
        argocd_app_name = 'test'
        project = 'myproject'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        dest_namespace = 'my-namespace'
        auto_sync = True
        values_files = ['values-foo.yaml']
        ArgoCDGeneric._argocd_app_create_or_update(
            argocd_app_name=argocd_app_name,
            project=project,
            repo=repo,
            revision=revision,
            path=path,
            dest_server=dest_server,
            dest_namespace=dest_namespace,
            auto_sync=auto_sync,
            values_files=values_files
        )

        sync_policy = 'automated'
        values_params = ['--values=values-foo.yaml']
        mock_argocd.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={dest_namespace}',
            f'--sync-policy={sync_policy}',
            f'--project={project}',
            values_params,
            '--upsert',
            _out=ANY,
            _err=ANY
        )

    @patch('sh.argocd', create=True)
    def testargocd_app_create_or_update_success_sync_auto_2_values_files(self, mock_argocd):
        argocd_app_name = 'test'
        project = 'myproject'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        dest_namespace = 'my-namespace'
        auto_sync = True
        values_files = ['values-foo.yaml', 'values-DEV.yaml']
        ArgoCDGeneric._argocd_app_create_or_update(
            argocd_app_name=argocd_app_name,
            project=project,
            repo=repo,
            revision=revision,
            path=path,
            dest_server=dest_server,
            dest_namespace=dest_namespace,
            auto_sync=auto_sync,
            values_files=values_files
        )

        sync_policy = 'automated'
        values_params = ['--values=values-foo.yaml', '--values=values-DEV.yaml']
        mock_argocd.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={dest_namespace}',
            f'--sync-policy={sync_policy}',
            f'--project={project}',
            values_params,
            '--upsert',
            _out=ANY,
            _err=ANY
        )

    @patch('sh.argocd', create=True)
    def testargocd_app_create_or_update_fail_sync_auto_1_values_files(self, mock_argocd):
        mock_argocd.app.create.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('argocd', b'mock out', b'mock create error')
        )

        argocd_app_name = 'test'
        project = 'myproject'
        repo = 'https://git.test.xyz'
        revision = 'feature/test'
        path = 'charts/awesome'
        dest_server = 'https://kubernetes.default.svc'
        dest_namespace = 'my-namespace'
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
            ArgoCDGeneric._argocd_app_create_or_update(
                argocd_app_name=argocd_app_name,
                project=project,
                repo=repo,
                revision=revision,
                path=path,
                dest_server=dest_server,
                dest_namespace=dest_namespace,
                auto_sync=auto_sync,
                values_files=values_files
            )

        sync_policy = 'automated'
        values_params = ['--values=values-foo.yaml']
        mock_argocd.app.create.assert_called_once_with(
            argocd_app_name,
            f'--repo={repo}',
            f'--revision={revision}',
            f'--path={path}',
            f'--dest-server={dest_server}',
            f'--dest-namespace={dest_namespace}',
            f'--sync-policy={sync_policy}',
            f'--project={project}',
            values_params,
            '--upsert',
            _out=ANY,
            _err=ANY
        )


@patch.object(ArgoCDGeneric, '_argocd_app_wait_for_health')
@patch.object(ArgoCDGeneric, '_argocd_app_wait_for_operation')
@patch('sh.argocd', create=True)
class TestStepImplementerSharedArgoCDGenericArgoCD_app_sync(TestStepImplementerSharedArgoCDBase):
    def test_success(
        self,
        mock_argocd,
        mock_argocd_app_wait_for_operation,
        mock_argocd_app_wait_for_health
    ):
        # run test
        ArgoCDGeneric._argocd_app_sync(
            argocd_app_name='test',
            argocd_sync_timeout_seconds=120,
            argocd_sync_retry_limit=3
        )

        # validate
        mock_argocd_app_wait_for_operation.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )
        mock_argocd.app.sync.assert_called_once_with(
            '--prune',
            '--timeout', 120,
            '--retry-limit', 3,
            'test',
            _out=ANY,
            _err=ANY
        )
        mock_argocd_app_wait_for_health.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )

    def test_success_retry(
        self,
        mock_argocd,
        mock_argocd_app_wait_for_operation,
        mock_argocd_app_wait_for_health
    ):
        # run test
        ArgoCDGeneric._argocd_app_sync(
            argocd_app_name='test',
            argocd_sync_timeout_seconds=120,
            argocd_sync_retry_limit=4
        )

        # validate
        mock_argocd_app_wait_for_operation.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )
        mock_argocd.app.sync.assert_called_once_with(
            '--prune',
            '--timeout', 120,
            '--retry-limit', 4,
            'test',
            _out=ANY,
            _err=ANY
        )
        mock_argocd_app_wait_for_health.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )

    def test_fail_sync(
        self,
        mock_argocd,
        mock_argocd_app_wait_for_operation,
        mock_argocd_app_wait_for_health
    ):
        # setup mocks
        mock_argocd.app.sync.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('argocd', b'mock out', b'mock sync error')
        )

        # run test
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
            ArgoCDGeneric._argocd_app_sync(
                argocd_app_name='test',
                argocd_sync_timeout_seconds=120,
                argocd_sync_retry_limit=3
            )

        # validate
        mock_argocd_app_wait_for_operation.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )
        mock_argocd.app.sync.assert_called_once_with(
            '--prune',
            '--timeout', 120,
            '--retry-limit', 3,
            'test',
            _out=ANY,
            _err=ANY
        )
        mock_argocd_app_wait_for_health.assert_not_called()

    def test_fail_sync_no_prune(
        self,
        mock_argocd,
        mock_argocd_app_wait_for_operation,
        mock_argocd_app_wait_for_health
    ):
        # setup mocks
        mock_argocd.app.sync.side_effect = create_sh_side_effect(
            exception=sh.ErrorReturnCode('argocd', b'mock out', b'mock sync error')
        )

        # run test
        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Error synchronization ArgoCD Application \(test\)."
                r" Sync 'prune' option is disabled."
                r" If sync error \(see logs\) was due to resource\(s\) that need to be pruned,"
                r" and the pruneable resources are intentionally there then see the ArgoCD"
                r" documentation for instructions for argo to ignore the resource\(s\)."
                " See: https://argoproj.github.io/argo-cd/user-guide/sync-options/#no-prune-resources"
                " and https://argoproj.github.io/argo-cd/user-guide/compare-options/#ignoring-resources-that-are-extraneous"
                r".*RAN: argocd"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock sync error",
                re.DOTALL
            )
        ):
            ArgoCDGeneric._argocd_app_sync(
                argocd_app_name='test',
                argocd_sync_timeout_seconds=120,
                argocd_sync_retry_limit=3,
                argocd_sync_prune=False
            )

        # validate
        mock_argocd_app_wait_for_operation.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )
        mock_argocd.app.sync.assert_called_once_with(
            '--timeout', 120,
            '--retry-limit', 3,
            'test',
            _out=ANY,
            _err=ANY
        )
        mock_argocd_app_wait_for_health.assert_not_called()

    def test_retry_sync_due_to_existing_operation(
        self,
        mock_argocd,
        mock_argocd_app_wait_for_operation,
        mock_argocd_app_wait_for_health
    ):
        # setup mocks
        mock_argocd.app.sync.side_effect = create_sh_side_effects([
            {
                'mock_stdout': 'time="2021-10-20T16:19:03Z" level=fatal msg="rpc error: code = FailedPrecondition desc = another operation is already in progress"',
                'mock_stderr': '',
                'exception': sh.ErrorReturnCode(
                    'argocd',
                    b'mock sync stdout',
                    b'mock sync error'
                )
            },
            {
                'mock_stdout': 'mock success',
                'mock_stderr': '',
                'exception': None
            }
        ])

        # run test
        ArgoCDGeneric._argocd_app_sync(
            argocd_app_name='test',
            argocd_sync_timeout_seconds=120,
            argocd_sync_retry_limit=3
        )

        # validate
        mock_argocd_app_wait_for_operation.assert_has_calls([
            call(
                argocd_app_name='test',
                argocd_timeout_seconds=120
            ),
            call(
                argocd_app_name='test',
                argocd_timeout_seconds=120
            )
        ])
        mock_argocd.app.sync.assert_has_calls([
            call(
                '--prune',
                '--timeout', 120,
                '--retry-limit', 3,
                'test',
                _out=ANY,
                _err=ANY
            ),
            call(
                '--prune',
                '--timeout', 120,
                '--retry-limit', 3,
                'test',
                _out=ANY,
                _err=ANY
            )
        ])
        mock_argocd_app_wait_for_health.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )

    def test_fail_wait_for_health_after_sync(
        self,
        mock_argocd,
        mock_argocd_app_wait_for_operation,
        mock_argocd_app_wait_for_health
    ):
        # setup mocks
        mock_argocd_app_wait_for_health.side_effect = StepRunnerException('mock error')

        # run test
        with self.assertRaisesRegex(StepRunnerException, 'mock error'):
            ArgoCDGeneric._argocd_app_sync(
                argocd_app_name='test',
                argocd_sync_timeout_seconds=120,
                argocd_sync_retry_limit=3
            )

        # verify
        mock_argocd_app_wait_for_operation.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )
        mock_argocd.app.sync.assert_called_once_with(
            '--prune',
            '--timeout', 120,
            '--retry-limit', 3,
            'test',
            _out=ANY,
            _err=ANY
        )
        mock_argocd_app_wait_for_health.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )

    def test_fail_wait_before_sync(
        self,
        mock_argocd,
        mock_argocd_app_wait_for_operation,
        mock_argocd_app_wait_for_health
    ):
        # setup mocks
        mock_argocd_app_wait_for_operation.side_effect = StepRunnerException('mock error')

        # run test
        with self.assertRaisesRegex(StepRunnerException, 'mock error'):
            ArgoCDGeneric._argocd_app_sync(
                argocd_app_name='test',
                argocd_sync_timeout_seconds=120,
                argocd_sync_retry_limit=3
            )

        # verify
        mock_argocd_app_wait_for_operation.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )
        mock_argocd.app.sync.assert_not_called()
        mock_argocd_app_wait_for_health.assert_not_called()

    def test_success_no_prune(
        self,
        mock_argocd,
        mock_argocd_app_wait_for_operation,
        mock_argocd_app_wait_for_health
    ):
        # run test
        ArgoCDGeneric._argocd_app_sync(
            argocd_app_name='test',
            argocd_sync_timeout_seconds=120,
            argocd_sync_retry_limit=3,
            argocd_sync_prune=False
        )

        # validate
        mock_argocd_app_wait_for_operation.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )
        mock_argocd.app.sync.assert_called_once_with(
            '--timeout', 120,
            '--retry-limit', 3,
            'test',
            _out=ANY,
            _err=ANY
        )
        mock_argocd_app_wait_for_health.assert_called_once_with(
            argocd_app_name='test',
            argocd_timeout_seconds=120
        )

@patch('sh.argocd', create=True)
class TestStepImplementerSharedArgoCDGenericArgoCD_argocd_app_wait_for_operation(
    TestStepImplementerSharedArgoCDBase
):
    def test_success(self, mock_argocd):
        # run test
        ArgoCDGeneric._argocd_app_wait_for_operation(
            argocd_app_name='mock-app',
            argocd_timeout_seconds=42
        )

        # validate
        mock_argocd.app.wait.assert_called_once_with(
            'mock-app',
            '--operation',
            '--timeout', 42,
            _out=ANY,
            _err=ANY
        )

    def test_failure(self, mock_argocd):
        # setup mocks
        mock_argocd.app.wait.side_effect = sh.ErrorReturnCode(
            'argocd',
            b'mock out',
            b'mock wait error'
        )

        # run test
        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Error waiting for existing ArgoCD operations on Application \(mock-app\):"
                r".*RAN: argocd"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock wait error",
                re.DOTALL
            )
        ):
            ArgoCDGeneric._argocd_app_wait_for_operation(
                argocd_app_name='mock-app',
                argocd_timeout_seconds=42
            )

        # validate
        mock_argocd.app.wait.assert_called_once_with(
            'mock-app',
            '--operation',
            '--timeout', 42,
            _out=ANY,
            _err=ANY
        )

@patch('sh.argocd', create=True)
class TestStepImplementerSharedArgoCDGenericArgoCD_argocd_app_wait_for_health(
    TestStepImplementerSharedArgoCDBase
):
    def test_success_on_first_wait(self, mock_argocd):
        # run test
        ArgoCDGeneric._argocd_app_wait_for_health(
            argocd_app_name='mock-app',
            argocd_timeout_seconds=42
        )

        # validate
        mock_argocd.app.wait.assert_called_once_with(
            'mock-app',
            '--health',
            '--timeout', 42,
            _out=ANY,
            _err=ANY
        )

    def test_success_on_second_wait_after_transitioning_from_healthy_to_degraded(self, mock_argocd):
        # setup mocks
        mock_argocd.app.wait.side_effect = create_sh_side_effects([
            {
                'mock_stdout': 'time="2021-11-04T22:57:38Z" level=fatal msg="application'
                    ' \'mock-app\' health state has transitioned from Healthy to Degraded"',
                'mock_stderr': '',
                'exception': sh.ErrorReturnCode(
                    'argocd',
                    b'mock wait stdout',
                    b'mock wait error'
                )
            },
            {
                'mock_stdout': 'mock success',
                'mock_stderr': '',
                'exception': None
            }
        ])

        # run test
        ArgoCDGeneric._argocd_app_wait_for_health(
            argocd_app_name='mock-app',
            argocd_timeout_seconds=42
        )

        # validate
        mock_argocd.app.wait.assert_has_calls([
            call(
                'mock-app',
                '--health',
                '--timeout', 42,
                _out=ANY,
                _err=ANY
            ),
            call(
                'mock-app',
                '--health',
                '--timeout', 42,
                _out=ANY,
                _err=ANY
            )
        ])

    def test_success_on_second_wait_after_transitioning_from_progressing_to_degraded(self, mock_argocd):
        # setup mocks
        mock_argocd.app.wait.side_effect = create_sh_side_effects([
            {
                'mock_stdout': 'time="2021-11-05T19:40:51Z" level=fatal msg="application'
                    ' \'mock-app\' health state has transitioned from Progressing to Degraded"',
                'mock_stderr': '',
                'exception': sh.ErrorReturnCode(
                    'argocd',
                    b'mock wait stdout',
                    b'mock wait error'
                )
            },
            {
                'mock_stdout': 'mock success',
                'mock_stderr': '',
                'exception': None
            }
        ])

        # run test
        ArgoCDGeneric._argocd_app_wait_for_health(
            argocd_app_name='mock-app',
            argocd_timeout_seconds=42
        )

        # validate
        mock_argocd.app.wait.assert_has_calls([
            call(
                'mock-app',
                '--health',
                '--timeout', 42,
                _out=ANY,
                _err=ANY
            ),
            call(
                'mock-app',
                '--health',
                '--timeout', 42,
                _out=ANY,
                _err=ANY
            )
        ])

    def test_failure_on_first_try(self, mock_argocd):
        # setup mocks
        mock_argocd.app.wait.side_effect = create_sh_side_effects([
            {
                'mock_stdout': '',
                'mock_stderr': 'unknown crazy scary mock error',
                'exception': sh.ErrorReturnCode(
                    'argocd',
                    b'mock wait out',
                    b'mock wait error'
                )
            }
        ])

        # run test
        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Error waiting for Healthy ArgoCD Application \(mock-app\):"
                r".*RAN: argocd"
                r".*STDOUT:"
                r".*mock wait out"
                r".*STDERR:"
                r".*mock wait error",
                re.DOTALL
            )
        ):
            ArgoCDGeneric._argocd_app_wait_for_health(
                argocd_app_name='mock-app',
                argocd_timeout_seconds=42
            )

        # validate
        mock_argocd.app.wait.assert_called_once_with(
            'mock-app',
            '--health',
            '--timeout', 42,
            _out=ANY,
            _err=ANY
        )

class TestStepImplementerSharedArgoCDGenericArgoCD_get_app_manifest(TestStepImplementerSharedArgoCDBase):
    @patch('sh.argocd', create=True)
    def test_argocd_get_app_manifest_success_live(self, mock_argocd):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                parent_work_dir_path=parent_work_dir_path,
            )

            argocd_app_manifest_file = step_implementer._argocd_get_app_manifest(
                argocd_app_name='test',
                source='live'
            )

            self.assertIsNotNone(argocd_app_manifest_file)
            mock_argocd.app.manifests.assert_called_once_with(
                '--source=live',
                'test',
                _out=ANY,
                _err=ANY
            )

    @patch('sh.argocd', create=True)
    def test_argocd_get_app_manifest_success_git(self, mock_argocd):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_implementer = self.create_step_implementer(
                step_config={},
                parent_work_dir_path=parent_work_dir_path,
            )

            argocd_app_manifest_file = step_implementer._argocd_get_app_manifest(
                argocd_app_name='test',
                source='git'
            )

            self.assertIsNotNone(argocd_app_manifest_file)
            mock_argocd.app.manifests.assert_called_once_with(
                '--source=git',
                'test',
                _out=ANY,
                _err=ANY
            )

    @patch('sh.argocd', create=True)
    def test_argocd_get_app_manifest_fail(self, mock_argocd):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config={},
                parent_work_dir_path=parent_work_dir_path,
            )

            mock_argocd.app.manifests.side_effect = create_sh_side_effect(
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
                argocd_app_manifest_file = step_implementer._argocd_get_app_manifest(
                    argocd_app_name='invalid',
                    source='live'
                )

                self.assertIsNotNone(argocd_app_manifest_file)
                mock_argocd.app.manifests.assert_called_once_with(
                    '--source=live',
                    'invalid',
                    _out=ANY,
                    _err=ANY
                )
