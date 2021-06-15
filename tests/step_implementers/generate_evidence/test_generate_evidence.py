import os
import zipfile
from pathlib import Path
from unittest.mock import patch

import mock
from ploigos_step_runner import StepResult
from ploigos_step_runner.results.workflow_result import WorkflowResult
from ploigos_step_runner.step_implementers.generate_evidence import GenerateEvidence
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestStepImplementerGenerateEvidenceBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=GenerateEvidence,
            step_config=step_config,
            step_name='generate_evidence',
            implementer='GenerateEvidence',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

class TestStepImplementerGenerateEvidence_other(TestStepImplementerGenerateEvidenceBase):
    def test_step_implementer_config_defaults(self):
        defaults = GenerateEvidence.step_implementer_config_defaults()
        expected_defaults = {
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = GenerateEvidence._required_config_or_result_keys()
        expected_required_keys = [
            'organization',
            'application-name',
            'service-name',
            'version',
        ]
        self.assertEqual(required_keys, expected_required_keys)

class TestStepImplementerGenerateEvidence_run_step(TestStepImplementerGenerateEvidenceBase):

    def __run_step(self, parent_work_dir_path):
        step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test',
            }

        step_result = StepResult(
            step_name='test-step',
            sub_step_name='test-sub-step',
            sub_step_implementer_name='test-sub-step-implementer'
        )
        step_result.add_evidence(
            name='test-evidence',
            value="test-value",
            description="test-description"
        )
        step_result.add_evidence(
            name='test-evidence2',
            value="test-value2",
            description="test-description2"
        )

        workflow_result = WorkflowResult()
        workflow_result.add_step_result(step_result)

        step_implementer = self.create_step_implementer(
            step_config=step_config,
            parent_work_dir_path=parent_work_dir_path,
            workflow_result=workflow_result
        )

        return step_implementer._run_step()

    
    def test__run_step_pass_no_evidence(self):
        step_config = {
            'organization': 'test-ORG',
            'application-name': 'test-APP',
            'service-name': 'test-SERVICE',
            'version': '42.0-test'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        step_result = step_implementer._run_step()
        expected_step_result = StepResult(
            step_name='generate_evidence',
            sub_step_name='GenerateEvidence',
            sub_step_implementer_name='GenerateEvidence'
        )
        expected_step_result.add_artifact(
            name='result-generate-evidence',
            value='No evidence to generate.',
            description='Evidence from all previously run steps.'
        )
        expected_step_result.message = "No evidence generated from previously run steps"

        self.assertEqual(step_result, expected_step_result)

    def test__run_step_pass_gather_evidence(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            

            # run the step
            step_result =  self.__run_step(parent_work_dir_path)

            # verify results
            expected_step_result = StepResult(
                step_name='generate_evidence',
                sub_step_name='GenerateEvidence',
                sub_step_implementer_name='GenerateEvidence'
            )
            expected_step_result.add_artifact(
            name='result-generate-evidence-path',
            value=os.path.join(parent_work_dir_path, 'generate_evidence',
             "test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json"),
            description='File path of evidence.'
            )
            expected_step_result.message = "Evidence successfully packaged in JSON file and uploaded to data store."

            self.assertEqual(step_result, expected_step_result)

    def test___gather_evidence_no_results(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            gathered_evidence = step_implementer._GenerateEvidence__gather_evidence()

            self.assertIsNone(gathered_evidence)

    def test_write_results_to_json_file(self):

        expected_evidence = \
                """{
    "apiVersion": "automated-governance/v1alpha1",
    "kind": "WorkflowEvidence",
    "workflow": {
        "test-step": {
            "test-sub-step": {
                "attestations": {
                    "test-evidence": {
                        "name": "test-evidence",
                        "value": "test-value",
                        "description": "test-description"
                    },
                    "test-evidence2": {
                        "name": "test-evidence2",
                        "value": "test-value2",
                        "description": "test-description2"
                    }
                }
            }
        }
    }
}"""

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_result =  self.__run_step(parent_work_dir_path)
            
            json_file_path = step_result.get_artifact_value("result-generate-evidence-path")

            with open(json_file_path, 'r') as actual_json_file:
                json_file_contents = actual_json_file.read()
                print(json_file_contents)
                self.assertEqual(json_file_contents, expected_evidence)

    @patch('ploigos_step_runner.step_implementers.generate_evidence.generate_evidence.upload_file')
    def test__run_step_pass_upload_to_file(self, upload_file_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_result = StepResult(
            step_name='test-step',
            sub_step_name='test-sub-step',
            sub_step_implementer_name='test-sub-step-implementer'
        )
            step_result.add_evidence(
                name='test-evidence',
                value="test-value",
                description="test-description"
            )
            step_result.add_evidence(
                name='test-evidence2',
                value="test-value2",
                description="test-description2"
            )

            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)

            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test',
                'evidence-destination-url': 'https://ploigos.com/mock/evidences',
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            # mock the upload results
            upload_file_mock.return_value = "mock upload results"

            # run the step
            step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate_evidence',
                sub_step_name='GenerateEvidence',
                sub_step_implementer_name='GenerateEvidence'
            )
            expected_step_result.add_artifact(
                name='results-evidence-upload-results',
                description='Results of uploading the evidence JSON file ' \
                            'to the given destination.',
                value='mock upload results'
                )
            expected_step_result.add_artifact(
                name='evidence-uri',
                description='URI of the uploaded results archive.',
                value='https://ploigos.com/mock/evidences/'\
                    'test-ORG/'\
                    'test-APP/test-SERVICE/test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json'
            )
            expected_step_result.add_artifact(
                name='result-generate-evidence-path',
                value=os.path.join(parent_work_dir_path, 'generate_evidence',
                "test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json"),
                description='File path of evidence.'
                )
            expected_step_result.message = "Evidence successfully packaged in JSON file and uploaded to data store."

            print(step_result)
            print("")
            print(expected_step_result)

            self.assertEqual(step_result, expected_step_result)

            # verify mocks called
            upload_file_mock.assert_called_once_with(
                file_path=mock.ANY,
                destination_uri='https://ploigos.com/mock/evidences/test-ORG/test-APP/'\
                'test-SERVICE/test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json',
                username=None,
                password=None
            )

    @patch('ploigos_step_runner.step_implementers.generate_evidence.generate_evidence.upload_file')
    def test__run_step_pass_upload_to_remote_with_auth(self, upload_file_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_result = StepResult(
            step_name='test-step',
            sub_step_name='test-sub-step',
            sub_step_implementer_name='test-sub-step-implementer'
        )
            step_result.add_evidence(
                name='test-evidence',
                value="test-value",
                description="test-description"
            )
            step_result.add_evidence(
                name='test-evidence2',
                value="test-value2",
                description="test-description2"
            )

            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)

            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test',
                'evidence-destination-url': 'https://ploigos.com/mock/evidences',
                'evidence-destination-username': 'test-user',
                'evidence-destination-password': 'test-pass'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            # mock the upload results
            upload_file_mock.return_value = "mock upload results"

            # run the step
            step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate_evidence',
                sub_step_name='GenerateEvidence',
                sub_step_implementer_name='GenerateEvidence'
            )
            expected_step_result.add_artifact(
                name='results-evidence-upload-results',
                description='Results of uploading the evidence JSON file ' \
                            'to the given destination.',
                value='mock upload results'
                )
            expected_step_result.add_artifact(
                name='evidence-uri',
                description='URI of the uploaded results archive.',
                value='https://ploigos.com/mock/evidences/'\
                    'test-ORG/'\
                    'test-APP/test-SERVICE/test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json'
            )
            expected_step_result.add_artifact(
                name='result-generate-evidence-path',
                value=os.path.join(parent_work_dir_path, 'generate_evidence',
                "test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json"),
                description='File path of evidence.'
                )
            expected_step_result.message = "Evidence successfully packaged in JSON file and uploaded to data store."

            self.assertEqual(step_result, expected_step_result)

            # verify mocks called
            upload_file_mock.assert_called_once_with(
                file_path=mock.ANY,
                destination_uri='https://ploigos.com/mock/evidences/test-ORG/test-APP/'\
                'test-SERVICE/test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json',
                username='test-user',
                password='test-pass'
            )

    @patch('ploigos_step_runner.step_implementers.generate_evidence.generate_evidence.upload_file')
    def test__run_step_pass_upload_to_remote_with_auth_failure(self, upload_file_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_result = StepResult(
            step_name='test-step',
            sub_step_name='test-sub-step',
            sub_step_implementer_name='test-sub-step-implementer'
        )
            step_result.add_evidence(
                name='test-evidence',
                value="test-value",
                description="test-description"
            )
            step_result.add_evidence(
                name='test-evidence2',
                value="test-value2",
                description="test-description2"
            )

            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)

            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test',
                'evidence-destination-url': 'https://ploigos.com/mock/evidences',
                'evidence-destination-username': 'test-user',
                'evidence-destination-password': 'test-pass'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            # mock the upload results
            upload_file_mock.side_effect = RuntimeError('mock upload error')
            upload_file_mock.return_value = "mock upload results"

            # run the step
            step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate_evidence',
                sub_step_name='GenerateEvidence',
                sub_step_implementer_name='GenerateEvidence'
            )
            expected_step_result.add_artifact(
                name='results-evidence-upload-results',
                description='Results of uploading the evidence JSON file ' \
                            'to the given destination.',
                value='mock upload results'
                )
            expected_step_result.add_artifact(
                name='evidence-uri',
                description='URI of the uploaded results archive.',
                value='https://ploigos.com/mock/evidences/'\
                    'test-ORG/'\
                    'test-APP/test-SERVICE/test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json'
            )
            expected_step_result.add_artifact(
                name='result-generate-evidence-path',
                value=os.path.join(parent_work_dir_path, 'generate_evidence',
                "test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json"),
                description='File path of evidence.'
                )
            expected_step_result.message = "Evidence successfully packaged in JSON file and uploaded to data store."

            expected_step_result.success = False
            expected_step_result.message = 'mock upload error'

            # verify mocks called
            upload_file_mock.assert_called_once_with(
                file_path=mock.ANY,
                destination_uri='https://ploigos.com/mock/evidences/test-ORG/test-APP/'\
                'test-SERVICE/test-ORG-test-APP-test-SERVICE-42.0-test-evidence.json',
                username='test-user',
                password='test-pass'
            )
