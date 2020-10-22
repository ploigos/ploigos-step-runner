import os
from io import IOBase, StringIO

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase

from tssc.config.config import Config
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult
from tssc.step_implementers.generate_metadata import SemanticVersion


class TestStepImplementerSemanticVersionGenerateMetadata(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            test_config={},
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=SemanticVersion,
            step_config=step_config,
            test_config=test_config,
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

    def test_required_runtime_step_config_keys(self):
        required_keys = SemanticVersion.required_runtime_step_config_keys()
        expected_required_keys = []
        self.assertEqual(required_keys, expected_required_keys)

    def test_run_step_pass(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_config = {}
            test_config = {'step-name': 'generate-metadata', 'implementer': 'SemanticVersion'}

            # create fake step implementer step_results
            step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            step_result.add_artifact(name='app-version', value='42.1.0')
            step_result.add_artifact(name='pre-release', value='master')
            step_result.add_artifact(name='build', value='abc123')
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result=step_result)
            pickle_filename = os.path.join(work_dir_path, 'tssc-results.pkl')
            workflow_result.write_to_pickle_file(pickle_filename=pickle_filename)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            expected_step_result.add_artifact(name='version', value='42.1.0+abc123')
            expected_step_result.add_artifact(name='container-image-version', value='42.1.0')

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    def test_run_step_no_app_version(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_config = {}
            test_config = {'step-name': 'generate-metadata', 'implementer': 'SemanticVersion'}

            # create fake step implementer step_results
            step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            step_result.add_artifact(name='pre-release', value='master')
            step_result.add_artifact(name='build', value='abc123')
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result=step_result)
            pickle_filename = os.path.join(work_dir_path, 'tssc-results.pkl')
            workflow_result.write_to_pickle_file(pickle_filename=pickle_filename)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            expected_step_result.success = False
            expected_step_result.message = f'No value for (app-version) provided via runtime flag' \
                '(app-version) or from prior step implementer ({self.step_name}).'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    def test_run_step_no_pre_release(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_config = {}
            test_config = {'step-name': 'generate-metadata', 'implementer': 'SemanticVersion'}

            # create fake step implementer step_results
            step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            step_result.add_artifact(name='app-version', value='42.1.0')
            step_result.add_artifact(name='build', value='abc123')
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result=step_result)
            pickle_filename = os.path.join(work_dir_path, 'tssc-results.pkl')
            workflow_result.write_to_pickle_file(pickle_filename=pickle_filename)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            expected_step_result.success = False
            expected_step_result.message = f'No value for (pre-release) provided via runtime flag' \
                '(pre-release) or from prior step implementer ({self.step_name}).'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    def test_run_step_no_build(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_config = {}
            test_config = {'step-name': 'generate-metadata', 'implementer': 'SemanticVersion'}

            # create fake step implementer step_results
            step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            step_result.add_artifact(name='app-version', value='42.1.0')
            step_result.add_artifact(name='pre-release', value='master')
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result=step_result)
            pickle_filename = os.path.join(work_dir_path, 'tssc-results.pkl')
            workflow_result.write_to_pickle_file(pickle_filename=pickle_filename)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            expected_step_result.success = False
            expected_step_result.message = f'No value for (build) provided via runtime flag' \
                '(build) or from prior step implementer ({self.step_name}).'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    def test_run_step_pass_different_pre_release(self):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_config = {}
            test_config = {'step-name': 'generate-metadata', 'implementer': 'SemanticVersion'}

            # create fake step implementer step_results
            step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            step_result.add_artifact(name='app-version', value='42.1.0')
            step_result.add_artifact(name='pre-release', value='feature123')
            step_result.add_artifact(name='build', value='abc123')
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result=step_result)
            pickle_filename = os.path.join(work_dir_path, 'tssc-results.pkl')
            workflow_result.write_to_pickle_file(pickle_filename=pickle_filename)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='SemanticVersion', sub_step_implementer_name='SemanticVersion')
            expected_step_result.add_artifact(name='version', value='42.1.0-feature123+abc123')
            expected_step_result.add_artifact(name='container-image-version', value='42.1.0-feature123')

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())
