"""Test Podman Sign

Tests signature generation for a container image.
"""
import os
import re
from io import IOBase
from pathlib import Path
from unittest.mock import MagicMock, patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any, StringRegexParam
from tssc.step_implementers.sign_container_image import PodmanSign


class TestStepImplementerSignContainerImagePodmanSign(BaseStepImplementerTestCase):
    """Test Step Implementer Sign Container Image Using Podman

    Test runner for the PodmanSign.
    """

    def create_step_implementer(
        self,
        step_config={},
        results_dir_path='',
        results_file_name='',
        work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=PodmanSign,
            step_config=step_config,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    @staticmethod
    def gpg_side_effect(*_args, **kwargs):
        """Side effect for gpg key load"""
        kwargs['_out']('fpr:::::::::DD7208BA0A6359F65B906B29CF4AC14A3D109637:')

    @staticmethod
    def generate_config():
        """Generate tssc config for tests"""
        return {
            'tssc-config': {
                'sign-container-image': {
                    'implementer': 'PodmanSign',
                    'config': {
                        'container-image-signer-pgp-private-key': '''
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
                    }
                }
            }
        }

    @staticmethod
    def generate_results(temp_dir):
        """Generate valid results"""
        container_image_tag = 'tssc:hello-node:latest'
        temp_dir.makedir('tssc-results')
        temp_dir.write(
            'tssc-results/tssc-results.yml',
            bytes(
                f'''tssc-results:
              push-container-image:
                container-image-tag: {container_image_tag}
            ''', 'utf-8')
        )
        return container_image_tag

    def test_push_container_signature_specify_podman_implementer_missing_config_values(self):
        """Test for missing config values"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImagePodmanSign.generate_config()
            config['tssc-config']['sign-container-image']['config'] = {}
            expected_step_results = {'tssc-results': {'sign-container-image': {}}}

            with self.assertRaisesRegex(
                AssertionError,
                r"The runtime step configuration \({}\) is missing the required configuration "
                r"keys \(\['container-image-signer-pgp-private-key'\]\)"
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results
                )

    def test_push_container_signature_specify_podman_implementer_missing_config_step_values(self):
        """Test for missing result step values"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImagePodmanSign.generate_config()
            expected_step_results = {'tssc-results': {'sign-container-image': {}}}

            with self.assertRaisesRegex(
                AssertionError,
                r"Expected key \(container-image-tag\) to be in step results from step " \
                r"\(push-container-image\): None"
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results
                )

    @patch('sh.gpg', create=True)
    def test_push_container_signature_specify_podman_implementer_pgp_failure(self, gpg_mock):
        """Test for pgp key load failure"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImagePodmanSign.generate_config()
            TestStepImplementerSignContainerImagePodmanSign.generate_results(temp_dir)

            gpg_mock.side_effect = sh.ErrorReturnCode(
                'PodmanSign',
                b'mock stdout',
                b'mock error about curl runtime'
            )
            with self.assertRaisesRegex(
                RuntimeError,
                r'Unexpected error importing pgp private key'
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results=None
                )

    @patch('sh.gpg', create=True)
    def test_push_container_signature_specify_podman_implementer_pgp_no_fingerprint(self, gpg_mock):
        """Test for pgp key missing fingerprint"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImagePodmanSign.generate_config()
            TestStepImplementerSignContainerImagePodmanSign.generate_results(temp_dir)

            gpg_mock.return_value = ''
            with self.assertRaisesRegex(
                RuntimeError,
                r'Unexpected error getting PGP fingerprint for PGP key to sign .*'
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results=None
                )

    @patch('sh.podman', create=True)
    @patch('sh.gpg', create=True)
    def test_push_container_signature_specify_podman_implementer_podman_failure(
        self,
        gpg_mock,
        podman_mock
    ):
        """Test for podman sign failure"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImagePodmanSign.generate_config()
            TestStepImplementerSignContainerImagePodmanSign.generate_results(temp_dir)

            gpg_mock.side_effect = TestStepImplementerSignContainerImagePodmanSign.gpg_side_effect
            podman_mock.image.side_effect = sh.ErrorReturnCode(
                'PodmanSign',
                b'mock stdout',
                b'mock error about curl runtime'
            )

            with self.assertRaisesRegex(
                RuntimeError,
                r'Unexpected error signing image .*'
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results=None
                )

    @patch('sh.podman', create=True)
    @patch('sh.gpg', create=True)
    def test_push_container_signature_specify_podman_implementer_with_wrong_number_of_signatures(
        self,
        gpg_mock,
        _podman_mock
    ):
        """Test for invalid signature signing"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImagePodmanSign.generate_config()
            TestStepImplementerSignContainerImagePodmanSign.generate_results(temp_dir)
            gpg_mock.side_effect = TestStepImplementerSignContainerImagePodmanSign.gpg_side_effect

            with self.assertRaisesRegex(
                RuntimeError,
                r'Unexpected number of signature files, expected 1: .*'
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results=None
                )

    @patch('sh.podman', create=True)
    @patch('sh.gpg', create=True)
    def test_push_container_signature_specify_podman_implementer_success(
        self,
        gpg_mock,
        podman_mock
    ):
        """Test for signature signing success"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImagePodmanSign.generate_config()
            config_dict = config['tssc-config']['sign-container-image']['config']
            key = config_dict['container-image-signer-pgp-private-key']
            image_name = TestStepImplementerSignContainerImagePodmanSign.generate_results(temp_dir)

            signature_dir = os.path.join(
                temp_dir.path,
                'tssc-working',
                'sign-container-image',
                'image-signature',
                'hello-node'
            )
            signature_file = os.path.join(signature_dir, 'signature-1')
            temp_dir.makedir(signature_dir)
            temp_dir.write(signature_file, b'signature')
            gpg_mock.side_effect = TestStepImplementerSignContainerImagePodmanSign.gpg_side_effect
            fingerprint = 'DD7208BA0A6359F65B906B29CF4AC14A3D109637'

            expected_step_results = {
                'tssc-results': {
                    'push-container-image': {
                        'container-image-tag': image_name
                    },
                    'sign-container-image': {
                        'container-image-signature-file-path': signature_file,
                        'container-image-signature-name': 'hello-node/signature-1',
                        'container-image-signature-private-key-fingerprint': fingerprint
                    }
                }
            }

            self.run_step_test_with_result_validation(
                temp_dir,
                'sign-container-image',
                config,
                expected_step_results
            )
            gpg_mock.assert_called_once_with(
                '--import',
                '--fingerprint',
                '--with-colons',
                '--import-options=import-show',
                _in=key,
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )

            podman_mock.image(
                'sign',
                f'--sign-by={fingerprint}',
                f'--directory={signature_dir}',
                f'docker://{image_name}',
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )

    @staticmethod
    def create_podman_image_sign_side_effect():
        def podman_image_sign_side_effect(*args, **kwargs):
            if (args[0] == 'sign'):
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
                mock_image_signature_path = os.path.join(
                    mock_image_signature_dir_path,
                    'signature-0'
                )
                Path(mock_image_signature_path).touch()

        return podman_image_sign_side_effect

    @patch('sh.podman', create=True)
    def test___sign_image(self, podman_mock):
        with TempDirectory() as temp_dir:
            pgp_private_key_fingerprint = 'abc123'
            image_signatures_directory = os.path.join(temp_dir.path, 'signatures')
            container_image_tag = 'does/not/matter:v0.42.0'

            podman_mock.image.side_effect = TestStepImplementerSignContainerImagePodmanSign.\
                create_podman_image_sign_side_effect()

            PodmanSign._PodmanSign__sign_image(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory=image_signatures_directory,
                container_image_tag=container_image_tag
            )

            podman_mock.image.assert_called_once_with(
                'sign',
                f'--sign-by={pgp_private_key_fingerprint}',
                f'--directory={image_signatures_directory}',
                f'docker://{container_image_tag}',
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )

    @patch.object(PodmanSign, '_PodmanSign__import_pgp_key')
    @patch.object(PodmanSign, '_PodmanSign__sign_image')
    def test__run_step_pass(self, sign_image_mock, import_pgp_key_mock):
        pgp_private_key_fingerprint = 'abc123'
        step_config = {
        }
        container_image_tag = 'does/not/matter:v0.42.0'
        signature_name = 'does/not/matter/signature-0'

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            temp_dir.write(
                f'tssc-results/{results_file_name}',
                bytes(
                    f'''---
tssc-results:
    push-container-image:
        container-image-tag: '{container_image_tag}'
                    ''',
                    'utf-8'
                )
            )

            def import_pgp_key_side_effect(pgp_private_key):
                return pgp_private_key_fingerprint
            import_pgp_key_mock.side_effect = import_pgp_key_side_effect

            def sign_image_side_effect(
                pgp_private_key_fingerprint,
                image_signatures_directory,
                container_image_tag
            ):
                return os.path.join(image_signatures_directory, signature_name)
            sign_image_mock.side_effect = sign_image_side_effect

            run_step_results = step_implementer._run_step()

            self.assertEqual(
                run_step_results,
                {
                    'container-image-signature-private-key-fingerprint': pgp_private_key_fingerprint,
                    'container-image-signature-file-path': os.path.join(
                        temp_dir.path,
                        'working/test/image-signature',
                        signature_name
                    ),
                    'container-image-signature-name': signature_name
                }
            )

            sign_image_mock.assert_called_once_with(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory=StringRegexParam(r".+"),
                container_image_tag=container_image_tag
            )
