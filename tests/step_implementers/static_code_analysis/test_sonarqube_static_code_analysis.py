import os
import re
import sys
from io import IOBase, StringIO
from unittest.mock import MagicMock, patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tssc.config.config import Config
from tssc.step_implementers.static_code_analysis import SonarQube
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult
from tests.helpers.test_utils import Any
from pathlib import Path


class TestStepImplementerSonarQubePackageBase(BaseStepImplementerTestCase):
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
            step_implementer=SonarQube,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

# TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = SonarQube.step_implementer_config_defaults()
        expected_defaults = {
            'properties': './sonar-project.properties'
        }
        self.assertEqual(defaults, expected_defaults)

    def test_required_runtime_step_config_keys(self):
        required_keys = SonarQube.required_runtime_step_config_keys()
        expected_required_keys = [
            'url',
            'application-name',
            'service-name'
        ]
        self.assertEqual(required_keys, expected_required_keys)
    
    def test__validate_runtime_step_config_valid(self):
        step_config = {            
            'url' : 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
            'application-name': 'app-name',
            'service-name': 'service-name',
            'username': 'username',
            'password': 'password'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='static-code-analysis',
            implementer='SonarQube'
        )

        step_implementer._validate_runtime_step_config(step_config)

    def test__validate_runtime_step_config_invalid(self):
        step_config = {
            'url' : 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
            'application-name': 'app-name',
            'service-name': 'service-name',
            'username': 'username'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='static-code-analysis',
            implementer='SonarQube'
        )
        with self.assertRaisesRegex(
                AssertionError,
                re.compile(
                    'Either username or password is not set. Neither or both must be set.'
                )
        ):
            step_implementer._validate_runtime_step_config(step_config)
    
    @patch('sh.sonar_scanner', create=True)
    def test_run_step_pass(self, sonar_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name',
                'username': 'username',
                'password': 'password'

            }
            
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis', 
                sub_step_name='SonarQube', 
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.add_artifact(name='sonarqube_result_set', value=f'file://{temp_dir.path}/working/report-task.txt', value_type='file')
            
            sonar_mock.assert_called_once_with(
                    '-Dproject.settings=' + properties_path,
                    '-Dsonar.host.url=https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                    '-Dsonar.projectVersion=1.0-123abc',
                    '-Dsonar.projectKey=app-name:service-name',
                    '-Dsonar.login=username',
                    '-Dsonar.password=password',
                    '-Dsonar.working.directory=' + work_dir_path,
                    _out=sys.stdout,
                    _err=sys.stderr
            )

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_pass_no_username_and_password(self, sonar_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name'

            }
            
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis', 
                sub_step_name='SonarQube', 
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.add_artifact(name='sonarqube_result_set', value=f'file://{temp_dir.path}/working/report-task.txt', value_type='file')
            
            sonar_mock.assert_called_once_with(
                    '-Dproject.settings=' + properties_path,
                    '-Dsonar.host.url=https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                    '-Dsonar.projectVersion=1.0-123abc',
                    '-Dsonar.projectKey=app-name:service-name',
                    '-Dsonar.working.directory=' + work_dir_path,
                    _out=sys.stdout,
                    _err=sys.stderr
            )

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_fail_no_version(self, sonar_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name'

            }
            
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis', 
                sub_step_name='SonarQube', 
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Severe error: Generate-metadata results is missing a version tag'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())
    
    @patch('sh.sonar_scanner', create=True)
    def test_run_step_fail_no_properties(self, sonar_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name'

            }
            
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis', 
                sub_step_name='SonarQube', 
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Properties file in tssc config not found: ./sonar-project.properties'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())
    
    @patch('sh.sonar_scanner', create=True)
    def test_run_step_fail_sonar_error(self, sonar_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name',
                'username': 'username',
                'password': 'password'

            }
            
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            sonar_mock.side_effect = sh.ErrorReturnCode('sonar', b'mock out', b'mock error')

            with self.assertRaisesRegex(
                RuntimeError,
                "Error invoking sonarscanner:"
            ):
                step_implementer._run_step()