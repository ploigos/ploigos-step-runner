# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
from io import IOBase
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any, StringRegexParam
from ploigos_step_runner.step_implementers.sign_container_image import CurlPush
from ploigos_step_runner.step_result import StepResult


class TestStepImplementerCurlPushSourceBase(BaseStepImplementerTestCase):
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
            step_implementer=CurlPush,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    # TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = CurlPush.step_implementer_config_defaults()
        expected_defaults = {'with-fips': True}
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = CurlPush._required_config_or_result_keys()
        expected_required_keys = [
            'container-image-signature-server-url',
            'container-image-signature-server-username',
            'container-image-signature-server-password',
            'container-image-signature-file-path',
            'container-image-signature-name'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    @patch('sh.curl', create=True)
    def test_run_step_pass(self, curl_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            signature_file_path = 'signature-1'
            temp_dir.write(signature_file_path, b'bogus signature')
            container_image_signature_file_path = os.path.join(temp_dir.path, signature_file_path)

            container_image_signature_name = 'jkeam/hello-node@sha256=2cbdb73c9177e63e85d267f738e' \
                '99e368db3f806eab4c541f5c6b719e69f1a2b/signature-1'

            step_config = {
                'container-image-signature-server-url': 'https://sigserver/signatures',
                'container-image-signature-server-username': 'admin',
                'container-image-signature-server-password': 'adminPassword',
                'with-fips': True
            }

            # Previous (fake) results
            artifact_config = {
                'container-image-signature-file-path': {'value': container_image_signature_file_path},
                'container-image-signature-name': {'value': container_image_signature_name},
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='CurlPush',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            # Expected results
            expected_step_result = StepResult(step_name='sign-container-image', sub_step_name='CurlPush',
                                              sub_step_implementer_name='CurlPush')
            expected_step_result.add_artifact(name='container-image-signature-url', value=f'https://sigserver/signatures/{container_image_signature_name}')

            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())
            curl_mock.assert_called_once_with(
                '-sSfv',
                '-X', 'PUT',
                '--user', "admin:adminPassword",
                '--upload-file', container_image_signature_file_path,
                f"https://sigserver/signatures/{container_image_signature_name}",
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )

    @patch('sh.curl', create=True)
    def test_run_step_pass_nofips(self, curl_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            signature_file_path = 'signature-1'
            temp_dir.write(signature_file_path, b'bogus signature')
            container_image_signature_file_path = os.path.join(temp_dir.path, signature_file_path)

            container_image_signature_name = 'jkeam/hello-node@sha256=2cbdb73c9177e63e85d267f738e' \
                '99e368db3f806eab4c541f5c6b719e69f1a2b/signature-1'

            step_config = {
                'container-image-signature-server-url': 'https://sigserver/signatures',
                'container-image-signature-server-username': 'admin',
                'container-image-signature-server-password': 'adminPassword',
                'with-fips': False
            }

            # Previous (fake) results
            artifact_config = {
                'container-image-signature-file-path': {'value': container_image_signature_file_path},
                'container-image-signature-name': {'value': container_image_signature_name},
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='CurlPush',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            # # Expected results
            expected_step_result = StepResult(step_name='sign-container-image', sub_step_name='CurlPush',
                                              sub_step_implementer_name='CurlPush')
            expected_step_result.add_artifact(name='container-image-signature-url', value=f'https://sigserver/signatures/{container_image_signature_name}')
            expected_step_result.add_artifact(name='container-image-signature-file-sha1', value='d9ba1fc747829392883c48adfe4bb688239dc8b2')
            expected_step_result.add_artifact(name='container-image-signature-file-md5', value='b66c5c3d4ab37a50e69a05d72ba302fa')

            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())
            curl_mock.assert_called_once_with(
                '-sSfv',
                '-X', 'PUT',
                '--user', "admin:adminPassword",
                '--upload-file', container_image_signature_file_path,
                '--header', StringRegexParam(r'X-Checksum-Sha1:.+'),
                '--header', StringRegexParam(r'X-Checksum-MD5:.+'),
                f"https://sigserver/signatures/{container_image_signature_name}",
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )

    @patch('sh.curl', create=True)
    def test_run_step_fail(self, curl_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            signature_file_path = 'signature-1'
            temp_dir.write(signature_file_path, b'bogus signature')
            container_image_signature_file_path = os.path.join(temp_dir.path, signature_file_path)

            container_image_signature_name = 'jkeam/hello-node@sha256=2cbdb73c9177e63e85d267f738e' \
                '99e368db3f806eab4c541f5c6b719e69f1a2b/signature-1'

            step_config = {
                'container-image-signature-server-url': 'https://sigserver/signatures',
                'container-image-signature-server-username': 'admin',
                'container-image-signature-server-password': 'adminPassword'
            }

            # Previous (fake) results
            artifact_config = {
                'container-image-signature-file-path': {'value': container_image_signature_file_path},
                'container-image-signature-name': {'value': container_image_signature_name},
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='CurlPush',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            sh.curl.side_effect = sh.ErrorReturnCode('curl', b'mock stdout', b'mock error')

            result = step_implementer._run_step()

            # # Expected results
            expected_step_result = StepResult(
                step_name='sign-container-image',
                sub_step_name='CurlPush',
                sub_step_implementer_name='CurlPush'
            )
            expected_step_result.success = False
            expected_step_result.message = "foo"

            self.assertEqual(result.success, expected_step_result.success)
            self.assertEqual(result.artifacts, expected_step_result.artifacts)
            self.assertRegex(
                result.message,
                re.compile(
                    r"Error pushing signature file to signature server using curl: "
                    r".*RAN: curl"
                    r".*STDOUT:"
                    r".*mock stdout"
                    r".*STDERR:"
                    r".*mock error",
                    re.DOTALL
                )
            )
            curl_mock.assert_called_once_with(
                '-sSfv',
                '-X', 'PUT',
                '--user', "admin:adminPassword",
                '--upload-file', container_image_signature_file_path,
                f"https://sigserver/signatures/{container_image_signature_name}",
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )
