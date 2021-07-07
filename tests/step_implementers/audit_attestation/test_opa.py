import os
from io import IOBase
from pathlib import Path
from unittest.mock import patch

import mock
import re
import sh
from ploigos_step_runner import StepResult
from ploigos_step_runner.results.workflow_result import WorkflowResult
from ploigos_step_runner.step_implementers.audit_attestation import OpenPolicyAgent
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any, create_sh_side_effect

class TestStepImplementerOpenPolicyAgentBase(BaseStepImplementerTestCase):

    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path='',
            environment=None
    ):
        return self.create_given_step_implementer(
            step_implementer=OpenPolicyAgent,
            step_config=step_config,
            step_name='audit_attestation',
            implementer='OpenPolicyAgent',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            environment=environment
        )

class TestStepImplementerOpenPolicyAgent_other(TestStepImplementerOpenPolicyAgentBase):
    def test_step_implementer_config_defaults(self):
        defaults = OpenPolicyAgent.step_implementer_config_defaults()
        expected_defaults = {
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = OpenPolicyAgent._required_config_or_result_keys()
        expected_required_keys = [
            'workflow-policy-uri',
            'evidence-uri'
        ]
        self.assertEqual(required_keys, expected_required_keys)

class TestStepImplementerOpenPolicyAgent_run_step(TestStepImplementerOpenPolicyAgentBase):


    @patch('ploigos_step_runner.step_implementers.audit_attestation.opa.download_source_to_destination')
    @patch.object(
        OpenPolicyAgent,
        '_OpenPolicyAgent__audit_attestation',
        return_value = None
    )
    def test__run_step_pass_audit_success(self,
        audit_attestation_mock,
        download_source_to_destination_mock):
        with TempDirectory() as temp_dir:

            workflow_attestation_uri = 'https://foo.bar/evidence.json'
            workflow_policy_uri = 'https://foo.bar/policy.json'

            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'workflow-policy-uri': workflow_policy_uri
            }

            step_result = StepResult(
            step_name='test-step',
            sub_step_name='test-sub-step',
            sub_step_implementer_name='test-sub-step-implementer'
            )
            step_result.add_artifact('evidence-uri', workflow_attestation_uri, 'URI of the uploaded results archive.')

            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            download_source_to_destination_mock.side_effect = [
                parent_work_dir_path + '/workflow_attestion.json',
                parent_work_dir_path + '/workflow_policy.rego']

            audit_attestation_mock.return_value = "Audit was successful", 0

            step_result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='audit_attestation',
                sub_step_name='OpenPolicyAgent',
                sub_step_implementer_name='OpenPolicyAgent'
            )
            expected_step_result.add_artifact(
                name='audit-results',
                value='Audit was successful'
            )
            expected_step_result.message = 'Audit was successful'

            self.assertEqual(step_result, expected_step_result)

            audit_attestation_mock.assert_called_once_with(parent_work_dir_path + '/workflow_attestion.json',
                parent_work_dir_path + '/workflow_policy.rego', "data.workflowResult.passAll")

            download_source_to_destination_mock.assert_has_calls([
                mock.call(workflow_attestation_uri,
                parent_work_dir_path + '/audit_attestation'),
                mock.call(workflow_policy_uri,
                parent_work_dir_path  + '/audit_attestation')
                ]
            )


    def test__run_step_fail_audit_fail_missing_workflow_attestation(self):
        with TempDirectory() as temp_dir:

            workflow_attestation_uri = 'https://foo.bar/evidence.json'
            workflow_policy_uri = 'https://foo.bar/policy.json'

            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'workflow-policy-uri': workflow_policy_uri
            }

            step_result = StepResult(
            step_name='test-step',
            sub_step_name='test-sub-step',
            sub_step_implementer_name='test-sub-step-implementer'
            )
            step_result.add_artifact('evidence-uri-wrong-key', workflow_attestation_uri, 'URI of the uploaded results archive.')

            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            step_result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='audit_attestation',
                sub_step_name='OpenPolicyAgent',
                sub_step_implementer_name='OpenPolicyAgent'
            )

            expected_step_result.success = False
            expected_step_result.message = "No value found for evidence-uri"

            self.assertEqual(step_result, expected_step_result)

    @patch('ploigos_step_runner.step_implementers.audit_attestation.opa.download_source_to_destination')
    @patch.object(
        OpenPolicyAgent,
        '_OpenPolicyAgent__audit_attestation',
        return_value = None
    )
    def test__run_step_fail_audit_fail_error_on_audit(self,
        audit_attestation_mock,
        download_source_to_destination_mock):
        with TempDirectory() as temp_dir:

            workflow_attestation_uri = 'https://foo.bar/evidence.json'
            workflow_policy_uri = 'https://foo.bar/policy.json'

            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'workflow-policy-uri': workflow_policy_uri
            }

            step_result = StepResult(
            step_name='test-step',
            sub_step_name='test-sub-step',
            sub_step_implementer_name='test-sub-step-implementer'
            )
            step_result.add_artifact('evidence-uri', workflow_attestation_uri, 'URI of the uploaded results archive.')

            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            download_source_to_destination_mock.side_effect = [
                parent_work_dir_path + '/workflow_attestion.json',
                parent_work_dir_path + '/workflow_policy.rego']

            audit_attestation_mock.return_value = "foo", 1

            step_result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='audit_attestation',
                sub_step_name='OpenPolicyAgent',
                sub_step_implementer_name='OpenPolicyAgent'
            )
            expected_step_result.add_artifact(
                name='audit-results',
                value='foo'
            )
            expected_step_result.success = False
            expected_step_result.message = step_result.message = "Attestation error: foo"

            self.assertEqual(step_result, expected_step_result)

            audit_attestation_mock.assert_has_calls([
                mock.call(parent_work_dir_path + '/workflow_attestion.json',
                parent_work_dir_path + '/workflow_policy.rego', "data.workflowResult.passAll"),
                mock.call(parent_work_dir_path + '/workflow_attestion.json',
                parent_work_dir_path + '/workflow_policy.rego', "data")
            ])

            download_source_to_destination_mock.assert_has_calls([
                mock.call(workflow_attestation_uri,
                parent_work_dir_path + '/audit_attestation'),
                mock.call(workflow_policy_uri,
                parent_work_dir_path  + '/audit_attestation')
                ]
            )

class TestStepImplementerOpenPolicyAgent_audit_attestation(TestStepImplementerOpenPolicyAgentBase):

    @patch('sh.opa', create=True)
    def test_audit_attestation_pass(self, audit_results_mock):


        step_config = {
                'workflow-policy-uri': "https://foo.bar"
        }

        step_implementer = self.create_step_implementer(
            step_config=step_config
        )
        audit_results_mock.return_value = "pass"

        workflow_attestation_file_path = "workflow_attestation_file_path"
        workflow_policy_file_path = "workflow_policy_file_path"
        workflow_policy_query =  "fooquery"

        step_implementer._OpenPolicyAgent__audit_attestation(
            workflow_attestation_file_path = "workflow_attestation_file_path",
            workflow_policy_file_path = "workflow_policy_file_path",
            workflow_policy_query =  "fooquery"
        )

        audit_results_mock.assert_called_once_with(
            'eval',
            '--fail-defined',
            '-d',
            workflow_attestation_file_path,
            '-i',
            workflow_policy_file_path,
            workflow_policy_query,
            _out=Any(IOBase),
            _err_to_out=True,
            _tee='out'
        )

    @patch('sh.opa', create=True)
    def test_audit_attestation_fail(self, audit_results_mock):


        step_config = {
                'workflow-policy-uri': "https://foo.bar"
        }

        step_implementer = self.create_step_implementer(
            step_config=step_config
        )
        audit_results_mock.return_value = "pass"
        audit_results_mock.side_effect = sh.ErrorReturnCode('opa', b'mock out', b'mock error')

        result_message, result_return_code = step_implementer._OpenPolicyAgent__audit_attestation(
            workflow_attestation_file_path = "workflow_attestation_file_path",
            workflow_policy_file_path = "workflow_policy_file_path",
            workflow_policy_query =  "fooquery"
        )

        self.assertRegex(result_message, re.compile(
                r"Error evaluating query against data:"
                r".*RAN: opa"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            ))

        self.assertEqual(result_return_code, 1)
