import os
import re
import sys
from pathlib import Path
from unittest.mock import patch

import sh
from ploigos_step_runner.results import StepResult
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

@patch("ploigos_step_runner.step_implementer.StepImplementer._validate_required_config_or_previous_step_result_artifact_keys")
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

@patch('ploigos_step_runner.step_implementers.create_container_image.buildah.add_container_build_step_result_artifacts')
@patch('ploigos_step_runner.step_implementers.create_container_image.buildah.get_container_image_digest')
@patch('ploigos_step_runner.step_implementers.create_container_image.buildah.determine_container_image_address_info')
@patch('sh.buildah', create=True)
class TestStepImplementerCreateContainerImageBuildah___run_step(
    BaseTestStepImplementerCreateContainerImageBuildah
):
    def test_pass(
        self,
        buildah_mock,
        mock_determine_container_image_address_info,
        mock_get_container_image_digest,
        mock_add_container_build_step_result_artifacts
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
            mock_determine_container_image_address_info.return_value=[
                'localhost/mock-org/mock-app/mock-service:1.0-123abc',
                'mock-org/mock-app/mock-service:1.0-123abc',
                'localhost',
                'mock-app/mock-service',
                '1.0-123abc'
            ]
            mock_get_container_image_digest.return_value = 'sha256:mockabc123'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            mock_get_container_image_digest.assert_called_once_with(
                container_image_address='localhost/mock-org/mock-app/mock-service:1.0-123abc'
            )
            mock_add_container_build_step_result_artifacts.assert_called_once_with(
                step_result=actual_step_result,
                contaimer_image_registry='localhost',
                container_image_repository='mock-app/mock-service',
                container_image_tag='1.0-123abc',
                container_image_digest='sha256:mockabc123',
                container_image_build_address='localhost/mock-org/mock-app/mock-service:1.0-123abc',
                container_image_build_short_address='mock-org/mock-app/mock-service:1.0-123abc'
            )
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/mock-org/mock-app/mock-service:1.0-123abc',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    def test_pass_custom_auth_file(
        self,
        buildah_mock,
        mock_determine_container_image_address_info,
        mock_get_container_image_digest,
        mock_add_container_build_step_result_artifacts
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
            mock_determine_container_image_address_info.return_value=[
                'localhost/mock-org/mock-app/mock-service:1.0-123abc',
                'mock-org/mock-app/mock-service:1.0-123abc',
                'localhost',
                'mock-app/mock-service',
                '1.0-123abc'
            ]
            mock_get_container_image_digest.return_value = 'sha256:mockabc123'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            mock_get_container_image_digest.assert_called_once_with(
                container_image_address='localhost/mock-org/mock-app/mock-service:1.0-123abc'
            )
            mock_add_container_build_step_result_artifacts.assert_called_once_with(
                step_result=actual_step_result,
                contaimer_image_registry='localhost',
                container_image_repository='mock-app/mock-service',
                container_image_tag='1.0-123abc',
                container_image_digest='sha256:mockabc123',
                container_image_build_address='localhost/mock-org/mock-app/mock-service:1.0-123abc',
                container_image_build_short_address='mock-org/mock-app/mock-service:1.0-123abc'
            )
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/mock-org/mock-app/mock-service:1.0-123abc',
                '--authfile', 'mock-auth.json',
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    def test_pass_string_tls_verify_true(
        self,
        buildah_mock,
        mock_determine_container_image_address_info,
        mock_get_container_image_digest,
        mock_add_container_build_step_result_artifacts
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

            # set up mocks
            mock_determine_container_image_address_info.return_value=[
                'localhost/mock-org/mock-app/mock-service:1.0-123abc',
                'mock-org/mock-app/mock-service:1.0-123abc',
                'localhost',
                'mock-app/mock-service',
                '1.0-123abc'
            ]
            mock_get_container_image_digest.return_value = 'sha256:mockabc123'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            mock_get_container_image_digest.assert_called_once_with(
                container_image_address='localhost/mock-org/mock-app/mock-service:1.0-123abc'
            )
            mock_determine_container_image_address_info.assert_called_once_with(
                contaimer_image_registry='localhost',
                container_image_tag='1.0-123abc',
                organization='mock-org',
                application_name='mock-app',
                service_name='mock-service'
            )
            mock_add_container_build_step_result_artifacts.assert_called_once_with(
                step_result=actual_step_result,
                contaimer_image_registry='localhost',
                container_image_repository='mock-app/mock-service',
                container_image_tag='1.0-123abc',
                container_image_digest='sha256:mockabc123',
                container_image_build_address='localhost/mock-org/mock-app/mock-service:1.0-123abc',
                container_image_build_short_address='mock-org/mock-app/mock-service:1.0-123abc'
            )
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/mock-org/mock-app/mock-service:1.0-123abc',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    def test_pass_string_tls_verify_false(
        self,
        buildah_mock,
        mock_determine_container_image_address_info,
        mock_get_container_image_digest,
        mock_add_container_build_step_result_artifacts
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
                'tls-verify': 'false',
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
            mock_determine_container_image_address_info.return_value=[
                'localhost/mock-org/mock-app/mock-service:1.0-123abc',
                'mock-org/mock-app/mock-service:1.0-123abc',
                'localhost',
                'mock-app/mock-service',
                '1.0-123abc'
            ]
            mock_get_container_image_digest.return_value = 'sha256:mockabc123'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            mock_get_container_image_digest.assert_called_once_with(
                container_image_address='localhost/mock-org/mock-app/mock-service:1.0-123abc'
            )
            mock_determine_container_image_address_info.assert_called_once_with(
                contaimer_image_registry='localhost',
                container_image_tag='1.0-123abc',
                organization='mock-org',
                application_name='mock-app',
                service_name='mock-service'
            )
            mock_add_container_build_step_result_artifacts.assert_called_once_with(
                step_result=actual_step_result,
                contaimer_image_registry='localhost',
                container_image_repository='mock-app/mock-service',
                container_image_tag='1.0-123abc',
                container_image_digest='sha256:mockabc123',
                container_image_build_address='localhost/mock-org/mock-app/mock-service:1.0-123abc',
                container_image_build_short_address='mock-org/mock-app/mock-service:1.0-123abc'
            )
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=false',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/mock-org/mock-app/mock-service:1.0-123abc',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    def test_pass_no_container_image_version(
        self,
        buildah_mock,
        mock_determine_container_image_address_info,
        mock_get_container_image_digest,
        mock_add_container_build_step_result_artifacts
    ):
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

            # set up mocks
            mock_determine_container_image_address_info.return_value=[
                'localhost/mock-org/mock-app/mock-service:latest',
                'mock-org/mock-app/mock-service:latest',
                'localhost',
                'mock-app/mock-service',
                'latest'
            ]
            mock_get_container_image_digest.return_value = 'sha256:mockabc123'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            mock_get_container_image_digest.assert_called_once_with(
                container_image_address='localhost/mock-org/mock-app/mock-service:latest'
            )
            mock_determine_container_image_address_info.assert_called_once_with(
                contaimer_image_registry='localhost',
                container_image_tag=None,
                organization='mock-org',
                application_name='mock-app',
                service_name='mock-service'
            )
            mock_add_container_build_step_result_artifacts.assert_called_once_with(
                step_result=actual_step_result,
                contaimer_image_registry='localhost',
                container_image_repository='mock-app/mock-service',
                container_image_tag='latest',
                container_image_digest='sha256:mockabc123',
                container_image_build_address='localhost/mock-org/mock-app/mock-service:latest',
                container_image_build_short_address='mock-org/mock-app/mock-service:latest'
            )
            buildah_mock.bud.assert_called_once_with(
                '--format=oci',
                '--tls-verify=true',
                '--layers', '-f', 'Containerfile',
                '-t', 'localhost/mock-org/mock-app/mock-service:latest',
                '--authfile', os.path.join(step_implementer.work_dir_path, 'container-auth.json'),
                temp_dir.path,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

    def test_fail_buildah_bud_error(
        self,
        buildah_mock,
        mock_determine_container_image_address_info,
        mock_get_container_image_digest,
        mock_add_container_build_step_result_artifacts
    ):
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
            mock_determine_container_image_address_info.return_value=[
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
            mock_get_container_image_digest.assert_not_called()

    def test_fail_getting_digest(
        self,
        buildah_mock,
        mock_determine_container_image_address_info,
        mock_get_container_image_digest,
        mock_add_container_build_step_result_artifacts
    ):
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
            mock_determine_container_image_address_info.return_value=[
                'localhost/mock-org/mock-app-mock-service:1.0-123abc',
                'mock-org/mock-app-mock-service:1.0-123abc',
                'localhost',
                'mock-app-mock-service',
                '1.0-123abc'
            ]
            mock_get_container_image_digest.side_effect = RuntimeError('mock error getting digest')

            # run step
            result = step_implementer._run_step()

             # verify step result
            self.assertFalse(result.success)
            self.assertRegex(
                result.message,
                re.compile(
                    r'Error getting built container image digest: mock error getting digest',
                    re.DOTALL
                )
            )
