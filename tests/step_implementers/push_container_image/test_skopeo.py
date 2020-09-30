import sh
from io import IOBase

import unittest
from unittest.mock import patch
from testfixtures import TempDirectory

from tssc.step_implementers.push_container_image import Skopeo
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

from tests.helpers.test_utils import *

class TestStepImplementerPushContainerImageSkopeo(BaseTSSCTestCase):

    def test_push_container_image_specify_skopeo_implementer_missing_args(self):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            organization = 'xyzzy'
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name,
                        'organization': organization
                    },
                    'push-container-image': {
                        'implementer': 'Skopeo',
                        'config': {}
                    }
                }
            }
            expected_step_results = {'tssc-results': {'push-container-image': {'container-image-version': ''}}}

            with self.assertRaisesRegex(
                AssertionError,
                r"The runtime step configuration \(\{'src-tls-verify': 'true', "
                r"'dest-tls-verify': 'true', "
                r"'containers-config-auth-file': '.*/\.skopeo-auth.json', "
                r"'application-name': 'foo', "
                r"'service-name': 'bar', 'organization': 'xyzzy'\}\) "
                r"is missing the required configuration keys \(\['destination-url'\]\)"
            ):
                run_step_test_with_result_validation(temp_dir, 'push-container-image', config, expected_step_results)

    @patch('sh.skopeo', create=True)
    def test_create_container_image_specify_skopeo_implementer_invalid_arguments(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            organization = 'xyzzy'
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name,
                        'organization': organization
                    },
                    'push-container-image': {
                        'implementer': 'Skopeo',
                        'config': {
                            'destination-url' : 'docker-archive:' + temp_dir.path + '/image.tar'
                        }
                    }
                }
            }

            with self.assertRaisesRegex(
                    RuntimeError,
                    r'Missing image tar .*'):
                run_step_test_with_result_validation(temp_dir, 'push-container-image', config, [])

    @patch('sh.skopeo', create=True)
    def test_create_container_image_specify_skopeo_implementer_valid_arguments(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            source = 'quay.io/tssc/tssc-base:latest'
            destination = '{path}//image.tar'.format(path=temp_dir.path)
            version = '1.0-69442c8'
            temp_dir.makedir('tssc-results')
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {version}
                  create-container-image:
                    image-tar-file: {destination}
                '''.format(version=version, destination=destination),
                    'utf-8')
                )
            application_name = 'foo'
            service_name = 'bar'
            organization = 'xyzzy'
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name,
                        'organization': organization
                    },
                    'push-container-image': {
                        'implementer': 'Skopeo',
                        'config': {
                            'destination-url' : destination
                        }
                    }
                }
            }
            expected_step_results = {
                'tssc-results': {
                    'create-container-image': {
                        'image-tar-file': destination
                    },
                    'generate-metadata': {
                        'container-image-version': version
                    },
                    'push-container-image': {
                        'container-image-uri': f"{destination}/xyzzy/foo-bar",
                        "container-image-version": version,
                        'container-image-tag': f"{destination}/xyzzy/foo-bar:1.0-69442c8"
                    }
                }
            }

            run_step_test_with_result_validation(temp_dir, 'push-container-image', config, expected_step_results)
            skopeo_mock.copy.assert_called_once_with(
                '--src-tls-verify=true',
                '--dest-tls-verify=true',
                StringRegexParam(r"--authfile=.*/\.skopeo-auth.json"),
                "docker-archive:{destination}".format(destination=destination),
                "docker://{destination}/{organization}/{application_name}-{service_name}:{version}".format(destination=destination, organization=organization, application_name=application_name, service_name=service_name, version=version),
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

    @patch('sh.skopeo', create=True)
    def test_push_container_image_specify_skopeo_implementer_skopeo_error(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            source = 'quay.io/tssc/tssc-base:latest'
            destination = '{path}/image.tar'.format(path=temp_dir.path)
            version = '1.0-69442c8'
            temp_dir.makedir('tssc-results')
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    container-image-version: {version}
                  create-container-image:
                    image-tar-file: image.tar
                '''.format(version=version),
                    'utf-8')
                )

            application_name = 'foo'
            service_name = 'bar'
            organization = 'xyzzy'
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name,
                        'organization': organization
                    },
                    'push-container-image': {
                        'implementer': 'Skopeo',
                        'config': {
                            'destination-url' : destination
                        }
                    }
                },
                'generate-metadata': {
                        'implementer': 'Maven',
                        'config' : {}
                    }
            }
            expected_step_results = {'tssc-results': {'create-container-image': {'image-tar-file': 'image.tar'},'generate-metadata': {'container-image-version': version},
                                     'push-container-image': {'container-image-version':"docker://{destination}:{version}".format(destination=destination, version=version)}}}

            sh.skopeo.copy.side_effect = sh.ErrorReturnCode('skopeo', b'mock stdout', b'mock error about skopeo runtime')
            with self.assertRaisesRegex(
                    RuntimeError,
                    r'Error invoking .*'):
                    run_step_test_with_result_validation(temp_dir, 'push-container-image', config, expected_step_results)
