import os
import sh
import sys
import uuid

import unittest
from unittest.mock import patch
from testfixtures import TempDirectory

from tssc.step_implementers.create_container_image import Buildah

from test_utils import *

class TestStepImplementerCreateContainerImageBuildah(unittest.TestCase):
    def test_create_container_image_default(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {}
            }

            with self.assertRaisesRegex(
                    ValueError,
                    r'Key \(destination\) must have non-empty value in the step configuration'):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})

    def test_create_container_image_specify_buildah_implementer(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {}
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError,
                    r'Key \(destination\) must have non-empty value in the step configuration'):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})

    def test_create_container_image_specify_buildah_implementer_missing_config(self):
        with TempDirectory() as temp_dir:
            destination = 'localhost'
            config = {
                'tssc-config': {
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'destination' : destination,
                            'tlsverify' : None,
                        }
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError,
                    r'Key \(tlsverify\) must have non-empty value in the step configuration'):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})

    def test_create_container_image_specify_buildah_implementer_with_destination_no_dockerfile(self):
        with TempDirectory() as temp_dir:
            destination = 'localhost'
            config = {
                'tssc-config': {
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'destination' : destination,
                            'context' : temp_dir.path
                        }
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError,
                    'Image specification file does not exist in location'):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_destination_invalid_dockerfile(self, buildah_mock):
        with TempDirectory() as temp_dir:
            temp_dir.write('Dockerfile',b'Invalid Dockerfile')
            destination = 'localhost'
            config = {
                'tssc-config': {
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'destination' : destination,
                            'context' : temp_dir.path
                        }
                    }
                }
            }

            sh.buildah.bud.side_effect = sh.ErrorReturnCode('buildah bud', b'mock stdout', b'mock error about invalid dockerfile')
            with self.assertRaisesRegex(
                    RuntimeError,
                    r'Issue invoking buildah bud with given image specification file \(Dockerfile\)'):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_destination_valid_dockerfile(self, buildah_mock):
        with TempDirectory() as temp_dir:
            destination = 'localhost'
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'destination' : destination,
                            'context' : temp_dir.path
                        }
                    }
                }
            }

            image_tar_file = 'image-latest.tar'
            expected_step_results = {'tssc-results': {'create-container-image': {'image-tag': destination + ':latest', 'image-tar-file': image_tar_file}}}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', destination + ':latest',
                temp_dir.path,
                _out=sys.stdout
            )
            buildah_mock.push.assert_called()

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_destination_valid_dockerfile_metadata_version(self, buildah_mock):
        with TempDirectory() as temp_dir:
            destination = 'localhost'
            version = '1.0-69442c8'
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            temp_dir.makedir('tssc-results')
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    version: {version}
                    image-tag: {version}
                '''.format(version=version),
                    'utf-8')
                )
            config = {
                'tssc-config': {
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'destination' : destination,
                            'context' : temp_dir.path
                        }
                    },
                     'generate-metadata': {
                        'implementer': 'Maven',
                        'config' : {}
                    }
                }
            }

            expected_step_results = {'tssc-results': {'generate-metadata': \
                {'image-tag': version, 'version': '{version}'.format(version=version)},\
                'create-container-image': {'image-tag': '{destination}:{version}'\
                .format(destination=destination,version=version),\
                'image-tar-file' : 'image-{version}.tar'.format(version=version)
                }}}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', '{destination}:{version}'.format(destination=destination, version=version),
                temp_dir.path,
                _out=sys.stdout
            )
            buildah_mock.push.assert_called()

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_destination_valid_dockerfile_as_tarfile_success(self, buildah_mock):
        with TempDirectory() as temp_dir:
            destination = 'localhost'
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'destination' : destination,
                            'context' : temp_dir.path
                        }
                    }
                }
            }

            image_tar_file = 'image-latest.tar'

            expected_step_results = {'tssc-results': {'create-container-image': {'image-tag': destination + ':latest', 'image-tar-file' : image_tar_file}}}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', destination + ':latest',
                temp_dir.path,
                _out=sys.stdout
            )
            buildah_mock.push.assert_called_once_with(
                destination + ':latest',
                'docker-archive:{image_tar_file}'.format(image_tar_file=image_tar_file),
                _out=sys.stdout
            )

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_destination_valid_dockerfile_as_tarfile_fail(self, buildah_mock):
        with TempDirectory() as temp_dir:
            destination = 'localhost'
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'destination' : destination,
                            'context' : temp_dir.path
                        }
                    }
                }
            }
            image_tar_file = 'image-latest.tar'
            sh.buildah.push.side_effect = sh.ErrorReturnCode('buildah bud', b'mock stdout', b'mock error about invalid image tar file')
            with self.assertRaisesRegex(
                  RuntimeError,
                  r'Issue invoking buildah push to tar file {image_tar_file}'.format(image_tar_file=image_tar_file)):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_destination_valid_dockerfile_as_tarfile_and_existing_tarfile_success(self, buildah_mock):
        with TempDirectory() as temp_dir:
            destination = 'localhost'
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'destination' : destination,
                            'context' : temp_dir.path
                        }
                    }
                }
            }

            image_tar_file = 'image-latest.tar'
            f = open(image_tar_file, 'w')
            f.write('If you wish to make an apple pie from scratch, you must first invent the universe.')
            f.close()

            expected_step_results = {'tssc-results': {'create-container-image': {'image-tag': destination + ':latest', 'image-tar-file' : image_tar_file}}}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', destination + ':latest',
                temp_dir.path,
                _out=sys.stdout
            )
            buildah_mock.push.assert_called_once_with(
                destination + ':latest',
                'docker-archive:{image_tar_file}'.format(image_tar_file=image_tar_file),
                _out=sys.stdout
            )

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_destination_valid_dockerfile_metadata_version_and_global_application_name_and_service_name(self, buildah_mock):
        with TempDirectory() as temp_dir:
            destination = 'localhost'
            version = '1.0-69442c8'
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            temp_dir.makedir('tssc-results')
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                          generate-metadata:
                            version: {version}
                            image-tag: {version}
                        '''.format(version=version),
                            'utf-8')
                )
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'foo',
                        'service-name': 'bar'
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'destination' : destination,
                            'context' : temp_dir.path
                        }
                    },
                     'generate-metadata': {
                        'implementer': 'Maven',
                        'config' : {}
                    }
                }
            }

            expected_step_results = {'tssc-results': {'generate-metadata': \
                {'image-tag': version, 'version': '{version}'.format(version=version)},\
                'create-container-image': {'image-tag': '{destination}:{version}'\
                .format(destination=destination,version=version),\
                'image-tar-file' : 'image-foo-bar-{version}.tar'.format(version=version)
                }}}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', '{destination}:{version}'.format(destination=destination, version=version),
                temp_dir.path,
                _out=sys.stdout
            )
            buildah_mock.push.assert_called()
