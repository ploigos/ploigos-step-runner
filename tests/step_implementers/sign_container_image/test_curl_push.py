from io import IOBase
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.test_utils import (Any, StringRegexParam,
                                      run_step_test_with_result_validation)
from tssc.step_implementers.sign_container_image import CurlPush


class TestStepImplementerSignContainerImageCurlPush(BaseTSSCTestCase):
    @staticmethod
    def generate_config():
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
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImageCurlPush.generate_config()
            config['tssc-config']['sign-container-image']['config'] = {}
            expected_step_results = {'tssc-results': {'sign-container-image': {}}}

            with self.assertRaisesRegex(
                AssertionError,
                r"The runtime step configuration \(\{\}\) is missing the required configuration keys "
                r"\(\['container-image-signature-server-url', 'container-image-signature-server-username', 'container-image-signature-server-password'\]\)"
            ):
                run_step_test_with_result_validation(temp_dir, 'sign-container-image', config, expected_step_results)

    def test_push_container_signature_specify_curl_implementer_missing_config_step_values(self):
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImageCurlPush.generate_config()
            expected_step_results = {'tssc-results': {'sign-container-image': {}}}

            with self.assertRaisesRegex(
                RuntimeError,
                r'Missing container-image-signature-file-path '
                r'step results from sign-container-image'
            ):
                run_step_test_with_result_validation(temp_dir, 'sign-container-image', config, expected_step_results)

    @patch('sh.curl', create=True)
    def test_push_container_signature_specify_curl_implementer_success(self, curl_mock):
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImageCurlPush.generate_config()

            container_image_signature_file_path = '/tmp/jkeam/hello-node@sha256=2cbdb73c9177e63e85d267f738e99e368db3f806eab4c541f5c6b719e69f1a2b/signature-1'
            container_image_signature_name = 'jkeam/hello-node@sha256=2cbdb73c9177e63e85d267f738e99e368db3f806eab4c541f5c6b719e69f1a2b/signature-1'
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
                        'container-image-signature-url' : f'https://sigserver/signatures/{container_image_signature_name}'
                    }
                }
            }

            run_step_test_with_result_validation(temp_dir, 'sign-container-image', config, expected_step_results)
            curl_mock.assert_called_once_with(
                '-sSfv',
                '-X', 'PUT',
                '--user', "admin:adminPassword",
                '--data-binary', f"@{container_image_signature_file_path}",
                f"https://sigserver/signatures/{container_image_signature_name}",
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

    @patch('sh.curl', create=True)
    def test_push_container_signature_specify_curl_implementer_failure(self, curl_mock):
        with TempDirectory() as temp_dir:
            config = TestStepImplementerSignContainerImageCurlPush.generate_config()

            container_image_signature_file_path = '/tmp/jkeam/hello-node@sha256=2cbdb73c9177e63e85d267f738e99e368db3f806eab4c541f5c6b719e69f1a2b/signature-1'
            container_image_signature_name = 'jkeam/hello-node@sha256=2cbdb73c9177e63e85d267f738e99e368db3f806eab4c541f5c6b719e69f1a2b/signature-1'
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
                    },
                    'sign-container-image': {
                        'container-image-signature-name': container_image_signature_name
                    }
                }
            }

            sh.curl.side_effect = sh.ErrorReturnCode('CurlPush', b'mock stdout', b'mock error about curl runtime')
            with self.assertRaisesRegex(
                    RuntimeError,
                    r'Unexpected error curling signature file to signature server.*'):
                    run_step_test_with_result_validation(temp_dir, 'sign-container-image', config, expected_step_results)
