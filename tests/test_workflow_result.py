"""
:return:
"""
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult


class TestStepWorkflowResultTest(BaseTSSCTestCase):
    """
    :return:
    """

    def test_dump(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete(result_file)
        workflow_results = WorkflowResult.load(result_file)

        current_step = StepResult('step1', 'one')
        current_step.add_artifact('version',
                                  'v0.10.0+23',
                                  'semantic version',
                                  )
        # update the workflow by adding current_step
        workflow_results.add_step_result(current_step)
        workflow_results.dump_pickle(result_file)
        workflow_results.dump_yml('tssc-results.yml')
        workflow_results.dump_json('tssc-results.json')

        expected_result = {
            'description': 'semantic version',
            'type': 'str',
            'value': 'v0.10.0+23'
        }
        self.assertEqual(
            workflow_results.get_artifact('version'),
            expected_result
        )

    def test_dump_load(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete(result_file)
        workflow_results = WorkflowResult.load(result_file)

        current_step = StepResult('step1', 'one')
        current_step.add_artifact('version',
                                  'v0.10.0+23',
                                  'semantic version',
                                  )
        # update the workflow by adding current_step
        workflow_results.add_step_result(current_step)
        workflow_results.dump_pickle(result_file)

        test_results = WorkflowResult.load(result_file)
        expected_result = {
            'description': 'semantic version',
            'type': 'str',
            'value': 'v0.10.0+23'
        }
        self.assertEqual(
            test_results.get_artifact('version'),
            expected_result
        )

    def test_dump_load_artifacts(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete(result_file)
        workflow_results = WorkflowResult.load(result_file)

        # add step
        current_step = StepResult('step1', 'one')
        current_step.add_artifact('a', 'A')
        current_step.add_artifact('b', 'B')
        current_step.add_artifact('z', 'Z')
        workflow_results.add_step_result(current_step)

        # add another step
        current_step = StepResult('step2', 'two')
        current_step.add_artifact('c', 'C')
        current_step.add_artifact('d', 'D')
        workflow_results.add_step_result(current_step)

        # dump memory
        workflow_results.dump_pickle(result_file)

        # dump read file
        test_results = WorkflowResult.load(result_file)

        # TEST: look-up FIRST ARTIFACT C (any step)
        expected_result = {
            'description': '',
            'type': 'str',
            'value': 'C'
        }
        self.assertEqual(
            test_results.get_artifact('c'),
            expected_result
        )

        # TEST: look-up ARTIFACTS for a STEP
        expected_result = {
                    'a': {'description': '', 'type': 'str', 'value': 'A'},
                    'b': {'description': '', 'type': 'str', 'value': 'B'},
                    'z': {'description': '', 'type': 'str', 'value': 'Z'}
        }
        self.assertEqual(
            test_results.get_step_artifacts('step1'),
            expected_result
        )

    def test_dump_load_results(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete(result_file)
        workflow_results = WorkflowResult.load(result_file)

        # add step
        current_step = StepResult('step1', 'one')
        current_step.add_artifact('a', 'A', 'aA')
        current_step.add_artifact('b', 'B', 'bB', 'file')
        current_step.add_artifact('z', 'Z')
        workflow_results.add_step_result(current_step)

        # add another step
        current_step = StepResult('step2', 'two')
        current_step.add_artifact('c', 'C')
        current_step.add_artifact('d', 'D')
        current_step.message = 'Failure'
        current_step.success = False
        workflow_results.add_step_result(current_step)

        # dump memory
        workflow_results.dump_pickle(result_file)

        # dump read file
        test_results = WorkflowResult.load(result_file)
        version = test_results.get_step_result('step1')
        expected_result = {
            'step1': {
                'artifacts': {
                    'a': {'description': 'aA', 'type': 'str', 'value': 'A'},
                    'b': {'description': 'bB', 'type': 'file', 'value': 'B'},
                    'z': {'description': '', 'type': 'str', 'value': 'Z'}
                },
                'message': '',
                'step-implementer-name': 'one',
                'step-name': 'step1',
                'success': True
            }
        }
        self.assertEqual(
            test_results.get_step_result('step1'),
            expected_result
        )
        expected_result = {
            'step2': {
                'artifacts': {
                    'c': {'description': '', 'type': 'str', 'value': 'C'},
                    'd': {'description': '', 'type': 'str', 'value': 'D'},
                },
                'message': 'Failure',
                'success': False,
                'step-implementer-name': 'two',
                'step-name': 'step2',
            }
        }
        self.assertEqual(
            test_results.get_step_result('step2'),
            expected_result
        )

