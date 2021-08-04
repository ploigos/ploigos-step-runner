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
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app'
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
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app',
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
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app'
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
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app',
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

@patch('ploigos_step_runner.step_implementers.create_container_image.buildah.determine_container_image_build_tag_info')
@patch('sh.buildah', create=True)
class TestStepImplementerCreateContainerImageBuildah___run_step(
    BaseTestStepImplementerCreateContainerImageBuildah
):
    def test_pass(
        self,
        buildah_mock,
        mock_determine_container_image_build_tag_info
    ):
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
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            # set up mocks
            mock_determine_container_image_build_tag_info.return_value=[
                'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                'mock-org/mock-app-mock-service:1.0-123abc',
                'localhost',
                'mock-app-mock-service',
                '1.0-123abc'
            ]

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
                value='mock-org',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='mock-app-mock-service',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='mock-app-mock-service',
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
                value='localhost/mock-org/mock-app-mock-service:1.0-123abc',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='mock-org/mock-app-mock-service:1.0-123abc',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )
            self.assertEqual(result, expected_step_result)

            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    def test_pass_custom_auth_file(self, buildah_mock, mock_determine_container_image_build_tag_info):
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
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app',
                'containers-config-auth-file': 'mock-auth.json'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            # set up mocks
            mock_determine_container_image_build_tag_info.return_value=[
                'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                'mock-org/mock-app-mock-service:1.0-123abc',
                'localhost',
                'mock-app-mock-service',
                '1.0-123abc'
            ]

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
                value='mock-org',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='mock-app-mock-service',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='mock-app-mock-service',
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
                value='localhost/mock-org/mock-app-mock-service:1.0-123abc',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='mock-org/mock-app-mock-service:1.0-123abc',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )
            self.assertEqual(result, expected_step_result)

            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                '--authfile', 'mock-auth.json',
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    def test_pass_string_tls_verify(self, buildah_mock, mock_determine_container_image_build_tag_info):
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
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            # setup sideeffects
            mock_determine_container_image_build_tag_info.return_value=[
                'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                'mock-org/mock-app-mock-service:1.0-123abc',
                'localhost',
                'mock-app-mock-service',
                '1.0-123abc'
            ]

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
                value='mock-org',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='mock-app-mock-service',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='mock-app-mock-service',
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
                value='localhost/mock-org/mock-app-mock-service:1.0-123abc',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='mock-org/mock-app-mock-service:1.0-123abc',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )
            self.assertEqual(result, expected_step_result)

            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    def test_pass_no_container_image_version(self, buildah_mock, mock_determine_container_image_build_tag_info):
        with TempDirectory() as temp_dir:
            # setup test
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('Containerfile',b'''testing''')
            step_config = {
                'imagespecfile': 'Containerfile',
                'context': temp_dir.path,
                'tls-verify': True,
                'format': 'oci',
                'organization': 'mock-org',
                'service-name': 'mock-service',
                'application-name': 'mock-app'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            mock_determine_container_image_build_tag_info.return_value=[
                'localhost/mock-org/mock-app-mock-service:mock-default-version',
                'mock-org/mock-app-mock-service:mock-default-version',
                'localhost',
                'mock-app-mock-service',
                'mock-default-version'
            ]

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
                value='mock-org',
                description='Organization portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='mock-app-mock-service',
                description='Repository portion of the container image tag' \
                    ' of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='mock-app-mock-service',
                description='Another way to reference the' \
                    ' repository portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value='mock-default-version',
                description='Version portion of the container image tag of the built container image.'
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='localhost/mock-org/mock-app-mock-service:mock-default-version',
                description='Full container image tag of the built container,' \
                    ' including the registry URI.'
            )
            expected_step_result.add_artifact(
                name='container-image-short-tag',
                value='mock-org/mock-app-mock-service:mock-default-version',
                description='Short container image tag of the built container image,' \
                    ' excluding the registry URI.'
            )
            self.assertEqual(result, expected_step_result)

            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/mock-org/mock-app-mock-service:mock-default-version',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    def test_fail_buildah_bud_error(self, buildah_mock, mock_determine_container_image_build_tag_info):
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
                'service-name': 'mock-service',
                'application-name': 'mock-app'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='create-container-image',
                implementer='Buildah',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            # setup sideeffects
            mock_determine_container_image_build_tag_info.return_value=[
                'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                'mock-org/mock-app-mock-service:1.0-123abc',
                'localhost',
                'mock-app-mock-service',
                '1.0-123abc'
            ]

            # run step with mock failure
            buildah_mock.bud.side_effect = sh.ErrorReturnCode('buildah', b'mock out', b'mock error')
            result = step_implementer._run_step()

             # verify step result
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
