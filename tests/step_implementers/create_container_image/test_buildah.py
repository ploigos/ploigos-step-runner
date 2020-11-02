import sh
from io import IOBase

import unittest
from unittest.mock import patch
from testfixtures import TempDirectory

from tssc.step_implementers.create_container_image import Buildah

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.test_utils import *

class TestStepImplementerCreateContainerImageBuildah(BaseTSSCTestCase):
    def test_create_container_image_default_missing_imagespecfile(self):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {}
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError,
                    r"Image specification file does not exist in location: ./Dockerfile"):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})

    def test_create_container_image_specify_buildah_implementer_missing_imagespecfile(self):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {}
                    }
                }
            }

            with self.assertRaisesRegex(
                    ValueError,
                    r"Image specification file does not exist in location: ./Dockerfile"):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})

    def test_create_container_image_specify_buildah_implementer_missing_config_tlsverify(self):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tls-verify' : None,
                        }
                    }
                }
            }

            with self.assertRaisesRegex(
                    AssertionError,
                    r"The runtime step configuration \(.*\) is missing the required configuration keys \(\['tls-verify'\]\)"):
                run_step_test_with_result_validation(temp_dir, 'create-container-image', config, {})

    def test_create_container_image_specify_buildah_implementer_no_dockerfile(self):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
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
    def test_create_container_image_specify_buildah_implementer_with_invalid_dockerfile(self, buildah_mock):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            temp_dir.write('Dockerfile',b'Invalid Dockerfile')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
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
    def test_create_container_image_specify_buildah_implementer_with_valid_dockerfile(self, buildah_mock):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            version = 'latest'
            tag = 'localhost/{application_name}/{service_name}:{version}'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )
            image_tar_file = 'image-{application_name}-{service_name}-{version}.tar'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'context' : temp_dir.path
                        }
                    }
                }
            }

            expected_step_results = {'tssc-results': {
                'create-container-image': {
                    'container-image-version': tag,
                    'image-tar-file': image_tar_file
                }
            }}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--storage-driver=vfs',
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', tag,
                '--authfile', StringRegexParam(r".*/\.buildah-auth.json"),
                temp_dir.path,
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
            buildah_mock.push.assert_called()

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_valid_dockerfile_metadata_version(self, buildah_mock):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            version = '1.0-69442c8'
            tag = 'localhost/{application_name}/{service_name}:{version}'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )
            image_tar_file = 'image-{application_name}-{service_name}-{version}.tar'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            temp_dir.makedir('tssc-results')
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    version: {version}
                    container-image-version: {version}
                '''.format(version=version),
                    'utf-8')
                )
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'context' : temp_dir.path
                        }
                    },
                     'generate-metadata': {
                        'implementer': 'Maven',
                        'config' : {}
                    }
                }
            }

            expected_step_results = {'tssc-results': {
                'generate-metadata': {
                    'container-image-version': version,
                    'version': version
                },
                'create-container-image': {
                    'container-image-version': tag,
                    'image-tar-file': image_tar_file
                }
            }}
            run_step_test_with_result_validation(
                temp_dir,
                'create-container-image',
                config,
                expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--storage-driver=vfs',
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', '{tag}'.format(tag=tag),
                '--authfile', StringRegexParam(r".*/\.buildah-auth.json"),
                temp_dir.path,
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
            buildah_mock.push.assert_called()

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_valid_dockerfile_as_tarfile_success(self, buildah_mock):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            version = 'latest'
            tag = 'localhost/{application_name}/{service_name}:{version}'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )
            image_tar_file = 'image-{application_name}-{service_name}-{version}.tar'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )

            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'context' : temp_dir.path
                        }
                    }
                }
            }

            expected_step_results = {'tssc-results': {
                'create-container-image': {
                    'container-image-version': tag,
                    'image-tar-file' : image_tar_file
                }
            }}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--storage-driver=vfs',
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', tag,
                '--authfile', StringRegexParam(r".*/\.buildah-auth.json"),
                temp_dir.path,
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
            buildah_mock.push.assert_called_once_with(
                '--storage-driver=vfs',
                tag,
                'docker-archive:{image_tar_file}'.format(image_tar_file=image_tar_file),
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_destination_valid_dockerfile_as_tarfile_fail(self, buildah_mock):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            version = 'latest'
            image_tar_file = 'image-{application_name}-{service_name}-{version}.tar'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'context' : temp_dir.path
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
    def test_create_container_image_specify_buildah_implementer_with_destination_valid_dockerfile_as_tarfile_and_existing_tarfile_success(self, buildah_mock):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            version = 'latest'
            tag = 'localhost/{application_name}/{service_name}:{version}'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )
            image_tar_file = 'image-{application_name}-{service_name}-{version}.tar'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )

            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'context' : temp_dir.path
                        }
                    }
                }
            }

            f = open(image_tar_file, 'w')
            f.write('If you wish to make an apple pie from scratch, you must first invent the universe.')
            f.close()

            expected_step_results = {'tssc-results': {
                'create-container-image': {
                    'container-image-version': tag,
                    'image-tar-file' : image_tar_file
                }
            }}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--storage-driver=vfs',
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', tag,
                '--authfile', StringRegexParam(r".*/\.buildah-auth.json"),
                temp_dir.path,
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
            buildah_mock.push.assert_called_once_with(
                '--storage-driver=vfs',
                tag,
                'docker-archive:{image_tar_file}'.format(image_tar_file=image_tar_file),
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

    @patch('sh.buildah', create=True)
    def test_create_container_image_specify_buildah_implementer_with_destination_valid_dockerfile_metadata_version_and_global_application_name_and_service_name(self, buildah_mock):
        with TempDirectory() as temp_dir:
            application_name = 'foo'
            service_name = 'bar'
            version = '1.0-69442c8'
            tag = 'localhost/{application_name}/{service_name}:{version}'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )
            image_tar_file = 'image-{application_name}-{service_name}-{version}.tar'.format(
                application_name=application_name,
                service_name=service_name,
                version=version
            )
            file = 'Dockerfile'
            temp_dir.write(file,b'FROM registry.access.redhat.com/ubi8:latest')
            temp_dir.makedir('tssc-results')
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                          generate-metadata:
                            version: {version}
                            container-image-version: {version}
                        '''.format(version=version),
                            'utf-8')
                )
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': application_name,
                        'service-name': service_name
                    },
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'context' : temp_dir.path
                        }
                    },
                     'generate-metadata': {
                        'implementer': 'Maven',
                        'config' : {}
                    }
                }
            }

            expected_step_results = {'tssc-results': {
                'generate-metadata': {
                    'container-image-version': version,
                    'version': version
                },
                'create-container-image': {
                    'container-image-version': tag,
                    'image-tar-file' : image_tar_file
                }
            }}
            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
            buildah_mock.bud.assert_called_once_with(
                '--storage-driver=vfs',
                '--format=oci',
                '--tls-verify=true',
                '--layers',
                '-f', file,
                '-t', tag,
                '--authfile', StringRegexParam(r".*/\.buildah-auth.json"),
                temp_dir.path,
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
            buildah_mock.push.assert_called()
