# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import filecmp
import pickle

from ploigos_step_runner import StepResult, WorkflowResult
from ploigos_step_runner.exceptions import StepRunnerException
from testfixtures import TempDirectory
from tests.helpers.base_test_case import BaseTestCase


def setup_test():
    step_result1 = StepResult('step1', 'sub1', 'implementer1')
    step_result1.add_artifact('artifact1', 'value1', 'description1')
    step_result1.add_artifact('artifact2', 'value2', 'description2')
    step_result1.add_artifact('artifact3', 'value3')
    step_result1.add_artifact('artifact4', False)
    step_result1.add_artifact('same-artifact-all-env-and-no-env', 'result1')

    step_result1.add_evidence('evidence1', 'value1', 'description1')
    step_result1.add_evidence('evidence2', 'value2', 'description2')
    step_result1.add_evidence('evidence3', 'value3')
    step_result1.add_evidence('evidence4', False)
    step_result1.add_evidence('same-evidence-all-env-and-no-env', 'result1')


    step_result2 = StepResult('step2', 'sub2', 'implementer2')
    step_result2.add_artifact('artifact1', True)
    step_result2.add_artifact('artifact2', False)
    step_result2.add_artifact('artifact5', 'value5')

    step_result2.add_evidence('evidence1', True)
    step_result2.add_evidence('evidence2', False)
    step_result2.add_evidence('evidence5', 'value5')

    step_result3 = StepResult('deploy', 'deploy-sub', 'helm', 'dev')
    step_result3.add_artifact('same-artifact-diff-env', 'value-dev-env')
    step_result3.add_artifact('unique-artifact-to-step-and-environment-1', 'value1-dev-env')
    step_result3.add_artifact('same-artifact-all-env-and-no-env', 'result3-dev-env')

    step_result3.add_evidence('same-evidence-diff-env', 'value-dev-env')
    step_result3.add_evidence('unique-evidence-to-step-and-environment-1', 'value1-dev-env')
    step_result3.add_evidence('same-evidence-all-env-and-no-env', 'result3-dev-env')

    step_result4 = StepResult('deploy', 'deploy-sub', 'helm', 'test')
    step_result4.add_artifact('artifact1', True)
    step_result4.add_artifact('artifact2', False)
    step_result4.add_artifact('artifact5', 'value5')
    step_result4.add_artifact('same-artifact-diff-env', 'value-test-env')
    step_result4.add_artifact('unique-artifact-to-step-and-environment-2', 'value2-test-env')
    step_result4.add_artifact('same-artifact-all-env-and-no-env', 'result4-test-env')

    step_result4.add_evidence('evidence1', True)
    step_result4.add_evidence('evidence2', False)
    step_result4.add_evidence('evidence5', 'value5')
    step_result4.add_evidence('same-evidence-diff-env', 'value-test-env')
    step_result4.add_evidence('unique-evidence-to-step-and-environment-2', 'value2-test-env')
    step_result4.add_evidence('same-evidence-all-env-and-no-env', 'result4-test-env')

    wfr = WorkflowResult()
    wfr.add_step_result(step_result1)
    wfr.add_step_result(step_result2)
    wfr.add_step_result(step_result3)
    wfr.add_step_result(step_result4)

    return wfr


def setup_test_sub_steps():
    step_result1 = StepResult('step1', 'sub1', 'implementer1')
    step_result1.add_artifact('artifact1', 'value1', 'description1')
    step_result1.add_artifact('artifact2', 'value2', 'description2')
    step_result1.add_artifact('artifact3', 'value3')
    step_result1.add_artifact('artifact4', False)

    step_result1.add_evidence('evidence1', 'value1', 'description1')
    step_result1.add_evidence('evidence2', 'value2', 'description2')
    step_result1.add_evidence('evidence3', 'value3')
    step_result1.add_evidence('evidence4', False)

    step_result2 = StepResult('step1', 'sub2', 'implementer2')
    step_result2.add_artifact('artifact1', True)
    step_result2.add_artifact('artifact2', False)
    step_result2.add_artifact('artifact5', 'value5')

    step_result2.add_evidence('evidence1', True)
    step_result2.add_evidence('evidence2', False)
    step_result2.add_evidence('evidence5', 'value5')

    wfr = WorkflowResult()
    wfr.add_step_result(step_result1)
    wfr.add_step_result(step_result2)

    return wfr


class TestStepWorkflowResultTest(BaseTestCase):
    """
    :return:
    """

    def test_get_artifact_value_without_step(self):
        wfr = setup_test()

        expected_artifact = True
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='artifact1')
        )

        expected_artifact = 'value5'
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='artifact5')
        )

        expected_artifact = False
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='artifact4')
        )

        expected_artifact = None
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='bad')
        )

    def test_get_evidence_value_without_step(self):
        wfr = setup_test()

        expected_evidence = 'value1'
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='evidence1')
        )

        expected_evidence = 'value5'
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='evidence5')
        )

        expected_evidence = False
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='evidence4')
        )

        expected_evidence = None
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='bad')
        )

    def test_get_artifact_value_with_step(self):
        wfr = setup_test()

        expected_artifact = 'value1'
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='artifact1', step_name='step1')
        )
        expected_artifact = False
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='artifact2', step_name='step2')
        )
        expected_artifact = None
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='artifact2', step_name='bad')
        )

    def test_get_evidence_value_with_step(self):
        wfr = setup_test()

        expected_evidence = 'value1'
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='evidence1', step_name='step1')
        )
        expected_evidence = False
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='evidence2', step_name='step2')
        )
        expected_evidence = None
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='evidence2', step_name='bad')
        )

    def test_get_artifact_value_with_step_sub_step(self):
        wfr = setup_test()

        expected_artifact = 'value1'
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='artifact1', step_name='step1', sub_step_name='sub1')
        )
        expected_artifact = False
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='artifact2', step_name='step2', sub_step_name='sub2')
        )
        expected_artifact = None
        self.assertEqual(
            expected_artifact,
            wfr.get_artifact_value(artifact='artifact2', step_name='step2', sub_step_name='bad')
        )

    def test_get_evidence_value_with_step_sub_step(self):
        wfr = setup_test()

        expected_evidence = 'value1'
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='evidence1', step_name='step1', sub_step_name='sub1')
        )
        expected_evidence = False
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='evidence2', step_name='step2', sub_step_name='sub2')
        )
        expected_evidence = None
        self.assertEqual(
            expected_evidence,
            wfr.get_evidence_value(evidence='evidence2', step_name='step2', sub_step_name='bad')
        )

    def test_get_artifact_value_in_step_executed_in_different_environments_and_no_environment(self):
        wfr = setup_test()

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='same-artifact-all-env-and-no-env'
            ),
            'result4-test-env'
        )

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='same-artifact-all-env-and-no-env',
                environment='dev'
            ),
            'result3-dev-env'
        )

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='same-artifact-all-env-and-no-env',
                environment='test'
            ),
            'result4-test-env'
        )

    def test_get_evidence_value_in_step_executed_in_different_environments_and_no_environment(self):
        wfr = setup_test()

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='same-evidence-all-env-and-no-env'
            ),
            'result1'
        )

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='same-evidence-all-env-and-no-env',
                environment='dev'
            ),
            'result3-dev-env'
        )

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='same-evidence-all-env-and-no-env',
                environment='test'
            ),
            'result4-test-env'
        )

    def test_get_artifact_value_in_step_executed_in_different_environments(self):
        wfr = setup_test()

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='same-artifact-diff-env'
            ),
            'value-test-env'
        )

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='same-artifact-diff-env',
                environment='dev'
            ),
            'value-dev-env'
        )

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='same-artifact-diff-env',
                environment='test'
            ),
            'value-test-env'
        )

    def test_get_evidence_value_in_step_executed_in_different_environments(self):
        wfr = setup_test()

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='same-evidence-diff-env'
            ),
            'value-dev-env'
        )

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='same-evidence-diff-env',
                environment='dev'
            ),
            'value-dev-env'
        )

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='same-evidence-diff-env',
                environment='test'
            ),
            'value-test-env'
        )

    def test_get_artifact_value_unique_to_environment(self):
        wfr = setup_test()

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='unique-artifact-to-step-and-environment-1'
            ),
            'value1-dev-env'
        )

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='unique-artifact-to-step-and-environment-1',
                environment='dev'
            ),
            'value1-dev-env'
        )

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='unique-artifact-to-step-and-environment-1',
                environment='test'
            ),
            None
        )

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='unique-artifact-to-step-and-environment-2'
            ),
            'value2-test-env'
        )

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='unique-artifact-to-step-and-environment-2',
                environment='dev'
            ),
            None
        )

        self.assertEqual(
            wfr.get_artifact_value(
                artifact='unique-artifact-to-step-and-environment-2',
                environment='test'
            ),
            'value2-test-env'
        )

    def test_get_evidence_value_unique_to_environment(self):
        wfr = setup_test()

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='unique-evidence-to-step-and-environment-1'
            ),
            'value1-dev-env'
        )

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='unique-evidence-to-step-and-environment-1',
                environment='dev'
            ),
            'value1-dev-env'
        )

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='unique-evidence-to-step-and-environment-1',
                environment='test'
            ),
            None
        )

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='unique-evidence-to-step-and-environment-2'
            ),
            'value2-test-env'
        )

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='unique-evidence-to-step-and-environment-2',
                environment='dev'
            ),
            None
        )

        self.assertEqual(
            wfr.get_evidence_value(
                evidence='unique-evidence-to-step-and-environment-2',
                environment='test'
            ),
            'value2-test-env'
        )

    def test_add_step_result_duplicate_no_env(self):
        duplicate_step_result = StepResult('step1', 'sub1', 'implementer1')
        duplicate_step_result.add_artifact('newartifact', 'newvalue', 'newdescription')
        duplicate_step_result.add_evidence('newevidence', 'newvalue', 'newdescription')

        wfr = setup_test()

        with self.assertRaisesRegex(
            StepRunnerException,
            r"Can not add duplicate StepResult for step \(step1\),"
            r" sub step \(sub1\), and environment \(None\)."
        ):
            wfr.add_step_result(duplicate_step_result)

    def test_add_step_result_duplicate_with_env(self):
        duplicate_step_result = StepResult('deploy', 'deploy-sub', 'helm', 'dev')
        duplicate_step_result.add_artifact('newartifact', 'newvalue', 'newdescription')
        duplicate_step_result.add_evidence('newevidence', 'newvalue', 'newdescription')

        wfr = setup_test()

        with self.assertRaisesRegex(
            StepRunnerException,
            r"Can not add duplicate StepResult for step \(deploy\),"
            r" sub step \(deploy-sub\), and environment \(dev\)."
        ):
            wfr.add_step_result(duplicate_step_result)

    def test_add_step_result_exception(self):
        wfr = setup_test()

        with self.assertRaisesRegex(
                StepRunnerException,
                r"expect StepResult instance type"):
            wfr.add_step_result(step_result="bad")

    def test_write_results_to_yml_file(self):
        expected_yml_result = """step-runner-results:
    step1:
        sub1:
            artifacts:
            -   description: description1
                name: artifact1
                value: value1
            -   description: description2
                name: artifact2
                value: value2
            -   description: ''
                name: artifact3
                value: value3
            -   description: ''
                name: artifact4
                value: false
            evidence:
            -   description: description1
                name: evidence1
                value: value1
            -   description: description2
                name: evidence2
                value: value2
            -   description: ''
                name: evidence3
                value: value3
            -   description: ''
                name: evidence4
                value: false
            message: ''
            sub-step-implementer-name: implementer1
            success: true
        sub2:
            artifacts:
            -   description: ''
                name: artifact1
                value: true
            -   description: ''
                name: artifact2
                value: false
            -   description: ''
                name: artifact5
                value: value5
            evidence:
            -   description: ''
                name: evidence1
                value: true
            -   description: ''
                name: evidence2
                value: false
            -   description: ''
                name: evidence5
                value: value5
            message: ''
            sub-step-implementer-name: implementer2
            success: true
"""
        wfr = setup_test_sub_steps()
        with TempDirectory() as temp_dir:
            yml_file = temp_dir.path + '/test-results.yml'
            wfr.write_results_to_yml_file(yml_file)

            expected_yml_file = temp_dir.path + '/test-expected-results.yml'

            with open(yml_file, 'r') as actual:
                self.assertEqual(actual.read(), expected_yml_result)

    def test_write_results_to_yml_file_exception(self):
        wfr = setup_test()

        with self.assertRaises(RuntimeError):
            wfr.write_results_to_yml_file('/NotAStepResult/dir/test.yml')

    def test_write_results_to_json_file(self):
        expected_json_result = """{
    "step-runner-results": {
        "step1": {
            "sub1": {
                "sub-step-implementer-name": "implementer1",
                "success": true,
                "message": "",
                "artifacts": [
                    {
                        "name": "artifact1",
                        "value": "value1",
                        "description": "description1"
                    },
                    {
                        "name": "artifact2",
                        "value": "value2",
                        "description": "description2"
                    },
                    {
                        "name": "artifact3",
                        "value": "value3",
                        "description": ""
                    },
                    {
                        "name": "artifact4",
                        "value": false,
                        "description": ""
                    },
                    {
                        "name": "same-artifact-all-env-and-no-env",
                        "value": "result1",
                        "description": ""
                    }
                ],
                "evidence": [
                    {
                        "name": "evidence1",
                        "value": "value1",
                        "description": "description1"
                    },
                    {
                        "name": "evidence2",
                        "value": "value2",
                        "description": "description2"
                    },
                    {
                        "name": "evidence3",
                        "value": "value3",
                        "description": ""
                    },
                    {
                        "name": "evidence4",
                        "value": false,
                        "description": ""
                    },
                    {
                        "name": "same-evidence-all-env-and-no-env",
                        "value": "result1",
                        "description": ""
                    }
                ]
            }
        },
        "step2": {
            "sub2": {
                "sub-step-implementer-name": "implementer2",
                "success": true,
                "message": "",
                "artifacts": [
                    {
                        "name": "artifact1",
                        "value": true,
                        "description": ""
                    },
                    {
                        "name": "artifact2",
                        "value": false,
                        "description": ""
                    },
                    {
                        "name": "artifact5",
                        "value": "value5",
                        "description": ""
                    }
                ],
                "evidence": [
                    {
                        "name": "evidence1",
                        "value": true,
                        "description": ""
                    },
                    {
                        "name": "evidence2",
                        "value": false,
                        "description": ""
                    },
                    {
                        "name": "evidence5",
                        "value": "value5",
                        "description": ""
                    }
                ]
            }
        },
        "dev": {
            "deploy": {
                "deploy-sub": {
                    "sub-step-implementer-name": "helm",
                    "success": true,
                    "message": "",
                    "artifacts": [
                        {
                            "name": "same-artifact-diff-env",
                            "value": "value-dev-env",
                            "description": ""
                        },
                        {
                            "name": "unique-artifact-to-step-and-environment-1",
                            "value": "value1-dev-env",
                            "description": ""
                        },
                        {
                            "name": "same-artifact-all-env-and-no-env",
                            "value": "result3-dev-env",
                            "description": ""
                        }
                    ],
                    "evidence": [
                        {
                            "name": "same-evidence-diff-env",
                            "value": "value-dev-env",
                            "description": ""
                        },
                        {
                            "name": "unique-evidence-to-step-and-environment-1",
                            "value": "value1-dev-env",
                            "description": ""
                        },
                        {
                            "name": "same-evidence-all-env-and-no-env",
                            "value": "result3-dev-env",
                            "description": ""
                        }
                    ]
                }
            }
        },
        "test": {
            "deploy": {
                "deploy-sub": {
                    "sub-step-implementer-name": "helm",
                    "success": true,
                    "message": "",
                    "artifacts": [
                        {
                            "name": "artifact1",
                            "value": true,
                            "description": ""
                        },
                        {
                            "name": "artifact2",
                            "value": false,
                            "description": ""
                        },
                        {
                            "name": "artifact5",
                            "value": "value5",
                            "description": ""
                        },
                        {
                            "name": "same-artifact-diff-env",
                            "value": "value-test-env",
                            "description": ""
                        },
                        {
                            "name": "unique-artifact-to-step-and-environment-2",
                            "value": "value2-test-env",
                            "description": ""
                        },
                        {
                            "name": "same-artifact-all-env-and-no-env",
                            "value": "result4-test-env",
                            "description": ""
                        }
                    ],
                    "evidence": [
                        {
                            "name": "evidence1",
                            "value": true,
                            "description": ""
                        },
                        {
                            "name": "evidence2",
                            "value": false,
                            "description": ""
                        },
                        {
                            "name": "evidence5",
                            "value": "value5",
                            "description": ""
                        },
                        {
                            "name": "same-evidence-diff-env",
                            "value": "value-test-env",
                            "description": ""
                        },
                        {
                            "name": "unique-evidence-to-step-and-environment-2",
                            "value": "value2-test-env",
                            "description": ""
                        },
                        {
                            "name": "same-evidence-all-env-and-no-env",
                            "value": "result4-test-env",
                            "description": ""
                        }
                    ]
                }
            }
        }
    }
}"""
        wfr = setup_test()
        with TempDirectory() as temp_dir:
            json_file_path = temp_dir.path + '/test-results.json'
            wfr.write_results_to_json_file(json_file_path)

            with open(json_file_path, 'r') as actual_json_file:
                json_file_contents = actual_json_file.read()
                self.assertEqual(json_file_contents, expected_json_result)

    def test_write_results_to_json_file_exception(self):
        wfr = setup_test()

        # the sub-folders will be created
        # with TempDirectory() as temp_dir:
        #     wfr.write_results_to_json_file(f'{temp_dir.path}/NotAStepResult/dir/test.json')
        with self.assertRaises(
                RuntimeError):
            wfr.write_results_to_json_file('/NotAStepResult/dir/test.json')

    def test_load_from_pickle_file_no_file(self):
        pickle_wfr = WorkflowResult.load_from_pickle_file('test.pkl')
        expected_wfr = WorkflowResult()
        self.assertEqual(
            pickle_wfr._WorkflowResult__get_all_step_results_dict(),
            expected_wfr._WorkflowResult__get_all_step_results_dict()
        )

    def test_load_from_pickle_file_empty_file(self):
        with TempDirectory() as temp_dir:
            pickle_file = temp_dir.path + '/test.pkl'
            open(pickle_file, 'a').close()
            pickle_wfr = WorkflowResult.load_from_pickle_file(pickle_file)
            expected_wfr = WorkflowResult()
            self.assertEqual(
                pickle_wfr._WorkflowResult__get_all_step_results_dict(),
                expected_wfr._WorkflowResult__get_all_step_results_dict()
            )

    def test_load_from_pickle_file_no_workflowresult(self):
        with TempDirectory() as temp_dir:
            pickle_file = temp_dir.path + '/test.pkl'

            not_wfr = {"step1": "value1", "step2": "value2"}
            with open(pickle_file, 'wb') as file:
                pickle.dump(not_wfr, file)

            with self.assertRaisesRegex(
                    StepRunnerException,
                    f'error {pickle_file} has invalid data'):
                WorkflowResult.load_from_pickle_file(pickle_file)

    def test_load_from_pickle_file_yes_workflow_result(self):
        with TempDirectory() as temp_dir:
            pickle_file = temp_dir.path + '/test.pkl'
            expected_wfr = setup_test()
            expected_wfr.write_to_pickle_file(pickle_file)
            pickle_wfr = WorkflowResult.load_from_pickle_file(pickle_file)

    def test_load_from_pickle_file_exception(self):
        with TempDirectory() as temp_dir:
            pickle_file_name = temp_dir.path + '/test.pkl'

            pickle_file = open(pickle_file_name, 'w+')
            pickle_file.write("This is not a Workflow Result.")
            pickle_file.close()

            with self.assertRaises(
                    StepRunnerException):
                WorkflowResult.load_from_pickle_file(pickle_file)

    def test_write_to_pickle_file(self):
        wfr = setup_test()
        with self.assertRaises(
                RuntimeError):
            wfr.write_to_pickle_file(None)
