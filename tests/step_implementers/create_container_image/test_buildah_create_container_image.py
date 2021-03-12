import os
import re
import sys
from pathlib import Path
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.step_implementers.create_container_image import Buildah
from ploigos_step_runner.step_result import StepResult


class TestStepImplementerCreateContainerImageBuildah(BaseStepImplementerTestCase):
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
            step_implementer=Buildah,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

# TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = Buildah.step_implementer_config_defaults()
        expected_defaults = {
            'containers-config-auth-file': os.path.join(Path.home(), '.buildah-auth.json'),
            'imagespecfile': 'Dockerfile',
            'context': '.',
            'tls-verify': True,
            'format': 'oci'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Buildah._required_config_or_result_keys()
        expected_required_keys = [
            'containers-config-auth-file',
            'imagespecfile',
            'context',
            'tls-verify',
            'format',
            'service-name',
            'application-name'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    @patch('sh.buildah', create=True)
    def test__run_step_pass(self, buildah_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Dockerfile',b'''testing''')

            step_config = {
                'containers-config-auth-file': 'buildah-auth.json',
                'imagespecfile': 'Dockerfile',
                'context': temp_dir.path,
                'tls-verify': True,
                'format': 'oci',
                'service-name': 'service-name',
                'application-name': 'app-name'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='Buildah',
                sub_step_implementer_name='Buildah'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='localhost/app-name/service-name:1.0-123abc'
            )
            expected_step_result.add_artifact(
                name='image-tar-file',
                value=work_dir_path + '/create-container-image/image-app-name-service-name-1.0-123abc.tar'
            )


            buildah_mock.bud.assert_called_once_with(
                '--storage-driver=vfs',
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Dockerfile',
                '-t', 'localhost/app-name/service-name:1.0-123abc',
                '--authfile', 'buildah-auth.json',
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

            buildah_mock.push.assert_called_once_with(
                '--storage-driver=vfs',
                'localhost/app-name/service-name:1.0-123abc',
                'docker-archive:' + work_dir_path + '/create-container-image/image-app-name-service-name-1.0-123abc.tar',
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )
            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch('sh.buildah', create=True)
    def test__run_step_pass_no_container_image_version(self, buildah_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Dockerfile',b'''testing''')

            step_config = {
                'containers-config-auth-file': 'buildah-auth.json',
                'imagespecfile': 'Dockerfile',
                'context': temp_dir.path,
                'tls-verify': True,
                'format': 'oci',
                'service-name': 'service-name',
                'application-name': 'app-name'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='Buildah',
                sub_step_implementer_name='Buildah'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='localhost/app-name/service-name:latest'
            )
            expected_step_result.add_artifact(
                name='image-tar-file',
                value=work_dir_path + '/create-container-image/image-app-name-service-name-latest.tar'
            )

            buildah_mock.bud.assert_called_once_with(
                '--storage-driver=vfs',
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Dockerfile',
                '-t', 'localhost/app-name/service-name:latest',
                '--authfile', 'buildah-auth.json',
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

            buildah_mock.push.assert_called_once_with(
                '--storage-driver=vfs',
                'localhost/app-name/service-name:latest',
                'docker-archive:' + work_dir_path + '/create-container-image/image-app-name-service-name-latest.tar',
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )
            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch('sh.buildah', create=True)
    def test__run_step_pass_image_tar_file_exists(self, buildah_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Dockerfile',b'''testing''')

            step_config = {
                'containers-config-auth-file': 'buildah-auth.json',
                'imagespecfile': 'Dockerfile',
                'context': temp_dir.path,
                'tls-verify': True,
                'format': 'oci',
                'service-name': 'service-name',
                'application-name': 'app-name'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer.write_working_file('image-app-name-service-name-1.0-123abc.tar')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='Buildah',
                sub_step_implementer_name='Buildah'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='localhost/app-name/service-name:1.0-123abc'
            )
            expected_step_result.add_artifact(
                name='image-tar-file',
                value=work_dir_path + '/create-container-image/image-app-name-service-name-1.0-123abc.tar'
            )


            buildah_mock.bud.assert_called_once_with(
                '--storage-driver=vfs',
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Dockerfile',
                '-t', 'localhost/app-name/service-name:1.0-123abc',
                '--authfile', 'buildah-auth.json',
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

            buildah_mock.push.assert_called_once_with(
                '--storage-driver=vfs',
                'localhost/app-name/service-name:1.0-123abc',
                'docker-archive:' + work_dir_path + '/create-container-image/image-app-name-service-name-1.0-123abc.tar',
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )
            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch('sh.buildah', create=True)
    def test__run_step_fail_no_image_spec_file(self, buildah_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'service-name': 'service-name',
                'application-name': 'app-name'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='Buildah',
                sub_step_implementer_name='Buildah'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Image specification file does not exist in location: ./Dockerfile'

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch('sh.buildah', create=True)
    def test__run_step_fail_buildah_bud_error(self, buildah_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Dockerfile',b'''testing''')

            image_spec_file = 'Dockerfile'
            step_config = {
                'containers-config-auth-file': 'buildah-auth.json',
                'imagespecfile': image_spec_file,
                'context': temp_dir.path,
                'tls-verify': True,
                'format': 'oci',
                'service-name': 'service-name',
                'application-name': 'app-name'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            buildah_mock.bud.side_effect = sh.ErrorReturnCode('buildah', b'mock out', b'mock error')

            result = step_implementer._run_step()

            self.assertFalse(result.success)
            self.assertRegex(
                result.message,
                re.compile(
                    r'Issue invoking buildah bud with given image '
                    rf'specification file \({image_spec_file}\):'
                    r'.*RAN: buildah'
                    r'.*STDOUT:'
                    r'.*mock out'
                    r'.*STDERR:'
                    r'.*mock error',
                    re.DOTALL
                )
            )

    @patch('sh.buildah', create=True)
    def test__run_step_fail_buildah_push_error(self, buildah_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Dockerfile',b'''testing''')

            application_name = 'app-name'
            service_name = 'service-name'
            image_tag_version = '1.0-123abc'
            step_config = {
                'containers-config-auth-file': 'buildah-auth.json',
                'imagespecfile': 'Dockerfile',
                'context': temp_dir.path,
                'tl-sverify': 'true',
                'format': 'oci',
                'service-name': service_name,
                'application-name': application_name
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'container-image-version': {'description': '', 'value': image_tag_version},
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            buildah_mock.push.side_effect = sh.ErrorReturnCode('buildah', b'mock out', b'mock error')

            result = step_implementer._run_step()

            image_tar_path = os.path.join(
                work_dir_path,
                'create-container-image',
                f'image-{application_name}-{service_name}-{image_tag_version}.tar'
            )
            self.assertFalse(result.success)
            self.assertRegex(
                result.message,
                re.compile(
                    rf'Issue invoking buildah push to tar file \({image_tar_path}\):'
                    r'.*RAN: buildah'
                    r'.*STDOUT:'
                    r'.*mock out'
                    r'.*STDERR:'
                    r'.*mock error',
                    re.DOTALL
                )
            )
