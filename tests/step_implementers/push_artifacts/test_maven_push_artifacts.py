# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os

from unittest.mock import patch
import sh

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase

from tssc.step_result import StepResult
from tssc.step_implementers.push_artifacts import Maven


class TestStepImplementerMavenPushArtifacts(BaseStepImplementerTestCase):
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
            step_implementer=Maven,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        actual_defaults = Maven.step_implementer_config_defaults()
        expected_defaults = {
        }
        self.assertEqual(expected_defaults, actual_defaults)

    def test_required_runtime_step_config_keys(self):
        actual_required_keys = Maven.required_runtime_step_config_keys()
        expected_required_keys = ['maven-push-artifact-repo-url', 'maven-push-artifact-repo-id']
        self.assertEqual(expected_required_keys, actual_required_keys)

    @patch('sh.mvn', create=True)
    def test_run_step_pass(self, mvn_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'maven-push-artifact-repo-url': 'pass',
                'maven-push-artifact-repo-id': 'pass'
            }

            # Previous (fake) results
            package_artifacts = [{
                'path': 'test-path',
                'group-id': 'test-group-id',
                'artifact-id': 'test-artifact-id',
                'package-type': 'test-package-type'
            }]
            artifact_config = {
                'package-artifacts': {'value': package_artifacts},
                'version': {'value': 'test-version'}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='push-artifacts',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            result = step_implementer._run_step()

            # Expected results
            push_artifacts = [{
                'artifact-id': 'test-artifact-id',
                'group-id': 'test-group-id',
                'version': 'test-version',
                'path': 'test-path',

            }]
            expected_step_result = StepResult(step_name='push-artifacts', sub_step_name='Maven', sub_step_implementer_name='Maven')
            expected_step_result.add_artifact(name='push-artifacts', value=push_artifacts)
            self.assertEqual(expected_step_result.get_step_result(), result.get_step_result())

    @patch('sh.mvn', create=True)
    def test_run_step_fail(self, mvn_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            # config
            step_config = {
                'maven-push-artifact-repo-url': 'pass',
                'maven-push-artifact-repo-id': 'pass'
            }

            # Previous (fake) results
            package_artifacts = [{
                'path': 'test-path',
                'group-id': 'test-group-id',
                'artifact-id': 'test-artifact-id',
                'package-type': 'test-package-type'
            }]
            artifact_config = {
                'package-artifacts': {'value': package_artifacts},
                'version': {'value': 'test-version'}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='push-artifacts',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            sh.mvn.side_effect = sh.ErrorReturnCode('mvn', b'mock stdout', b'mock error')
            with self.assertRaisesRegex(
                     RuntimeError,
                     'Error invoking mvn'):
                step_implementer._run_step()

    @patch('sh.mvn', create=True)
    def test_run_step_fail_missing_version(self, mvn_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'maven-push-artifact-repo-url': 'pass',
                'maven-push-artifact-repo-id': 'pass'
            }

            # Previous (fake) results
            package_artifacts = [{
                'path': 'test-path',
                'group-id': 'test-group-id',
                'artifact-id': 'test-artifact-id',
                'package-type': 'test-package-type'
            }]
            artifact_config = {
                'package-artifacts': {'value': package_artifacts},
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='push-artifacts',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            result = step_implementer._run_step()

            # Expected results
            expected_step_result = StepResult(step_name='push-artifacts', sub_step_name='Maven', sub_step_implementer_name='Maven')
            expected_step_result.success = False
            expected_step_result.message = 'previous step results missing version'
            self.assertEqual(expected_step_result.get_step_result(), result.get_step_result())

    @patch('sh.mvn', create=True)
    def test_run_step_fail_missing_package_artifacts(self, mvn_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'maven-push-artifact-repo-url': 'pass',
                'maven-push-artifact-repo-id': 'pass'
            }

            artifact_config = {
                'version': {'value': 'test-version'}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            # Actual results
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='push-artifacts',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            result = step_implementer._run_step()

            # Expected results
            expected_step_result = StepResult(step_name='push-artifacts', sub_step_name='Maven', sub_step_implementer_name='Maven')
            expected_step_result.success = False
            expected_step_result.message = 'previous step results missing package-artifacts'
            self.assertEqual(expected_step_result.get_step_result(), result.get_step_result())
