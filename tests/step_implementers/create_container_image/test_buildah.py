import os
import sh
import sys

import unittest
from unittest.mock import patch
from testfixtures import TempDirectory

from tssc.step_implementers.create_container_image import Buildah

from test_utils import *

class TestStepImplementerCreateContaienrImageBuildah(unittest.TestCase):
    def test_create_container_image_default(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {}
            }
            
            with self.assertRaisesRegex(
                    ValueError,
                    r'Key \(tag\) must have non-empty value in the step configuration'):
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
                    r'Key \(tag\) must have non-empty value in the step configuration'):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})
    
    def test_create_container_image_specify_buildah_implementer_missing_config(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tag' : 'localhost:test',
                            'tlsverify' : None,
                        }
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError,
                    r'Key \(tlsverify\) must have non-empty value in the step configuration'):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})
    
    def test_create_container_image_specify_buildah_implementer_with_tag_no_dockerfile(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tag' : 'localhost:test',
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
    def test_create_container_image_specify_buildah_implementer_with_tag_invalid_dockerfile(self, buildah_mock):
        with TempDirectory() as temp_dir:
            temp_dir.write('Dockerfile',b'Invalid Dockerfile')
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tag' : 'localhost:test',
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
    def test_create_container_image_specify_buildah_implementer_with_tag_valid_dockerfile(self, buildah_mock):
        with TempDirectory() as temp_dir:
            tag = 'localhost:test'
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tag' : tag,
                            'context' : temp_dir.path
                        }
                    }
                }
            }
            expected_step_results = {'tssc-results': {'create-container-image': {'image_tag': 'localhost:test'}}}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', tag,
                temp_dir.path,
                _out=sys.stdout
            )
            buildah_mock.push.assert_not_called()
    
    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_tag_valid_dockerfile_as_tarfile_fail(self, buildah_mock):
        with TempDirectory() as temp_dir:
            image_tar_file = '/nonexistentpath/image.tar'
            temp_dir.write('Dockerfile',b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tag' : 'localhost:test',
                            'context' : temp_dir.path,
                            'image_tar_file' : image_tar_file
                        }
                    }
                }
            }
            
            sh.buildah.push.side_effect = sh.ErrorReturnCode('buildah bud', b'mock stdout', b'mock error about invalid image tar file')
            with self.assertRaisesRegex(
                    RuntimeError,
                    r'Issue invoking buildah push to tar file {image_tar_file}'.format(image_tar_file=image_tar_file)):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})
    
    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_tag_valid_dockerfile_as_tarfile_success(self, buildah_mock):
        with TempDirectory() as temp_dir:
            tag = 'localhost:test'
            file = 'Dockerfile'
            image_tar_file = temp_dir.path + '/image.tar'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tag' : tag,
                            'context' : temp_dir.path,
                            'image_tar_file' : image_tar_file
                        }
                    }
                }
            }
            expected_step_results = {'tssc-results': {'create-container-image': {'image_tag': 'localhost:test', 'image_tar_file' : temp_dir.path + '/image.tar'}}}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', tag,
                temp_dir.path,
                _out=sys.stdout
            )
            buildah_mock.push.assert_called_once_with(
                tag,
                'docker-archive:{image_tar_file}'.format(image_tar_file=image_tar_file),
                _out=sys.stdout
            )
