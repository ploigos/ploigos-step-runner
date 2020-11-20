# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
from io import IOBase
from pathlib import Path
from unittest.mock import MagicMock, patch
from testfixtures import TempDirectory
from tssc.step_implementers.sign_container_image import PodmanSign
from tssc.step_result import StepResult
from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from tests.helpers.test_utils import Any, StringRegexParam


class TestStepImplementerPodmanSignSourceBase(BaseStepImplementerTestCase):
    @staticmethod
    def generate_config():
        """Generate tssc config for tests"""
        return {
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

    @staticmethod
    def gpg_side_effect(*_args, **kwargs):
        """Side effect for gpg key load"""
        kwargs['_out']('fpr:::::::::DD7208BA0A6359F65B906B29CF4AC14A3D109637:')

    @staticmethod
    def create_podman_image_sign_side_effect():
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
                mock_image_signature_path = os.path.join(
                    mock_image_signature_dir_path,
                    'signature-0'
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

    # TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = PodmanSign.step_implementer_config_defaults()
        expected_defaults = {}
        self.assertEqual(defaults, expected_defaults)

    def test_required_runtime_step_config_keys(self):
        required_keys = PodmanSign.required_runtime_step_config_keys()
        expected_required_keys = ['container-image-signer-pgp-private-key']
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_runtime_step_config_valid(self):
        step_config = {
            'container-image-signer-pgp-private-key': 'test'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='sign-container-image',
            implementer='PodmanSign'
        )

        step_implementer._validate_runtime_step_config(step_config)

    def test__validate_runtime_step_config_invalid(self):
        step_config = {
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='sign-container-image',
            implementer='PodmanSign'
        )
        with self.assertRaisesRegex(
                AssertionError,
                r"The runtime step configuration \({}\) is missing "
                r"the required configuration keys "
                r"\(\['container-image-signer-pgp-private-key'\]\)"
        ):
            step_implementer._validate_runtime_step_config(step_config)

    @patch.object(PodmanSign, '_PodmanSign__import_pgp_key')
    @patch.object(PodmanSign, '_PodmanSign__sign_image')
    def test_run_step_pass(self, sign_image_mock, import_pgp_key_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = {
            }
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

            # # Expected results
            expected_step_result = StepResult(step_name='sign-container-image', sub_step_name='PodmanSign',
                                              sub_step_implementer_name='PodmanSign')
            expected_step_result.add_artifact(name='container-image-signature-file-path',
                                              value= os.path.join(
                                                  work_dir_path,
                                                  'sign-container-image/image-signature',
                                                  signature_name)
                                              )
            expected_step_result.add_artifact(name='container-image-signature-name',
                                              value=signature_name)
            expected_step_result.add_artifact(name='container-image-signature-private-key-fingerprint',
                                              value=pgp_private_key_fingerprint)
            self.assertEqual(expected_step_result.get_step_result(), result.get_step_result())

    @patch.object(PodmanSign, '_PodmanSign__import_pgp_key')
    @patch.object(PodmanSign, '_PodmanSign__sign_image')
    def test_run_step_fail_missing_container_image_tag(self, sign_image_mock, import_pgp_key_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = {
            }
            container_image_tag = 'does/not/matter:v0.42.0'
            signature_name = 'does/not/matter/signature-0'

            # Previous (fake) results
            artifact_config = {
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

            # # Expected results
            expected_step_result = StepResult(step_name='sign-container-image', sub_step_name='PodmanSign',
                                              sub_step_implementer_name='PodmanSign')
            expected_step_result.success = False
            expected_step_result.message = 'Missing container-image-tag'
            self.assertEqual(expected_step_result.get_step_result(), result.get_step_result())

    @patch('sh.podman', create=True)
    def test___sign_image(self, podman_mock):
        with TempDirectory() as temp_dir:
            pgp_private_key_fingerprint = 'abc123'
            image_signatures_directory = os.path.join(temp_dir.path, 'signatures')
            container_image_tag = 'does/not/matter:v0.42.0'

            podman_mock.image.side_effect = TestStepImplementerPodmanSignSourceBase.\
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
    @patch('sh.gpg', create=True)
    def test_push_container_signature_specify_podman_implementer_success(
            self,
            gpg_mock,
            podman_mock
    ):
        """Test for signature signing success"""
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = TestStepImplementerPodmanSignSourceBase.generate_config()
            key = step_config['container-image-signer-pgp-private-key']
            container_image_tag = 'tssc:hello-node:latest'

            signature_dir = os.path.join(
                temp_dir.path,
                'working',
                'sign-container-image',
                'image-signature',
                'hello-node'
            )
            signature_file = os.path.join(signature_dir, 'signature-1')
            temp_dir.makedir(signature_dir)
            temp_dir.write(signature_file, b'signature')
            gpg_mock.side_effect = TestStepImplementerPodmanSignSourceBase.gpg_side_effect
            fingerprint = 'DD7208BA0A6359F65B906B29CF4AC14A3D109637'

            # Previous (fake) results
            artifact_config = {
                'container-image-tag': {'value': container_image_tag}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

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

            # # Expected results
            expected_step_result = StepResult(step_name='sign-container-image', sub_step_name='PodmanSign',
                                              sub_step_implementer_name='PodmanSign')
            expected_step_result.add_artifact(
                name='container-image-signature-file-path',
                value=signature_file
            )
            expected_step_result.add_artifact(
                name='container-image-signature-name',
                value='hello-node/signature-1'
            )
            expected_step_result.add_artifact(
                name='container-image-signature-private-key-fingerprint',
                value=fingerprint
            )

            self.assertEqual(expected_step_result.get_step_result(), result.get_step_result())

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
                f'docker://{container_image_tag}',
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )

    @patch('sh.gpg', create=True)
    def test_push_container_signature_specify_podman_implementer_pgp_no_fingerprint(self, gpg_mock):
        """Test for pgp key missing fingerprint"""
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = TestStepImplementerPodmanSignSourceBase.generate_config()
            container_image_tag = 'tssc:hello-node:latest'
            gpg_mock.return_value = ''
            artifact_config = {
                'container-image-tag': {'value': container_image_tag}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            with self.assertRaisesRegex(
                    RuntimeError,
                    r'Unexpected error getting PGP fingerprint for PGP key to sign .*'
            ):
                step_implementer = self.create_step_implementer(
                    step_config=step_config,
                    step_name='sign-container-image',
                    implementer='PodmanSign',
                    results_dir_path=results_dir_path,
                    results_file_name=results_file_name,
                    work_dir_path=work_dir_path,
                )
                result = step_implementer._run_step()
