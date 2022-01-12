import os
import re
from io import IOBase
from pathlib import Path
from unittest.mock import patch

import mock
import sh
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared import ContainerDeployMixin
from ploigos_step_runner.step_implementers.sign_container_image import \
    PodmanSign
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any


class TestStepImplementerSignContainerImagePodmanBase(BaseStepImplementerTestCase):
    TEST_FAKE_PRIVATE_KEY = '''
        -----BEGIN RSA PRIVATE KEY-----
        MIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp
        wmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5
        1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh
        3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2
        pIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX
        GukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il
        AkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF
        L0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k
        X6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl
        U9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ
        37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=
        -----END RSA PRIVATE KEY-----'''

    @staticmethod
    def generate_config():
        return {
            'signer-pgp-private-key': \
                TestStepImplementerSignContainerImagePodmanBase.TEST_FAKE_PRIVATE_KEY
        }

    @staticmethod
    def create_podman_image_sign_side_effect(num_signatures=1):
        def podman_image_sign_side_effect(*args, **kwargs):
            if args[0] == 'sign':
                # determine the directory for the signature
                for arg in args:
                    match = re.match(r'^--directory=(?P<image_signature_directory>.+)$', arg)
                    if match:
                        image_signatures_directory =match.groupdict()['image_signature_directory']
                        break

                # touch mock signature file
                mock_image_signature_dir_path = os.path.join(
                    image_signatures_directory,
                    'mock/sig/path'
                )
                os.makedirs(mock_image_signature_dir_path)

                for i in range(num_signatures):
                    mock_image_signature_path = os.path.join(
                        mock_image_signature_dir_path,
                        f'signature-{i}'
                    )
                    Path(mock_image_signature_path).touch()

        return podman_image_sign_side_effect

    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=PodmanSign,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

@patch.object(ContainerDeployMixin, 'step_implementer_config_defaults', return_value={})
class TestStepImplementerSignContainerImagePodman_step_implementer_config_defaults(
    TestStepImplementerSignContainerImagePodmanBase
):
    def test_results(self, mock_super_config_defaults):
        defaults = PodmanSign.step_implementer_config_defaults()
        expected_defaults = {
            'src-tls-verify': 'true'
        }
        self.assertEqual(defaults, expected_defaults)
        mock_super_config_defaults.assert_called_once()

@patch.object(ContainerDeployMixin, '_required_config_or_result_keys', return_value=[])
class TestStepImplementerSignContainerImagePodman__required_config_or_result_keys(
    TestStepImplementerSignContainerImagePodmanBase
):
    def test_results(self, mock_super_required_keys):
        required_keys = PodmanSign._required_config_or_result_keys()
        expected_required_keys = [
            ['signer-pgp-private-key', 'container-image-signer-pgp-private-key']
        ]
        self.assertEqual(required_keys, expected_required_keys)
        mock_super_required_keys.assert_called_once()

@patch.object(
    PodmanSign,
    '_get_deploy_time_container_image_address',
    return_value='mock-deploy-time-container-image-address'
)
@patch('ploigos_step_runner.step_implementers.sign_container_image.podman_sign.container_registries_login')
@patch('ploigos_step_runner.step_implementers.sign_container_image.podman_sign.upload_file')
@patch('ploigos_step_runner.step_implementers.sign_container_image.podman_sign.import_pgp_key')
@patch.object(PodmanSign, '_PodmanSign__sign_image')
class TestStepImplementerSignContainerImagePodman__run_step(
    TestStepImplementerSignContainerImagePodmanBase
):
    def test_pass(
        self,
        mock_sign_image,
        mock_import_pgp_key,
        mock_upload_file,
        mock_container_registries_login,
        mock_get_deploy_time_container_image_address
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = TestStepImplementerSignContainerImagePodmanBase.generate_config()
            signature_name = 'does/not/matter/signature-0'

            # setup mocks
            def import_pgp_key_side_effect(pgp_private_key):
                return pgp_private_key_fingerprint
            mock_import_pgp_key.side_effect = import_pgp_key_side_effect

            def sign_image_side_effect(
                pgp_private_key_fingerprint,
                image_signatures_directory,
                container_image_address
            ):
                return os.path.join(image_signatures_directory, signature_name)
            mock_sign_image.side_effect = sign_image_side_effect

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                parent_work_dir_path=parent_work_dir_path
            )
            result = step_implementer._run_step()

            # validate
            mock_import_pgp_key.assert_called_once_with(
                pgp_private_key=step_config['signer-pgp-private-key']
            )
            mock_sign_image.assert_called_once_with(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory= os.path.join(
                    parent_work_dir_path,
                    'sign-container-image/image-signature'
                ),
                container_image_address='mock-deploy-time-container-image-address'
            )
            mock_get_deploy_time_container_image_address.assert_called_once()
            mock_upload_file.assert_not_called()
            mock_container_registries_login.assert_called_once_with(
                registries=None,
                containers_config_tls_verify=True,
                container_command_short_name='podman'
            )

            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='PodmanSign',
                sub_step_implementer_name='PodmanSign'
            )
            expected_step_result.add_artifact(
                name='container-image-signed-address',
                value='mock-deploy-time-container-image-address',
            )
            expected_step_result.add_artifact(
                name='container-image-signature-file-path',
                value= os.path.join(
                    parent_work_dir_path,
                    'sign-container-image/image-signature',
                    signature_name
                )
            )
            expected_step_result.add_artifact(
                name='container-image-signature-name',
                value=signature_name
            )
            expected_step_result.add_artifact(
                name='container-image-signature-signer-private-key-fingerprint',
                value=pgp_private_key_fingerprint
            )
            self.assertEqual(expected_step_result, result)

    def test_pass_with_signature_upload_to_file(
        self,
        mock_sign_image,
        mock_import_pgp_key,
        mock_upload_file,
        mock_container_registries_login,
        mock_get_deploy_time_container_image_address
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = TestStepImplementerSignContainerImagePodmanBase.generate_config()
            step_config['container-image-signature-destination-url'] = '/mock/container-sigs'
            signature_name = 'does/not/matter/signature-0'

            # setup mocks
            def import_pgp_key_side_effect(pgp_private_key):
                return pgp_private_key_fingerprint
            mock_import_pgp_key.side_effect = import_pgp_key_side_effect

            def sign_image_side_effect(
                    pgp_private_key_fingerprint,
                    image_signatures_directory,
                    container_image_address
            ):
                return os.path.join(image_signatures_directory, signature_name)
            mock_sign_image.side_effect = sign_image_side_effect

            mock_upload_file.return_value = "mock upload results"

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                parent_work_dir_path=parent_work_dir_path
            )
            result = step_implementer._run_step()

            # validate
            mock_import_pgp_key.assert_called_once_with(
                pgp_private_key=step_config['signer-pgp-private-key']
            )
            mock_sign_image.assert_called_once_with(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory= os.path.join(
                    parent_work_dir_path,
                    'sign-container-image/image-signature'
                ),
                container_image_address='mock-deploy-time-container-image-address'
            )
            mock_upload_file.assert_called_once_with(
                file_path=mock.ANY,
                destination_uri='/mock/container-sigs/does/not/matter/signature-0',
                username=None,
                password=None
            )
            mock_container_registries_login.assert_called_once_with(
                registries=None,
                containers_config_tls_verify=True,
                container_command_short_name='podman'
            )
            mock_get_deploy_time_container_image_address.assert_called_once()

            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='PodmanSign',
                sub_step_implementer_name='PodmanSign'
            )
            expected_step_result.add_artifact(
                name='container-image-signed-address',
                value='mock-deploy-time-container-image-address',
            )
            expected_step_result.add_artifact(
                name='container-image-signature-file-path',
                value= os.path.join(
                    parent_work_dir_path,
                    'sign-container-image/image-signature',
                    signature_name
                )
            )
            expected_step_result.add_artifact(
                name='container-image-signature-name',
                value=signature_name
            )
            expected_step_result.add_artifact(
                name='container-image-signature-signer-private-key-fingerprint',
                value=pgp_private_key_fingerprint
            )
            expected_step_result.add_artifact(
                name='container-image-signature-uri',
                description='URI of the uploaded container image signature',
                value='/mock/container-sigs/does/not/matter/signature-0'
            )
            expected_step_result.add_artifact(
                name='container-image-signature-upload-results',
                description='Results of uploading the container image signature' \
                            ' to the given destination.',
                value='mock upload results'
            )
            self.assertEqual(expected_step_result, result)

    def test_pass_with_signature_upload_to_remote_with_auth(
        self,
        mock_sign_image,
        mock_import_pgp_key,
        mock_upload_file,
        mock_container_registries_login,
        mock_get_deploy_time_container_image_address
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = TestStepImplementerSignContainerImagePodmanBase.generate_config()
            step_config['container-image-signature-destination-url'] = \
                'https://ploigos.com/mock/container-sigs'
            step_config['container-image-signature-destination-username'] = 'test-user'
            step_config['container-image-signature-destination-password'] = 'test-pass'
            signature_name = 'does/not/matter/signature-0'

            # setup mocks
            def import_pgp_key_side_effect(pgp_private_key):
                return pgp_private_key_fingerprint
            mock_import_pgp_key.side_effect = import_pgp_key_side_effect

            def sign_image_side_effect(
                    pgp_private_key_fingerprint,
                    image_signatures_directory,
                    container_image_address
            ):
                return os.path.join(image_signatures_directory, signature_name)
            mock_sign_image.side_effect = sign_image_side_effect

            mock_upload_file.return_value = "mock upload results"

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                parent_work_dir_path=parent_work_dir_path
            )
            result = step_implementer._run_step()

            # validate
            mock_import_pgp_key.assert_called_once_with(
                pgp_private_key=step_config['signer-pgp-private-key']
            )
            mock_sign_image.assert_called_once_with(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory= os.path.join(
                    parent_work_dir_path,
                    'sign-container-image/image-signature'
                ),
                container_image_address='mock-deploy-time-container-image-address'
            )
            mock_upload_file.assert_called_once_with(
                file_path=mock.ANY,
                destination_uri='https://ploigos.com/mock/container-sigs/does/not/matter/signature-0',
                username='test-user',
                password='test-pass'
            )
            mock_container_registries_login.assert_called_once_with(
                registries=None,
                containers_config_tls_verify=True,
                container_command_short_name='podman'
            )
            mock_get_deploy_time_container_image_address.assert_called_once()

            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='PodmanSign',
                sub_step_implementer_name='PodmanSign'
            )
            expected_step_result.add_artifact(
                name='container-image-signed-address',
                value='mock-deploy-time-container-image-address',
            )
            expected_step_result.add_artifact(
                name='container-image-signature-file-path',
                value= os.path.join(
                    parent_work_dir_path,
                    'sign-container-image/image-signature',
                    signature_name
                )
            )
            expected_step_result.add_artifact(
                name='container-image-signature-name',
                value=signature_name
            )
            expected_step_result.add_artifact(
                name='container-image-signature-signer-private-key-fingerprint',
                value=pgp_private_key_fingerprint
            )
            expected_step_result.add_artifact(
                name='container-image-signature-uri',
                description='URI of the uploaded container image signature',
                value='https://ploigos.com/mock/container-sigs/does/not/matter/signature-0'
            )
            expected_step_result.add_artifact(
                name='container-image-signature-upload-results',
                description='Results of uploading the container image signature' \
                            ' to the given destination.',
                value='mock upload results'
            )
            self.assertEqual(expected_step_result, result)

    def test_pass_with_signature_upload_to_remote_with_auth_failure(
        self,
        mock_sign_image,
        mock_import_pgp_key,
        mock_upload_file,
        mock_container_registries_login,
        mock_get_deploy_time_container_image_address
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = TestStepImplementerSignContainerImagePodmanBase.generate_config()
            step_config['container-image-signature-destination-url'] = \
                'https://ploigos.com/mock/container-sigs'
            step_config['container-image-signature-destination-username'] = 'test-user'
            step_config['container-image-signature-destination-password'] = 'test-pass'
            signature_name = 'does/not/matter/signature-0'

            # setup mocks
            def import_pgp_key_side_effect(pgp_private_key):
                return pgp_private_key_fingerprint
            mock_import_pgp_key.side_effect = import_pgp_key_side_effect

            def sign_image_side_effect(
                    pgp_private_key_fingerprint,
                    image_signatures_directory,
                    container_image_address
            ):
                return os.path.join(image_signatures_directory, signature_name)
            mock_sign_image.side_effect = sign_image_side_effect

            mock_upload_file.side_effect = RuntimeError('mock upload error')

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                parent_work_dir_path=parent_work_dir_path
            )
            result = step_implementer._run_step()

            # validate
            mock_import_pgp_key.assert_called_once_with(
                pgp_private_key=step_config['signer-pgp-private-key']
            )
            mock_sign_image.assert_called_once_with(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory= os.path.join(
                    parent_work_dir_path,
                    'sign-container-image/image-signature'
                ),
                container_image_address='mock-deploy-time-container-image-address'
            )
            mock_upload_file.assert_called_once_with(
                file_path=mock.ANY,
                destination_uri='https://ploigos.com/mock/container-sigs/does/not/matter/signature-0',
                username='test-user',
                password='test-pass'
            )
            mock_container_registries_login.assert_called_once_with(
                registries=None,
                containers_config_tls_verify=True,
                container_command_short_name='podman'
            )
            mock_get_deploy_time_container_image_address.assert_called_once()

            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='PodmanSign',
                sub_step_implementer_name='PodmanSign'
            )
            expected_step_result.add_artifact(
                name='container-image-signed-address',
                value='mock-deploy-time-container-image-address',
            )
            expected_step_result.add_artifact(
                name='container-image-signature-file-path',
                value= os.path.join(
                    parent_work_dir_path,
                    'sign-container-image/image-signature',
                    signature_name
                )
            )
            expected_step_result.add_artifact(
                name='container-image-signature-name',
                value=signature_name
            )
            expected_step_result.add_artifact(
                name='container-image-signature-signer-private-key-fingerprint',
                value=pgp_private_key_fingerprint
            )
            expected_step_result.add_artifact(
                name='container-image-signature-uri',
                description='URI of the uploaded container image signature',
                value='https://ploigos.com/mock/container-sigs/does/not/matter/signature-0'
            )
            expected_step_result.success = False
            expected_step_result.message = 'mock upload error'

            self.assertEqual(expected_step_result, result)

    def test_fail_import_pgp_key(
        self,
        mock_sign_image,
        mock_import_pgp_key,
        mock_upload_file,
        mock_container_registries_login,
        mock_get_deploy_time_container_image_address
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = TestStepImplementerSignContainerImagePodmanBase.generate_config()
            signature_name = 'does/not/matter/signature-0'

            # setup mocks
            mock_import_pgp_key.side_effect = RuntimeError('mock error importing pgp key')

            def sign_image_side_effect(
                    pgp_private_key_fingerprint,
                    image_signatures_directory,
                    container_image_address
            ):
                return os.path.join(image_signatures_directory, signature_name)

            mock_sign_image.side_effect = sign_image_side_effect

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                parent_work_dir_path=parent_work_dir_path
            )
            result = step_implementer._run_step()

            # validate
            mock_import_pgp_key.assert_called_once_with(
                pgp_private_key=step_config['signer-pgp-private-key']
            )
            mock_upload_file.assert_not_called()
            mock_container_registries_login.assert_not_called()
            mock_get_deploy_time_container_image_address.assert_called_once()

            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='PodmanSign',
                sub_step_implementer_name='PodmanSign'
            )
            expected_step_result.success = False
            expected_step_result.message = 'mock error importing pgp key'

            self.assertEqual(expected_step_result, result)

    def test_fail_sign_image(
        self,
        mock_sign_image,
        mock_import_pgp_key,
        mock_upload_file,
        mock_container_registries_login,
        mock_get_deploy_time_container_image_address
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = TestStepImplementerSignContainerImagePodmanBase.generate_config()

            # setup mocks
            def import_pgp_key_side_effect(pgp_private_key):
                return pgp_private_key_fingerprint
            mock_import_pgp_key.side_effect = import_pgp_key_side_effect

            mock_sign_image.side_effect = StepRunnerException('mock error signing image')

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                parent_work_dir_path=parent_work_dir_path
            )
            result = step_implementer._run_step()

            # validate
            mock_import_pgp_key.assert_called_once_with(
                pgp_private_key=step_config['signer-pgp-private-key']
            )
            mock_sign_image.assert_called_once_with(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory= os.path.join(
                    parent_work_dir_path,
                    'sign-container-image/image-signature'
                ),
                container_image_address='mock-deploy-time-container-image-address'
            )
            mock_container_registries_login.assert_called_once_with(
                registries=None,
                containers_config_tls_verify=True,
                container_command_short_name='podman'
            )
            mock_get_deploy_time_container_image_address.assert_called_once()

            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='PodmanSign',
                sub_step_implementer_name='PodmanSign'
            )
            expected_step_result.add_artifact(
                name='container-image-signature-signer-private-key-fingerprint',
                value=pgp_private_key_fingerprint
            )
            expected_step_result.success = False
            expected_step_result.message = 'mock error signing image'
            self.assertEqual(expected_step_result, result)
@patch('sh.podman', create=True)
class TestStepImplementerSignContainerImagePodman___sign_image(
    TestStepImplementerSignContainerImagePodmanBase
):
    def test_success(self, podman_mock):
        with TempDirectory() as temp_dir:
            pgp_private_key_fingerprint = 'abc123'
            image_signatures_directory = os.path.join(temp_dir.path, 'signatures')
            container_image_address = 'does/not/matter:v0.42.0'

            podman_mock.image.side_effect = TestStepImplementerSignContainerImagePodmanBase.\
                create_podman_image_sign_side_effect()

            PodmanSign._PodmanSign__sign_image(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory=image_signatures_directory,
                container_image_address=container_image_address
            )

            podman_mock.image.assert_called_once_with(
                'sign',
                f'--sign-by={pgp_private_key_fingerprint}',
                f'--directory={image_signatures_directory}',
                f'docker://{container_image_address}',
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )

    def test_podman_image_sign_fail(self, podman_mock):
        with TempDirectory() as temp_dir:
            pgp_private_key_fingerprint = 'abc123'
            image_signatures_directory = os.path.join(temp_dir.path, 'signatures')
            container_image_address = 'does/not/matter:v0.42.0'

            podman_mock.image.side_effect = sh.ErrorReturnCode('podman', b'mock stdout', b'mock error signing image')

            with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    rf"Error signing image \({container_image_address}\):"
                    r".*RAN: podman"
                    r".*STDOUT:"
                    r".*mock stdout"
                    r".*STDERR:"
                    r".*mock error signing image",
                    re.DOTALL
                )
            ):
                PodmanSign._PodmanSign__sign_image(
                    pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                    image_signatures_directory=image_signatures_directory,
                    container_image_address=container_image_address
                )

            podman_mock.image.assert_called_once_with(
                'sign',
                f'--sign-by={pgp_private_key_fingerprint}',
                f'--directory={image_signatures_directory}',
                f'docker://{container_image_address}',
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )

    def test_podman_image_sign_to_many_sigs(self, podman_mock):
        with TempDirectory() as temp_dir:
            pgp_private_key_fingerprint = 'abc123'
            image_signatures_directory = os.path.join(temp_dir.path, 'signatures')
            container_image_address = 'does/not/matter:v0.42.0'

            podman_mock.image.side_effect = TestStepImplementerSignContainerImagePodmanBase.\
                create_podman_image_sign_side_effect(num_signatures=2)

            with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Unexpected number of signature files, expected 1: \['.*', '.*'\]",
                    re.DOTALL
                )
            ):
                PodmanSign._PodmanSign__sign_image(
                    pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                    image_signatures_directory=image_signatures_directory,
                    container_image_address=container_image_address
                )

            podman_mock.image.assert_called_once_with(
                'sign',
                f'--sign-by={pgp_private_key_fingerprint}',
                f'--directory={image_signatures_directory}',
                f'docker://{container_image_address}',
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )
