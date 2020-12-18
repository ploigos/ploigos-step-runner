# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
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
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.sign_container_image import PodmanSign
from ploigos_step_runner.step_result import StepResult


class TestStepImplementerSignContainerImagePodman(BaseStepImplementerTestCase):
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
            'container-image-signer-pgp-private-key': \
                TestStepImplementerSignContainerImagePodman.TEST_FAKE_PRIVATE_KEY
        }

    @staticmethod
    def gpg_side_effect(*_args, **kwargs):
        """Side effect for gpg key load"""
        kwargs['_out']('fpr:::::::::DD7208BA0A6359F65B906B29CF4AC14A3D109637:')

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
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=PodmanSign,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = PodmanSign.step_implementer_config_defaults()
        expected_defaults = {}
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = PodmanSign._required_config_or_result_keys()
        expected_required_keys = [
            'container-image-signer-pgp-private-key',
            'container-image-tag'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    @patch.object(PodmanSign, '_PodmanSign__import_pgp_key')
    @patch.object(PodmanSign, '_PodmanSign__sign_image')
    def test_run_step_pass(self, sign_image_mock, import_pgp_key_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = TestStepImplementerSignContainerImagePodman.generate_config()
            container_image_tag = 'does/not/matter:v0.42.0'
            signature_name = 'does/not/matter/signature-0'

            # Previous (fake) results
            artifact_config = {
                'container-image-tag': {'value': container_image_tag}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

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

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()
            import_pgp_key_mock.assert_called_once_with(
                pgp_private_key=step_config['container-image-signer-pgp-private-key']
            )
            sign_image_mock.assert_called_once_with(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory= os.path.join(
                    work_dir_path,
                    'sign-container-image/image-signature'
                ),
                container_image_tag=container_image_tag
            )

            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='PodmanSign',
                sub_step_implementer_name='PodmanSign'
            )
            expected_step_result.add_artifact(
                name='container-image-signature-file-path',
                value= os.path.join(
                    work_dir_path,
                    'sign-container-image/image-signature',
                    signature_name
                )
            )
            expected_step_result.add_artifact(
                name='container-image-signature-name',
                value=signature_name
            )
            expected_step_result.add_artifact(
                name='container-image-signature-private-key-fingerprint',
                value=pgp_private_key_fingerprint
            )
            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())

    @patch.object(PodmanSign, '_PodmanSign__import_pgp_key')
    @patch.object(PodmanSign, '_PodmanSign__sign_image')
    def test_run_step_fail_import_pgp_key(self, sign_image_mock, import_pgp_key_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = TestStepImplementerSignContainerImagePodman.generate_config()
            container_image_tag = 'does/not/matter:v0.42.0'
            signature_name = 'does/not/matter/signature-0'

            # Previous (fake) results
            artifact_config = {
                'container-image-tag': {'value': container_image_tag}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            import_pgp_key_mock.side_effect = StepRunnerException('mock error importing pgp key')

            def sign_image_side_effect(
                    pgp_private_key_fingerprint,
                    image_signatures_directory,
                    container_image_tag
            ):
                return os.path.join(image_signatures_directory, signature_name)

            sign_image_mock.side_effect = sign_image_side_effect

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()
            import_pgp_key_mock.assert_called_once_with(
                pgp_private_key=step_config['container-image-signer-pgp-private-key']
            )

            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='PodmanSign',
                sub_step_implementer_name='PodmanSign'
            )
            expected_step_result.success = False
            expected_step_result.message = 'mock error importing pgp key'

            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())

    @patch.object(PodmanSign, '_PodmanSign__import_pgp_key')
    @patch.object(PodmanSign, '_PodmanSign__sign_image')
    def test_run_step_fail_sign_image(self, sign_image_mock, import_pgp_key_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = TestStepImplementerSignContainerImagePodman.generate_config()
            container_image_tag = 'does/not/matter:v0.42.0'

            # Previous (fake) results
            artifact_config = {
                'container-image-tag': {'value': container_image_tag}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            def import_pgp_key_side_effect(pgp_private_key):
                return pgp_private_key_fingerprint
            import_pgp_key_mock.side_effect = import_pgp_key_side_effect

            sign_image_mock.side_effect = StepRunnerException('mock error signing image')

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()
            import_pgp_key_mock.assert_called_once_with(
                pgp_private_key=step_config['container-image-signer-pgp-private-key']
            )
            sign_image_mock.assert_called_once_with(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint,
                image_signatures_directory= os.path.join(
                    work_dir_path,
                    'sign-container-image/image-signature'
                ),
                container_image_tag=container_image_tag
            )

            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='PodmanSign',
                sub_step_implementer_name='PodmanSign'
            )
            expected_step_result.add_artifact(
                name='container-image-signature-private-key-fingerprint',
                value=pgp_private_key_fingerprint
            )
            expected_step_result.success = False
            expected_step_result.message = 'mock error signing image'

            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())

    @patch('sh.gpg', create=True)
    def test___import_pgp_key_success(self, gpg_mock):
        gpg_mock.side_effect = TestStepImplementerSignContainerImagePodman.gpg_side_effect

        pgp_private_key=TestStepImplementerSignContainerImagePodman.TEST_FAKE_PRIVATE_KEY
        PodmanSign._PodmanSign__import_pgp_key(
            pgp_private_key=pgp_private_key
        )
        gpg_mock.assert_called_once_with(
            '--import',
            '--fingerprint',
            '--with-colons',
            '--import-options=import-show',
            _in=pgp_private_key,
            _out=Any(IOBase),
            _err_to_out=True,
            _tee='out'
        )

    @patch('sh.gpg', create=True)
    def test___import_pgp_key_gpg_import_fail(self, gpg_mock):
        gpg_mock.side_effect = sh.ErrorReturnCode('gpg', b'mock stdout', b'mock error')

        pgp_private_key=TestStepImplementerSignContainerImagePodman.TEST_FAKE_PRIVATE_KEY

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Error importing pgp private key:"
                r".*RAN: gpg"
                r".*STDOUT:"
                r".*mock stdout"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            )
        ):
            PodmanSign._PodmanSign__import_pgp_key(
                pgp_private_key=pgp_private_key
            )

        gpg_mock.assert_called_once_with(
            '--import',
            '--fingerprint',
            '--with-colons',
            '--import-options=import-show',
            _in=pgp_private_key,
            _out=Any(IOBase),
            _err_to_out=True,
            _tee='out'
        )

    @patch('sh.gpg', create=True)
    def test___import_pgp_key_fail_get_fingerprint(self, gpg_mock):
        pgp_private_key=TestStepImplementerSignContainerImagePodman.TEST_FAKE_PRIVATE_KEY

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                r"Error getting PGP fingerprint for PGP key"
                r" to sign container image\(s\) with. See stdout and stderr for more info.",
                re.DOTALL
            )
        ):
            PodmanSign._PodmanSign__import_pgp_key(
                pgp_private_key=pgp_private_key
            )

        gpg_mock.assert_called_once_with(
            '--import',
            '--fingerprint',
            '--with-colons',
            '--import-options=import-show',
            _in=pgp_private_key,
            _out=Any(IOBase),
            _err_to_out=True,
            _tee='out'
        )

    @patch('sh.podman', create=True)
    def test___sign_image_success(self, podman_mock):
        with TempDirectory() as temp_dir:
            pgp_private_key_fingerprint = 'abc123'
            image_signatures_directory = os.path.join(temp_dir.path, 'signatures')
            container_image_tag = 'does/not/matter:v0.42.0'

            podman_mock.image.side_effect = TestStepImplementerSignContainerImagePodman.\
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

    @patch('sh.podman', create=True)
    def test___sign_image_podman_image_sign_fail(self, podman_mock):
        with TempDirectory() as temp_dir:
            pgp_private_key_fingerprint = 'abc123'
            image_signatures_directory = os.path.join(temp_dir.path, 'signatures')
            container_image_tag = 'does/not/matter:v0.42.0'

            podman_mock.image.side_effect = sh.ErrorReturnCode('podman', b'mock stdout', b'mock error signing image')

            with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    rf"Error signing image \({container_image_tag}\):"
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

    @patch('sh.podman', create=True)
    def test___sign_image_podman_image_sign_to_many_sigs(self, podman_mock):
        with TempDirectory() as temp_dir:
            pgp_private_key_fingerprint = 'abc123'
            image_signatures_directory = os.path.join(temp_dir.path, 'signatures')
            container_image_tag = 'does/not/matter:v0.42.0'

            podman_mock.image.side_effect = TestStepImplementerSignContainerImagePodman.\
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
