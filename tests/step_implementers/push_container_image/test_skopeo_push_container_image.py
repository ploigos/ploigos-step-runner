import os
from io import IOBase
from unittest.mock import patch

import sh
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.push_container_image import Skopeo
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any


class BaseTestStepImplementerSkopeoSourceBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Skopeo,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

class TestStepImplementerSkopeoSourceBase_step_implementer_config_defaults(
    BaseTestStepImplementerSkopeoSourceBase
):
    def test_result(self):
        defaults = Skopeo.step_implementer_config_defaults()
        expected_defaults = {
            'src-tls-verify': True,
            'dest-tls-verify': True,
            'container-image-pull-repository-type': 'containers-storage:',
            'container-image-push-repository-type': 'docker://'
        }
        self.assertEqual(defaults, expected_defaults)

class TestStepImplementerSkopeoSourceBase___required_config_or_result_keys(
    BaseTestStepImplementerSkopeoSourceBase
):
    def test_result(self):
        required_keys = Skopeo._required_config_or_result_keys()
        expected_required_keys = [
            'destination-url',
            ['source-tls,verify', 'src-tls-verify'],
            'dest-tls-verify',
            'service-name',
            'application-name',
            'organization',
            ['container-image-pull-tag', 'container-image-tag'],
            ['container-image-pull-repository-type', 'container-image-repository-type'],
            ['container-image-push-repository-type', 'container-image-repository-type']
        ]
        self.assertEqual(required_keys, expected_required_keys)

class TestStepImplementerSkopeoSourceBase__run_step(
    BaseTestStepImplementerSkopeoSourceBase
):
    def __run_pass_test(
        self,
        step_config,
        image_version,
        image_pull_tag,
        image_push_tag,
        temp_dir,
        skopeo_mock,
        skopeo_mock_call_dest_tls_value='true',
        skopeo_mock_call_src_tls_value='true',
        expected_step_result_message=None,
        containers_config_auth_file=None
    ):
        parent_work_dir_path = os.path.join(temp_dir.path, 'working')

        # setup step
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='push-container-image',
            implementer='Skopeo',
            parent_work_dir_path=parent_work_dir_path,
        )

        # run step
        result = step_implementer._run_step()

        # verify
        expected_step_result = StepResult(
            step_name='push-container-image',
            sub_step_name='Skopeo',
            sub_step_implementer_name='Skopeo'
        )
        if expected_step_result_message:
            expected_step_result.message = expected_step_result_message
        expected_step_result.add_artifact(
            name='container-image-registry-uri',
            value='fake-registry.xyz',
            description='Registry URI poriton of the container image tag' \
                ' of the pushed container image.'
        )
        expected_step_result.add_artifact(
            name='container-image-registry-organization',
            value='fake-org',
            description='Organization portion of the container image tag' \
                ' of the pushed container image.'
        )
        expected_step_result.add_artifact(
            name='container-image-repository',
            value='fake-app-fake-service',
            description='Repository portion of the container image tag' \
                ' of the pushed container image.'
        )
        expected_step_result.add_artifact(
            name='container-image-name',
            value='fake-app-fake-service',
            description='Another way to reference the' \
                ' repository portion of the container image tag of the pushed container image.'
        )
        expected_step_result.add_artifact(
            name='container-image-version',
            value=image_version,
            description='Version portion of the container image tag of the pushed container image.'
        )
        expected_step_result.add_artifact(
            name='container-image-tag',
            value=f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}',
            description='Full container image tag of the pushed container,' \
                ' including the registry URI.'
        )
        expected_step_result.add_artifact(
            name='container-image-short-tag',
            value=f'fake-org/fake-app-fake-service:{image_version}',
            description='Short container image tag of the pushed container image,' \
                ' excluding the registry URI.'
        )
        self.assertEqual(result, expected_step_result)

        if not containers_config_auth_file:
            containers_config_auth_file = os.path.join(
                step_implementer.work_dir_path,
                'container-auth.json'
            )

        skopeo_mock.copy.assert_called_once_with(
            f"--src-tls-verify={skopeo_mock_call_src_tls_value}",
            f"--dest-tls-verify={skopeo_mock_call_dest_tls_value}",
            f"--authfile={containers_config_auth_file}",
            f'containers-storage:{image_pull_tag}',
            f'docker://{image_push_tag}',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch.object(sh, 'skopeo', create=True)
    def test_pass(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            image_version = '1.0-69442c8'
            image_pull_tag = f'localhost/fake-org/fake-app-fake-service:{image_version}'
            image_push_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-version': image_version,
                'container-image-pull-tag': image_pull_tag
            }
            self.__run_pass_test(
                temp_dir=temp_dir,
                image_version=image_version,
                image_pull_tag=image_pull_tag,
                image_push_tag=image_push_tag,
                step_config=step_config,
                skopeo_mock=skopeo_mock
            )

    @patch.object(sh, 'skopeo', create=True)
    def test_pass_default_version(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            image_version = 'latest'
            image_pull_tag = f'localhost/fake-org/fake-app-fake-service:{image_version}'
            image_push_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-pull-tag': image_pull_tag
            }
            self.__run_pass_test(
                temp_dir=temp_dir,
                image_version=image_version,
                image_pull_tag=image_pull_tag,
                image_push_tag=image_push_tag,
                step_config=step_config,
                skopeo_mock=skopeo_mock
            )


    @patch.object(sh, 'skopeo', create=True)
    def test_pass_string_destination_tls_truethy(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            image_version = '1.0-69442c8'
            image_pull_tag = f'localhost/fake-org/fake-app-fake-service:{image_version}'
            image_push_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-version': image_version,
                'container-image-pull-tag': image_pull_tag,
                'dest-tls-verify': 'true'
            }
            self.__run_pass_test(
                temp_dir=temp_dir,
                image_version=image_version,
                image_pull_tag=image_pull_tag,
                image_push_tag=image_push_tag,
                step_config=step_config,
                skopeo_mock=skopeo_mock
            )

    @patch.object(sh, 'skopeo', create=True)
    def test_pass_string_destination_tls_falsy(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            image_version = '1.0-69442c8'
            image_pull_tag = f'localhost/fake-org/fake-app-fake-service:{image_version}'
            image_push_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-version': image_version,
                'container-image-pull-tag': image_pull_tag,
                'dest-tls-verify': 'false'
            }
            self.__run_pass_test(
                temp_dir=temp_dir,
                image_version=image_version,
                image_pull_tag=image_pull_tag,
                image_push_tag=image_push_tag,
                step_config=step_config,
                skopeo_mock=skopeo_mock,
                skopeo_mock_call_dest_tls_value='false'
            )

    @patch.object(sh, 'skopeo', create=True)
    def test_pass_string_source_tls_truthy(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            image_version = '1.0-69442c8'
            image_pull_tag = f'localhost/fake-org/fake-app-fake-service:{image_version}'
            image_push_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-version': image_version,
                'container-image-pull-tag': image_pull_tag,
                'src-tls-verify': 'true'
            }
            self.__run_pass_test(
                temp_dir=temp_dir,
                image_version=image_version,
                image_pull_tag=image_pull_tag,
                image_push_tag=image_push_tag,
                step_config=step_config,
                skopeo_mock=skopeo_mock
            )

    @patch.object(sh, 'skopeo', create=True)
    def test_pass_string_source_tls_falsy(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            image_version = '1.0-69442c8'
            image_pull_tag = f'localhost/fake-org/fake-app-fake-service:{image_version}'
            image_push_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-version': image_version,
                'container-image-pull-tag': image_pull_tag,
                'src-tls-verify': 'false'
            }
            self.__run_pass_test(
                temp_dir=temp_dir,
                image_version=image_version,
                image_pull_tag=image_pull_tag,
                image_push_tag=image_push_tag,
                step_config=step_config,
                skopeo_mock=skopeo_mock,
                skopeo_mock_call_src_tls_value='false'
            )

    @patch.object(sh, 'skopeo', create=True)
    def test_pass_custom_auth_file(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            image_version = '1.0-69442c8'
            image_pull_tag = f'localhost/fake-org/fake-app-fake-service:{image_version}'
            image_push_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-version': image_version,
                'container-image-pull-tag': image_pull_tag,
                'containers-config-auth-file': 'mock-auth.json'
            }
            self.__run_pass_test(
                temp_dir=temp_dir,
                image_version=image_version,
                image_pull_tag=image_pull_tag,
                image_push_tag=image_push_tag,
                step_config=step_config,
                skopeo_mock=skopeo_mock,
                containers_config_auth_file='mock-auth.json'
            )

    @patch.object(sh, 'skopeo', create=True)
    def test_fail_run_skopeo(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            # setup step
            image_version = '1.0-69442c8'
            image_pull_tag = f'localhost/fake-org/fake-app-fake-service:{image_version}'
            image_push_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-version': image_version,
                'container-image-version': image_version,
                'container-image-pull-tag': image_pull_tag
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='push-container-image',
                implementer='Skopeo',
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step (mock fail)
            skopeo_mock.copy.side_effect = sh.ErrorReturnCode('skopeo', b'mock stdout', b'mock error')
            result = step_implementer._run_step()

            # verify
            expected_step_result = StepResult(
                step_name='push-container-image',
                sub_step_name='Skopeo',
                sub_step_implementer_name='Skopeo'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='fake-registry.xyz',
                description='Registry URI poriton of the container image tag' \
                    ' of the pushed container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='fake-org',
                description='Organization portion of the container image tag' \
                    ' of the pushed container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='fake-app-fake-service',
                description='Repository portion of the container image tag' \
                    ' of the pushed container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='fake-app-fake-service',
                description='Another way to reference the' \
                    ' repository portion of the container image tag of the pushed container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value=image_version,
                description='Version portion of the container image tag of the pushed container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='fake-registry.xyz/fake-org/fake-app-fake-service:1.0-69442c8',
                description='Full container image tag of the pushed container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='fake-org/fake-app-fake-service:1.0-69442c8',
                description='Short container image tag of the pushed container image,' \
                    ' excluding the registry URI.'
            )
            expected_step_result.success = False
            expected_step_result.message = f"Error pushing container image ({image_pull_tag}) " +\
                f" to tag ({image_push_tag}) using skopeo: \n" +\
                f"\n" +\
                f"  RAN: skopeo\n" +\
                f"\n" +\
                f"  STDOUT:\n" +\
                f"mock stdout\n" +\
                f"\n" +\
                f"  STDERR:\n" +\
                f"mock error"
            self.assertEqual(result, expected_step_result)

            containers_config_auth_file = os.path.join(
                step_implementer.work_dir_path,
                'container-auth.json'
            )
            skopeo_mock.copy.assert_called_once_with(
                "--src-tls-verify=true",
                "--dest-tls-verify=true",
                f"--authfile={containers_config_auth_file}",
                f'containers-storage:{image_pull_tag}',
                f'docker://{image_push_tag}',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
