# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
from io import IOBase
from pathlib import Path
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any
from ploigos_step_runner.step_implementers.push_container_image import Skopeo
from ploigos_step_runner.step_result import StepResult


class TestStepImplementerSkopeoSourceBase(BaseStepImplementerTestCase):
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
            step_implementer=Skopeo,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = Skopeo.step_implementer_config_defaults()
        expected_defaults = {
            'containers-config-auth-file': os.path.join(Path.home(), '.skopeo-auth.json'),
            'dest-tls-verify': 'true',
            'src-tls-verify': 'true'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Skopeo._required_config_or_result_keys()
        expected_required_keys = [
            'containers-config-auth-file',
            'destination-url',
            'src-tls-verify',
            'dest-tls-verify',
            'service-name',
            'application-name',
            'organization',
            'container-image-version',
            'image-tar-file'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    @patch.object(sh, 'skopeo', create=True)
    def test_run_step_pass(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            image_tar_file = 'fake-image.tar'
            image_version = '1.0-69442c8'
            image_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-version': image_version,
                'image-tar-file': image_tar_file
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='push-container-image',
                implementer='Skopeo',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='push-container-image',
                sub_step_name='Skopeo',
                sub_step_implementer_name='Skopeo'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='fake-registry.xyz'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='fake-org'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='fake-app-fake-service'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='fake-app-fake-service'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value=image_version
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='fake-registry.xyz/fake-org/fake-app-fake-service:1.0-69442c8'
            )
            self.assertEqual(
                result.get_step_result_dict(),
                expected_step_result.get_step_result_dict()
            )

            containers_config_auth_file = os.path.join(Path.home(), '.skopeo-auth.json')
            skopeo_mock.copy.assert_called_once_with(
                "--src-tls-verify=true",
                "--dest-tls-verify=true",
                f"--authfile={containers_config_auth_file}",
                f'docker-archive:{image_tar_file}',
                f'docker://{image_tag}',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

    @patch.object(sh, 'skopeo', create=True)
    def test_run_step_fail_run_skopeo(self, skopeo_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            image_tar_file = 'fake-image.tar'
            image_version = '1.0-69442c8'
            image_tag = f'fake-registry.xyz/fake-org/fake-app-fake-service:{image_version}'
            step_config = {
                'destination-url': 'fake-registry.xyz',
                'service-name': 'fake-service',
                'application-name': 'fake-app',
                'organization': 'fake-org',
                'container-image-version': image_version,
                'image-tar-file': image_tar_file
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='push-container-image',
                implementer='Skopeo',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            skopeo_mock.copy.side_effect = sh.ErrorReturnCode('skopeo', b'mock stdout', b'mock error')
            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='push-container-image',
                sub_step_name='Skopeo',
                sub_step_implementer_name='Skopeo'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-uri',
                value='fake-registry.xyz'
            )
            expected_step_result.add_artifact(
                name='container-image-registry-organization',
                value='fake-org'
            )
            expected_step_result.add_artifact(
                name='container-image-repository',
                value='fake-app-fake-service'
            )
            expected_step_result.add_artifact(
                name='container-image-name',
                value='fake-app-fake-service'
            )
            expected_step_result.add_artifact(
                name='container-image-version',
                value=image_version
            )
            expected_step_result.add_artifact(
                name='container-image-tag',
                value='fake-registry.xyz/fake-org/fake-app-fake-service:1.0-69442c8'
            )
            expected_step_result.success = False
            expected_step_result.message = f"Error pushing container image ({image_tar_file}) " +\
                f" to tag ({image_tag}) using skopeo: \n" +\
                f"\n" +\
                f"  RAN: skopeo\n" +\
                f"\n" +\
                f"  STDOUT:\n" +\
                f"mock stdout\n" +\
                f"\n" +\
                f"  STDERR:\n" +\
                f"mock error"

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

            containers_config_auth_file = os.path.join(Path.home(), '.skopeo-auth.json')
            skopeo_mock.copy.assert_called_once_with(
                "--src-tls-verify=true",
                "--dest-tls-verify=true",
                f"--authfile={containers_config_auth_file}",
                f'docker-archive:{image_tar_file}',
                f'docker://{image_tag}',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )
