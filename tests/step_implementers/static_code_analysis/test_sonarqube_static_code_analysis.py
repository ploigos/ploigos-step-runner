# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
import sys
from unittest.mock import patch

import sh
from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.step_implementers.static_code_analysis import \
    SonarQube
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestStepImplementerSonarQubePackageBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=SonarQube,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

# TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = SonarQube.step_implementer_config_defaults()
        expected_defaults = {
            'properties': './sonar-project.properties',
            'java-truststore': '/etc/pki/java/cacerts'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = SonarQube._required_config_or_result_keys()
        expected_required_keys = [
            'url',
            'application-name',
            'service-name',
            'version'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        step_config = {
            'url' : 'https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
            'application-name': 'app-name',
            'service-name': 'service-name',
            'username': 'username',
            'password': 'password',
            'version': 'notused'
        }

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                parent_work_dir_path=parent_work_dir_path
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_missing_password(self):
        step_config = {
            'url' : 'https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
            'application-name': 'app-name',
            'service-name': 'service-name',
            'username': 'username',
            'version': 'notused'
        }
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                parent_work_dir_path=parent_work_dir_path
            )
            with self.assertRaisesRegex(
                StepRunnerException,
                r"Either 'username' or 'password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_missing_username(self):
        step_config = {
            'url' : 'https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
            'application-name': 'app-name',
            'service-name': 'service-name',
            'password': 'password',
            'version': 'notused'
        }
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                parent_work_dir_path=parent_work_dir_path
            )
            with self.assertRaisesRegex(
                StepRunnerException,
                r"Either 'username' or 'password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_pass(self, sonar_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            artifact_config = {
                'version': {'description': '', 'value': '1.0-123abc'},
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name',
                'username': 'username',
                'password': 'password'

            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis',
                sub_step_name='SonarQube',
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.add_artifact(
                name='sonarqube-result-set',
                value=f'{temp_dir.path}/working/static-code-analysis/report-task.txt'
            )
            expected_step_result.add_evidence(
                name='sonarqube-quality-gate-pass',
                value=True
            )

            sonar_mock.assert_called_once_with(
                    '-Dproject.settings=' + properties_path,
                    '-Dsonar.host.url=https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
                    '-Dsonar.projectVersion=1.0-123abc',
                    '-Dsonar.projectKey=app-name:service-name',
                    '-Dsonar.login=username',
                    '-Dsonar.password=password',
                    '-Dsonar.working.directory=' + step_implementer.work_dir_path,
                    _env={'SONAR_SCANNER_OPTS': '-Djavax.net.ssl.trustStore=/etc/pki/java/cacerts'},
                    _out=sys.stdout,
                    _err=sys.stderr
            )

            self.assertEqual(result, expected_step_result)

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_pass_no_username_and_password(self, sonar_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            artifact_config = {
                'version': {'description': '', 'value': '1.0-123abc'},
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name'

            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis',
                sub_step_name='SonarQube',
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.add_artifact(
                name='sonarqube-result-set',
                value=f'{temp_dir.path}/working/static-code-analysis/report-task.txt'
            )
            expected_step_result.add_evidence(
                name='sonarqube-quality-gate-pass',
                value=True
            )

            sonar_mock.assert_called_once_with(
                    '-Dproject.settings=' + properties_path,
                    '-Dsonar.host.url=https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
                    '-Dsonar.projectVersion=1.0-123abc',
                    '-Dsonar.projectKey=app-name:service-name',
                    '-Dsonar.working.directory=' + step_implementer.work_dir_path,
                    _env={'SONAR_SCANNER_OPTS': '-Djavax.net.ssl.trustStore=/etc/pki/java/cacerts'},
                    _out=sys.stdout,
                    _err=sys.stderr
            )

            self.assertEqual(result, expected_step_result)

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_fail_no_properties(self, sonar_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'version': {'description': '', 'value': '1.0-123abc'},
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': 'https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name'

            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis',
                sub_step_name='SonarQube',
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Properties file not found: ./sonar-project.properties'

            self.assertEqual(result, expected_step_result)

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_pass_alternate_java_truststore(self, sonar_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties', b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')
            temp_dir.write('alternate.jks', b'''testing''')
            java_truststore = os.path.join(temp_dir.path, 'alternate.jks')

            artifact_config = {
                'version': {'description': '', 'value': '1.0-123abc'},
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name',
                'username': 'username',
                'password': 'password',
                'java-truststore': java_truststore
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis',
                sub_step_name='SonarQube',
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.add_artifact(
                name='sonarqube-result-set',
                value=f'{temp_dir.path}/working/static-code-analysis/report-task.txt'
            )
            expected_step_result.add_evidence(
                name='sonarqube-quality-gate-pass',
                value=True
            )

            sonar_mock.assert_called_once_with(
                    '-Dproject.settings=' + properties_path,
                    '-Dsonar.host.url=https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
                    '-Dsonar.projectVersion=1.0-123abc',
                    '-Dsonar.projectKey=app-name:service-name',
                    '-Dsonar.login=username',
                    '-Dsonar.password=password',
                    '-Dsonar.working.directory=' + step_implementer.work_dir_path,
                    _env={'SONAR_SCANNER_OPTS': f'-Djavax.net.ssl.trustStore={java_truststore}'},
                    _out=sys.stdout,
                    _err=sys.stderr
            )

            self.assertEqual(result, expected_step_result)

    def __run__run_step_fail_sonar_scanner_error_test(
        self,
        sonar_scanner_error,
        expected_result_message_regex,
        sonar_mock
    ):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            artifact_config = {
                'version': {'description': '', 'value': '1.0-123abc'},
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name',
                'username': 'username',
                'password': 'password'

            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path,
            )

            sonar_mock.side_effect = sonar_scanner_error

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis',
                sub_step_name='SonarQube',
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.success = False
            expected_step_result.add_artifact(
                name='sonarqube-result-set',
                value=f'{temp_dir.path}/working/static-code-analysis/report-task.txt'
            )
            expected_step_result.add_evidence(
                name='sonarqube-quality-gate-pass',
                value=False
            )

            self.assertEqual(result.success, expected_step_result.success)
            self.assertEqual(result.artifacts, expected_step_result.artifacts)
            self.assertRegex(result.message, expected_result_message_regex)

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_fail_sonar_scanner_internal_error(self, sonar_mock):
        self.__run__run_step_fail_sonar_scanner_error_test(
            sonar_scanner_error=sh.ErrorReturnCode_1(
                'sonar-scanner',
                b'mock out',
                b'mock internal error'
            ),
            expected_result_message_regex=re.compile(
                r"Error running static code analysis using sonar-scanner:"
                r".*RAN: sonar-scanner"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock internal error",
                re.DOTALL
            ),
            sonar_mock=sonar_mock
        )

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_fail_sonar_scanner_tests_failed(self, sonar_mock):
        self.__run__run_step_fail_sonar_scanner_error_test(
           sonar_scanner_error=sh.ErrorReturnCode_2(
                'sonar-scanner',
                b'mock out',
                b'mock user error'
            ),
            expected_result_message_regex=re.compile(
                r"Static code analysis failed."
                r" See 'sonarqube-result-set' result artifact for details.",
                re.DOTALL
            ),
            sonar_mock=sonar_mock
        )

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_fail_sonar_scanner_unexpected_error(self, sonar_mock):
        self.__run__run_step_fail_sonar_scanner_error_test(
           sonar_scanner_error=sh.ErrorReturnCode_42(
                'sonar-scanner',
                b'mock out',
                b'mock unexpected error'
            ),
            expected_result_message_regex=re.compile(
                r"Unexpected error running static code analysis using sonar-scanner:"
                r".*RAN: sonar-scanner"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock unexpected error",
                re.DOTALL
            ),
            sonar_mock=sonar_mock
        )
