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
            'container-image-pull-registry-type': 'containers-storage:',
            'container-image-push-registry-type': 'docker://',
            'container-image-push-tag': 'latest'
        }
        self.assertEqual(defaults, expected_defaults)

class TestStepImplementerSkopeoSourceBase___required_config_or_result_keys(
    BaseTestStepImplementerSkopeoSourceBase
):
    def test_result(self):
        required_keys = Skopeo._required_config_or_result_keys()
        expected_required_keys = [
            ['container-image-pull-registry-type', 'container-image-registry-type'],
            ['container-image-pull-address', 'container-image-build-address'],
            ['source-tls,verify', 'src-tls-verify'],

            ['container-image-push-registry-type', 'container-image-registry-type'],
            ['container-image-push-registry', 'destination-url'],
            ['container-image-push-repository', 'container-image-repository'],
            ['container-image-push-tag', 'container-image-tag', 'container-image-version'],
            'dest-tls-verify'
        ]
        self.assertEqual(required_keys, expected_required_keys)

@patch('ploigos_step_runner.step_implementers.push_container_image.skopeo.get_container_image_digest')
@patch.object(sh, 'skopeo', create=True)
class TestStepImplementerSkopeoSourceBase__run_step(
    BaseTestStepImplementerSkopeoSourceBase
):
    def __run_test(
        self,
        step_config,
        image_tag,
        image_pull_address,
        image_push_address,
        temp_dir,
        mock_skopeo,
        mock_get_container_image_digest,
        mock_skopeo_call_dest_tls_value='true',
        mock_skopeo_call_src_tls_value='true',
        expected_step_result_success=True,
        expected_step_result_message=None,
        containers_config_auth_file=None,
        include_digest_results=True
    ):
        parent_work_dir_path = os.path.join(temp_dir.path, 'working')

        # setup mocks
        mock_get_container_image_digest.return_value = 'sha256:mockabc123'

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
        expected_step_result.success = expected_step_result_success
        if expected_step_result_message:
            expected_step_result.message = expected_step_result_message
        expected_step_result.add_artifact(
            name='container-image-push-registry',
            value='mock-reg.xyz',
            description='Container image registry container image was pushed to.'
        )
        expected_step_result.add_artifact(
            name='container-image-push-repository',
            value='fake-org/fake-app/fake-service',
            description='Container image repository container image was pushed to.'
        )
        expected_step_result.add_artifact(
            name='container-image-push-tag',
            value=image_tag,
            description='Container image tag container image was pushed to.'
        )
        expected_step_result.add_artifact(
            name='container-image-address-by-tag',
            value=f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}',
            description='Pushed container image address by tag.'
        )
        expected_step_result.add_artifact(
            name='container-image-short-address-by-tag',
            value=f'fake-org/fake-app/fake-service:{image_tag}',
            description='Pushed container image short address (no registry) by tag.'
        )

        if include_digest_results:
            expected_step_result.add_artifact(
                name='container-image-push-digest',
                value='sha256:mockabc123',
                description='Container image digest container image was pushed to.'
            )
            expected_step_result.add_artifact(
                name='container-image-address-by-digest',
                value='mock-reg.xyz/fake-org/fake-app/fake-service@sha256:mockabc123',
                description='Pushed container image address by digest.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-address-by-digest',
                value='fake-org/fake-app/fake-service@sha256:mockabc123',
                description='Pushed container image short address (no registry) by digest.'
            )

        self.assertEqual(result, expected_step_result)

        if not containers_config_auth_file:
            containers_config_auth_file = os.path.join(
                step_implementer.work_dir_path,
                'container-auth.json'
            )

        mock_skopeo.copy.assert_called_once_with(
            f"--src-tls-verify={mock_skopeo_call_src_tls_value}",
            f"--dest-tls-verify={mock_skopeo_call_dest_tls_value}",
            f"--authfile={containers_config_auth_file}",
            f'containers-storage:{image_pull_address}',
            f'docker://{image_push_address}',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    def test_pass(self, mock_skopeo, mock_get_container_image_digest):
        with TempDirectory() as temp_dir:
            image_tag = '1.0-69442c8'
            image_pull_address = f'localhost/fake-org/fake-app/fake-service:{image_tag}'
            image_push_address = f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}'
            step_config = {
                'container-image-pull-address': image_pull_address,
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-push-repository': 'fake-org/fake-app/fake-service',
                'container-image-push-tag': image_tag
            }
            self.__run_test(
                temp_dir=temp_dir,
                image_tag=image_tag,
                image_pull_address=image_pull_address,
                image_push_address=image_push_address,
                step_config=step_config,
                mock_skopeo=mock_skopeo,
                mock_get_container_image_digest=mock_get_container_image_digest
            )

    def test_pass_default_version(self, mock_skopeo, mock_get_container_image_digest):
        with TempDirectory() as temp_dir:
            image_tag = 'latest'
            image_pull_address = f'localhost/fake-org/fake-app/fake-service:{image_tag}'
            image_push_address = f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}'
            step_config = {
                'container-image-pull-address': image_pull_address,
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-push-repository': 'fake-org/fake-app/fake-service'
            }
            self.__run_test(
                temp_dir=temp_dir,
                image_tag=image_tag,
                image_pull_address=image_pull_address,
                image_push_address=image_push_address,
                step_config=step_config,
                mock_skopeo=mock_skopeo,
                mock_get_container_image_digest=mock_get_container_image_digest
            )

    def test_pass_string_destination_tls_truethy(self, mock_skopeo, mock_get_container_image_digest):
        with TempDirectory() as temp_dir:
            image_tag = '1.0-69442c8'
            image_pull_address = f'localhost/fake-org/fake-app/fake-service:{image_tag}'
            image_push_address = f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}'
            step_config = {
                'container-image-pull-address': image_pull_address,
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-push-repository': 'fake-org/fake-app/fake-service',
                'container-image-push-tag': image_tag,
                'dest-tls-verify': 'true'
            }
            self.__run_test(
                temp_dir=temp_dir,
                image_tag=image_tag,
                image_pull_address=image_pull_address,
                image_push_address=image_push_address,
                step_config=step_config,
                mock_skopeo=mock_skopeo,
                mock_get_container_image_digest=mock_get_container_image_digest
            )

    def test_pass_string_destination_tls_falsy(self, mock_skopeo, mock_get_container_image_digest):
        with TempDirectory() as temp_dir:
            image_tag = '1.0-69442c8'
            image_pull_address = f'localhost/fake-org/fake-app/fake-service:{image_tag}'
            image_push_address = f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}'
            step_config = {
                'container-image-pull-address': image_pull_address,
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-push-repository': 'fake-org/fake-app/fake-service',
                'container-image-push-tag': image_tag,
                'dest-tls-verify': 'false'
            }
            self.__run_test(
                temp_dir=temp_dir,
                image_tag=image_tag,
                image_pull_address=image_pull_address,
                image_push_address=image_push_address,
                step_config=step_config,
                mock_skopeo=mock_skopeo,
                mock_get_container_image_digest=mock_get_container_image_digest,
                mock_skopeo_call_dest_tls_value='false'
            )

    def test_pass_string_source_tls_truthy(self, mock_skopeo, mock_get_container_image_digest):
        with TempDirectory() as temp_dir:
            image_tag = '1.0-69442c8'
            image_pull_address = f'localhost/fake-org/fake-app/fake-service:{image_tag}'
            image_push_address = f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}'
            step_config = {
                'container-image-pull-address': image_pull_address,
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-push-repository': 'fake-org/fake-app/fake-service',
                'container-image-push-tag': image_tag,
                'src-tls-verify': 'true'
            }
            self.__run_test(
                temp_dir=temp_dir,
                image_tag=image_tag,
                image_pull_address=image_pull_address,
                image_push_address=image_push_address,
                step_config=step_config,
                mock_skopeo=mock_skopeo,
                mock_get_container_image_digest=mock_get_container_image_digest
            )

    def test_pass_string_source_tls_falsy(self, mock_skopeo, mock_get_container_image_digest):
        with TempDirectory() as temp_dir:
            image_tag = '1.0-69442c8'
            image_pull_address = f'localhost/fake-org/fake-app/fake-service:{image_tag}'
            image_push_address = f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}'
            step_config = {
                'container-image-pull-address': image_pull_address,
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-push-repository': 'fake-org/fake-app/fake-service',
                'container-image-push-tag': image_tag,
                'src-tls-verify': 'false'
            }
            self.__run_test(
                temp_dir=temp_dir,
                image_tag=image_tag,
                image_pull_address=image_pull_address,
                image_push_address=image_push_address,
                step_config=step_config,
                mock_skopeo=mock_skopeo,
                mock_get_container_image_digest=mock_get_container_image_digest,
                mock_skopeo_call_src_tls_value='false'
            )

    def test_pass_custom_auth_file(self, mock_skopeo, mock_get_container_image_digest):
        with TempDirectory() as temp_dir:
            image_tag = '1.0-69442c8'
            image_pull_address = f'localhost/fake-org/fake-app/fake-service:{image_tag}'
            image_push_address = f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}'
            step_config = {
                'container-image-pull-address': image_pull_address,
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-push-repository': 'fake-org/fake-app/fake-service',
                'container-image-push-tag': image_tag,
                'containers-config-auth-file': 'mock-auth.json'
            }
            self.__run_test(
                temp_dir=temp_dir,
                image_tag=image_tag,
                image_pull_address=image_pull_address,
                image_push_address=image_push_address,
                step_config=step_config,
                mock_skopeo=mock_skopeo,
                mock_get_container_image_digest=mock_get_container_image_digest,
                containers_config_auth_file='mock-auth.json'
            )

    def test_fail_run_skopeo(self, mock_skopeo, mock_get_container_image_digest):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            # setup step
            image_tag = '1.0-69442c8'
            image_pull_address = f'localhost/fake-org/fake-app/fake-service:{image_tag}'
            image_push_address = f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}'
            step_config = {
                'container-image-pull-address': image_pull_address,
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-push-repository': 'fake-org/fake-app/fake-service',
                'container-image-push-tag': image_tag,
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='push-container-image',
                implementer='Skopeo',
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step (mock fail)
            mock_skopeo.copy.side_effect = sh.ErrorReturnCode('skopeo', b'mock stdout', b'mock error')
            result = step_implementer._run_step()

            # verify
            expected_step_result = StepResult(
                step_name='push-container-image',
                sub_step_name='Skopeo',
                sub_step_implementer_name='Skopeo'
            )
            expected_step_result.add_artifact(
                name='container-image-push-registry',
                value='mock-reg.xyz',
                description='Container image registry container image was pushed to.'
            )
            expected_step_result.add_artifact(
                name='container-image-push-repository',
                value='fake-org/fake-app/fake-service',
                description='Container image repository container image was pushed to.'
            )
            expected_step_result.add_artifact(
                name='container-image-push-tag',
                value=image_tag,
                description='Container image tag container image was pushed to.'
            )
            expected_step_result.add_artifact(
                name='container-image-address-by-tag',
                value=f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}',
                description='Pushed container image address by tag.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-address-by-tag',
                value=f'fake-org/fake-app/fake-service:{image_tag}',
                description='Pushed container image short address (no registry) by tag.'
            )
            expected_step_result.success = False
            expected_step_result.message = f"Error pushing container image ({image_pull_address}) " +\
                f" to tag ({image_push_address}) using skopeo: \n" +\
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
            mock_skopeo.copy.assert_called_once_with(
                "--src-tls-verify=true",
                "--dest-tls-verify=true",
                f"--authfile={containers_config_auth_file}",
                f'containers-storage:{image_pull_address}',
                f'docker://{image_push_address}',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

    def test_fail_getting_digest(self, mock_skopeo, mock_get_container_image_digest):
        with TempDirectory() as temp_dir:
            image_tag = '1.0-69442c8'
            image_pull_address = f'localhost/fake-org/fake-app/fake-service:{image_tag}'
            image_push_address = f'mock-reg.xyz/fake-org/fake-app/fake-service:{image_tag}'
            step_config = {
                'container-image-pull-address': image_pull_address,
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-push-repository': 'fake-org/fake-app/fake-service',
                'container-image-push-tag': image_tag
            }

            mock_get_container_image_digest.side_effect = RuntimeError('mock error getting digest')

            self.__run_test(
                temp_dir=temp_dir,
                image_tag=image_tag,
                image_pull_address=image_pull_address,
                image_push_address=image_push_address,
                step_config=step_config,
                mock_skopeo=mock_skopeo,
                mock_get_container_image_digest=mock_get_container_image_digest,
                expected_step_result_success=False,
                expected_step_result_message="Error getting pushed container image digest:" \
                    " mock error getting digest",
                include_digest_results=False
            )
