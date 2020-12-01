"""Test Curl Push

Tests the push via curl of the container signature to the
signature store.
"""
import os
from io import IOBase
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any, StringRegexParam

class TestStepImplementerSignContainerImageCurlPush(BaseStepImplementerTestCase):
    """Test Step Implementer Sign Container Image using Curl to Push

    Test runner for the CurlPush.
    """

    @staticmethod
    def generate_config():
        """Generate tssc config for tests"""
        return {
            'tssc-config': {
                'sign-container-image': {
                    'implementer': 'CurlPush',
                    'config': {
                        'container-image-signature-server-url': 'https://sigserver/signatures',
                        'container-image-signature-server-username': 'admin',
                        'container-image-signature-server-password': 'adminPassword'
                    }
                }
            }
        }

    def test_push_container_signature_specify_curl_implementer_missing_config_values(self):
        """Test for missing config values"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImageCurlPush.generate_config()
            config['tssc-config']['sign-container-image']['config'] = {}
            expected_step_results = {'tssc-results': {'sign-container-image': {}}}

            with self.assertRaisesRegex(
                AssertionError,
                r"The runtime step configuration \(\{\}\) is missing the required configuration "
                r"keys \(\['container-image-signature-server-url', "
                r"'container-image-signature-server-username', "
                r"'container-image-signature-server-password'\]\)"
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results
                )

    def test_push_container_signature_specify_curl_implementer_missing_config_step_values(self):
        """Test for missing specific result step values"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImageCurlPush.generate_config()
            expected_step_results = {'tssc-results': {'sign-container-image': {}}}

            with self.assertRaisesRegex(
                RuntimeError,
                r'Missing container-image-signature-file-path '
                r'step results from sign-container-image'
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results
                )

    def test_push_container_signature_specify_curl_implementer_missing_config_step(self):
        """Test for missing result step for sign-container-image"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImageCurlPush.generate_config()
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  sign-container-image:
                ''', 'utf-8')
            )
            expected_step_results = {'tssc-results': {}}
            with self.assertRaisesRegex(
                RuntimeError,
                r'Missing step results from sign-container-image'
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results
                )

    @patch('sh.curl', create=True)
    def test_push_container_signature_specify_curl_implementer_success(self, curl_mock):
        """Test for curl success"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImageCurlPush.generate_config()

            signature_file_path = 'signature-1'
            temp_dir.write(signature_file_path, b'bogus signature')
            container_image_signature_file_path = os.path.join(temp_dir.path, signature_file_path)

            container_image_signature_name = 'jkeam/hello-node@sha256=2cbdb73c9177e63e85d267f738e' \
                '99e368db3f806eab4c541f5c6b719e69f1a2b/signature-1'
            temp_dir.makedir('tssc-results')
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    f'''tssc-results:
                  sign-container-image:
                    container-image-signature-file-path: {container_image_signature_file_path}
                    container-image-signature-name: {container_image_signature_name}
                ''', 'utf-8')
            )

            expected_step_results = {
                'tssc-results': {
                    'sign-container-image': {
                        'container-image-signature-file-path': container_image_signature_file_path,
                        'container-image-signature-name': container_image_signature_name,
                        'container-image-signature-url' :
                            f'https://sigserver/signatures/{container_image_signature_name}',
                        'container-image-signature-file-sha1' : StringRegexParam(r'.+'),
                        'container-image-signature-file-md5': StringRegexParam(r'.+')
                    }
                }
            }

            self.run_step_test_with_result_validation(
                temp_dir,
                'sign-container-image',
                config,
                expected_step_results
            )
            curl_mock.assert_called_once_with(
                '-sSfv',
                '-X', 'PUT',
                '--header', StringRegexParam(r'X-Checksum-Sha1:.+'),
                '--header', StringRegexParam(r'X-Checksum-MD5:.+'),
                '--user', "admin:adminPassword",
                '--upload-file', container_image_signature_file_path,
                f"https://sigserver/signatures/{container_image_signature_name}",
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )

    @patch('sh.curl', create=True)
    def test_push_container_signature_specify_curl_implementer_failure(self, curl_mock):
        """Test for curl failure"""
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImageCurlPush.generate_config()

            signature_file_path = 'signature-1'
            temp_dir.write(signature_file_path, b'bogus signature')
            container_image_signature_file_path = os.path.join(temp_dir.path, signature_file_path)

            container_image_signature_name = 'jkeam/hello-node@sha256=2cbdb73c9177e63e85d267f738e' \
                '99e368db3f806eab4c541f5c6b719e69f1a2b/signature-1'
            temp_dir.makedir('tssc-results')
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    f'''tssc-results:
                  sign-container-image:
                    container-image-signature-file-path: {container_image_signature_file_path}
                    container-image-signature-name: {container_image_signature_name}
                ''', 'utf-8')
            )

            curl_mock.side_effect = sh.ErrorReturnCode(
                'CurlPush',
                b'mock stdout',
                b'mock error about curl runtime'
            )
            with self.assertRaisesRegex(
                RuntimeError,
                r'Unexpected error curling signature file to signature server.*'
            ):
                self.run_step_test_with_result_validation(
                    temp_dir,
                    'sign-container-image',
                    config,
                    expected_step_results=None
                )
