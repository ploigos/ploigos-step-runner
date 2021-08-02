import os
import re
import sys
from pathlib import Path
from unittest.mock import patch

import sh
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.create_container_image import \
    Buildah
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class BaseTestStepImplementerCreateContainerImageBuildah(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Buildah,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

@patch("ploigos_step_runner.StepImplementer._validate_required_config_or_previous_step_result_artifact_keys")
class TestStepImplementerCreateContainerImageBuildah__validate_required_config_or_previous_step_result_artifact_keys(
    BaseTestStepImplementerCreateContainerImageBuildah
):
    def test_valid_defaults(self, mock_super_validate):
        with TempDirectory() as test_dir:
            # setup
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'context': test_dir.path,
                'organization': 'org-name',
                'service-name': 'service-name',
                'application-name': 'app-name'
            }
            test_dir.write('Containerfile',b'''testing''')

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once_with()

    def test_valid_custom_imagespecfile(self, mock_super_validate):
        with TempDirectory() as test_dir:
            # setup
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'context': test_dir.path,
                'organization': 'org-name',
                'service-name': 'service-name',
                'application-name': 'app-name',
                'imagespecfile': 'MockContainerfile.ubi8'
            }
            test_dir.write('MockContainerfile.ubi8',b'''testing''')

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once_with()

    def test_fail_missing_imagespecfile_defaults(self, mock_super_validate):
        with TempDirectory() as test_dir:
            # setup
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'context': test_dir.path,
                'organization': 'org-name',
                'service-name': 'service-name',
                'application-name': 'app-name'
            }

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )
            with self.assertRaisesRegex(
                AssertionError,
                rf'Given imagespecfile \(Containerfile\) does not exist'
                rf' in given context \({test_dir.path}\).'
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once_with()

    def test_fail_missing_imagespecfile_custom_imagespecfile(self, mock_super_validate):
        with TempDirectory() as test_dir:
            # setup
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'context': test_dir.path,
                'organization': 'org-name',
                'service-name': 'service-name',
                'application-name': 'app-name',
                'imagespecfile': 'MockContainerfile.ubi8'
            }

            # run test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )
            with self.assertRaisesRegex(
                AssertionError,
                rf'Given imagespecfile \(MockContainerfile.ubi8\) does not exist'
                rf' in given context \({test_dir.path}\).'
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once_with()

class TestStepImplementerCreateContainerImageBuildah_step_implementer_config_defaults(
    BaseTestStepImplementerCreateContainerImageBuildah
):
    def test_result(self):
        defaults = Buildah.step_implementer_config_defaults()
        expected_defaults = {
            'imagespecfile': 'Containerfile',
            'context': '.',
            'tls-verify': True,
            'format': 'oci'
        }
        self.assertEqual(defaults, expected_defaults)

class TestStepImplementerCreateContainerImageBuildah___required_config_or_result_keys(
    BaseTestStepImplementerCreateContainerImageBuildah
):
    def test_result(self):
        required_keys = Buildah._required_config_or_result_keys()
        expected_required_keys = [
            'imagespecfile',
            'context',
            'tls-verify',
            'format',
            'organization',
            'service-name',
            'application-name'
        ]
        self.assertEqual(required_keys, expected_required_keys)

class TestStepImplementerCreateContainerImageBuildah___run_step(
    BaseTestStepImplementerCreateContainerImageBuildah
):
    @patch('sh.buildah', create=True)
    def test_pass(self, buildah_mock):
        with TempDirectory() as temp_dir:
            # setup test
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Containerfile',b'''testing''')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-123abc'},
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'imagespecfile': 'Containerfile',
                'context': temp_dir.path,
                'tls-verify': True,
                'format': 'oci',
                'organization': 'org-name',
                'service-name': 'service-name',
                'application-name': 'app-name'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            # run test
            result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='Buildah',
                sub_step_implementer_name='Buildah'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='localhost',
                description='Registry URI poriton of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='org-name',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='app-name-service-name',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='app-name-service-name',
                description='Another way to reference the' \
                    ' repository portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='1.0-123abc',
                description='Version portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='localhost/org-name/app-name-service-name:1.0-123abc',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='org-name/app-name-service-name:1.0-123abc',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )
            self.assertEqual(result, expected_step_result)

            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/org-name/app-name-service-name:1.0-123abc',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    @patch('sh.buildah', create=True)
    def test_pass_custom_auth_file(self, buildah_mock):
        with TempDirectory() as temp_dir:
            # setup test
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Containerfile',b'''testing''')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-123abc'},
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'imagespecfile': 'Containerfile',
                'context': temp_dir.path,
                'tls-verify': True,
                'format': 'oci',
                'organization': 'org-name',
                'service-name': 'service-name',
                'application-name': 'app-name',
                'containers-config-auth-file': 'mock-auth.json'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            # run test
            result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='Buildah',
                sub_step_implementer_name='Buildah'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='localhost',
                description='Registry URI poriton of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='org-name',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='app-name-service-name',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='app-name-service-name',
                description='Another way to reference the' \
                    ' repository portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='1.0-123abc',
                description='Version portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='localhost/org-name/app-name-service-name:1.0-123abc',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='org-name/app-name-service-name:1.0-123abc',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )
            self.assertEqual(result, expected_step_result)

            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/org-name/app-name-service-name:1.0-123abc',
                '--authfile', 'mock-auth.json',
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    @patch('sh.buildah', create=True)
    def test_pass_string_tls_verify(self, buildah_mock):
        with TempDirectory() as temp_dir:
            # setup test
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Containerfile',b'''testing''')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-123abc'},
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'imagespecfile': 'Containerfile',
                'context': temp_dir.path,
                'tls-verify': 'true',
                'format': 'oci',
                'organization': 'org-name',
                'service-name': 'service-name',
                'application-name': 'app-name'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            # run test
            result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='Buildah',
                sub_step_implementer_name='Buildah'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='localhost',
                description='Registry URI poriton of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='org-name',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='app-name-service-name',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='app-name-service-name',
                description='Another way to reference the' \
                    ' repository portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='1.0-123abc',
                description='Version portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='localhost/org-name/app-name-service-name:1.0-123abc',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='org-name/app-name-service-name:1.0-123abc',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )
            self.assertEqual(result, expected_step_result)

            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/org-name/app-name-service-name:1.0-123abc',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    @patch('sh.buildah', create=True)
    def test_pass_no_container_image_version(self, buildah_mock):
        with TempDirectory() as temp_dir:
            # setup test
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Containerfile',b'''testing''')
            step_config = {
                'imagespecfile': 'Containerfile',
                'context': temp_dir.path,
                'tls-verify': True,
                'format': 'oci',
                'organization': 'org-name',
                'service-name': 'service-name',
                'application-name': 'app-name'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='create-container-image',
                sub_step_name='Buildah',
                sub_step_implementer_name='Buildah'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='localhost',
                description='Registry URI poriton of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='org-name',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='app-name-service-name',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='app-name-service-name',
                description='Another way to reference the' \
                    ' repository portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='latest',
                description='Version portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='localhost/org-name/app-name-service-name:latest',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='org-name/app-name-service-name:latest',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )
            self.assertEqual(result, expected_step_result)

            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/org-name/app-name-service-name:latest',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    @patch('sh.buildah', create=True)
    def test_fail_buildah_bud_error(self, buildah_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Containerfile',b'''testing''')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-123abc'},
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            image_spec_file = 'Containerfile'
            step_config = {
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
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

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
