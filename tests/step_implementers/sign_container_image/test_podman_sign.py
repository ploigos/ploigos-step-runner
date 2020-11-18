# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
from unittest.mock import patch
from testfixtures import TempDirectory
from tssc.step_implementers.sign_container_image import PodmanSign
from tssc.step_result import StepResult
from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase


class TestStepImplementerPodmanSignSourceBase(BaseStepImplementerTestCase):

    @staticmethod
    def gpg_side_effect(*_args, **kwargs):
        """Side effect for gpg key load"""
        kwargs['_out']('fpr:::::::::DD7208BA0A6359F65B906B29CF4AC14A3D109637:')

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
            step_implementer=PodmanSign,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    # TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = PodmanSign.step_implementer_config_defaults()
        expected_defaults = {}
        self.assertEqual(defaults, expected_defaults)

    def test_required_runtime_step_config_keys(self):
        required_keys = PodmanSign.required_runtime_step_config_keys()
        expected_required_keys = ['container-image-signer-pgp-private-key']
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_runtime_step_config_valid(self):
        step_config = {
            'container-image-signer-pgp-private-key': 'test'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='sign-container-image',
            implementer='PodmanSign'
        )

        step_implementer._validate_runtime_step_config(step_config)

    def test__validate_runtime_step_config_invalid(self):
        step_config = {
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='sign-container-image',
            implementer='PodmanSign'
        )
        with self.assertRaisesRegex(
                AssertionError,
                r"The runtime step configuration \({}\) is missing "
                r"the required configuration keys "
                r"\(\['container-image-signer-pgp-private-key'\]\)"
        ):
            step_implementer._validate_runtime_step_config(step_config)

    @patch.object(PodmanSign, '_PodmanSign__import_pgp_key')
    @patch.object(PodmanSign, '_PodmanSign__sign_image')
    def test_run_step_pass(self, sign_image_mock, import_pgp_key_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            pgp_private_key_fingerprint = 'abc123'
            step_config = {
            }
            container_image_tag = 'does/not/matter:v0.42.0'
            signature_name = 'does/not/matter/signature-0'

            # Previous (fake) results
            artifact_config = {
                'container-image-tag': {'value': container_image_tag}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            def import_pgp_key_side_effect(pgp_private_key):
                return pgp_private_key_fingerprint

            import_pgp_key_mock.side_effect = import_pgp_key_side_effect

            def sign_image_side_effect(
                    pgp_private_key_fingerprint,
                    image_signatures_directory,
                    container_image_tag
            ):
                return os.path.join(image_signatures_directory, signature_name)

            sign_image_mock.side_effect = sign_image_side_effect

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='sign-container-image',
                implementer='PodmanSign',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            # # Expected results
            expected_step_result = StepResult(step_name='sign-container-image', sub_step_name='PodmanSign',
                                              sub_step_implementer_name='PodmanSign')
            expected_step_result.add_artifact(name='container-image-signature-file-path',
                                              value= os.path.join(
                                                  work_dir_path,
                                                  'sign-container-image/image-signature',
                                                  signature_name)
                                              )
            expected_step_result.add_artifact(name='container-image-signature-name',
                                              value=signature_name)
            expected_step_result.add_artifact(name='container-image-signature-private-key-fingerprint',
                                              value=pgp_private_key_fingerprint)
            self.assertEqual(expected_step_result.get_step_result(), result.get_step_result())
