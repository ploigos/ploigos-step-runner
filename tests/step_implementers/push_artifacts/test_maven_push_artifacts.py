# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.push_artifacts import Maven


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
            'tls-verify': True
        }
        self.assertEqual(expected_defaults, actual_defaults)

    def test__required_config_or_result_keys(self):
        actual_required_keys = Maven._required_config_or_result_keys()
        expected_required_keys = [
            'maven-push-artifact-repo-url',
            'maven-push-artifact-repo-id',
            'version',
            'package-artifacts'
        ]
        self.assertEqual(expected_required_keys, actual_required_keys)

    @patch('sh.mvn', create=True)
    def test_run_step_pass(self, mvn_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
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
                'packaging': 'test-package-type',
            }]
            expected_step_result = StepResult(
                step_name='push-artifacts',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.add_artifact(name='push-artifacts', value=push_artifacts)
            mvn_output_file_path = os.path.join(
                work_dir_path,
                'push-artifacts',
                'mvn_test_output.txt'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from 'mvn install'.",
                name='maven-output',
                value=mvn_output_file_path
            )
            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())

    @patch('sh.mvn', create=True)
    def test_run_step_fail(self, mvn_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
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
            sh.mvn.side_effect = sh.ErrorReturnCode('mvn', b'mock out', b'mock error')

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='push-artifacts',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.add_artifact(
                name='push-artifacts',
                value=[]
            )
            mvn_output_file_path = os.path.join(
                work_dir_path,
                'push-artifacts',
                'mvn_test_output.txt'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from 'mvn install'.",
                name='maven-output',
                value=mvn_output_file_path
            )
            expected_step_result.success = False

            self.assertEqual(result.success, expected_step_result.success)
            self.assertRegex(result.message, re.compile(
                r"Push artifacts failures. See 'maven-output' report artifacts for details:"
                r".*RAN: mvn"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            ))
            self.assertEqual(result.artifacts, expected_step_result.artifacts)

    @patch('sh.mvn', create=True)
    def test_run_step_tls_verify_false(self, mvn_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'maven-push-artifact-repo-url': 'pass',
                'maven-push-artifact-repo-id': 'pass',
                'tls-verify': False
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
                'packaging': 'test-package-type',
            }]
            expected_step_result = StepResult(
                step_name='push-artifacts',
                sub_step_name='Maven',
                sub_step_implementer_name='Maven'
            )
            expected_step_result.add_artifact(name='push-artifacts', value=push_artifacts)
            mvn_output_file_path = os.path.join(
                work_dir_path,
                'push-artifacts',
                'mvn_test_output.txt'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from 'mvn install'.",
                name='maven-output',
                value=mvn_output_file_path
            )
            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())

