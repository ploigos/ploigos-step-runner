# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase

from ploigos_step_runner.step_result import StepResult
from ploigos_step_runner.step_implementers.generate_metadata import SemanticVersion


class TestStepImplementerSemanticVersionGenerateMetadata(BaseStepImplementerTestCase):
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
            step_implementer=SemanticVersion,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = SemanticVersion.step_implementer_config_defaults()
        expected_defaults = {
            'release-branch': 'master'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = SemanticVersion._required_config_or_result_keys()
        expected_required_keys = [
            'app-version',
            'pre-release',
            'release-branch',
            'build'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def test_run_step_pass(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'app-version': {'description': '', 'value': '42.1.0'},
                'pre-release': {'description': '', 'value': 'master'},
                'build': {'description': '', 'value': 'abc123'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='SemanticVersion',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='SemanticVersion',
                sub_step_implementer_name='SemanticVersion'
            )
            expected_step_result.add_artifact(name='version', value='42.1.0+abc123')
            expected_step_result.add_artifact(name='container-image-version', value='42.1.0')

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    def test_run_step_pass_different_pre_release(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'app-version': {'description': '', 'value': '42.1.0'},
                'pre-release': {'description': '', 'value': 'feature123'},
                'build': {'description': '', 'value': 'abc123'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='SemanticVersion',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='SemanticVersion',
                sub_step_implementer_name='SemanticVersion'
            )
            expected_step_result.add_artifact(name='version', value='42.1.0-feature123+abc123')
            expected_step_result.add_artifact(name='container-image-version', value='42.1.0-feature123')

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())
