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

    def test_get_step_result(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete_file(result_file)
        workflow_results = WorkflowResult.load_from_pickle_file(result_file)

        current_step = StepResult('step1', 'one', 'sub1')
        current_step.add_artifact('a', 'str', 'A')
        current_step.add_artifact('b', 'str', 'B')
        workflow_results.add_step_result(current_step)
        workflow_results.write_to_pickle_file(result_file)

        # NEXT TEST
        test_results = WorkflowResult.load_from_pickle_file(result_file)
        expected_result = {
            'tssc-results': {
                'step1': {
                    'step-name': 'step1',
                    'sub-step-name': 'one',
                    'sub-step-implementer-name': 'sub1',
                    'success': True, 'message': '',
                    'artifacts': {
                        'a': {'description': 'A', 'type': 'str', 'value': 'str'},
                        'b': {'description': 'B', 'type': 'str', 'value': 'str'},
                    }
                }
            }
        }
        self.assertEqual(
            test_results.get_step_result('step1'),
            expected_result
        )

        # test merge
        current_step = StepResult('step1', 'one', 'sub1')
        current_step.add_artifact('c', 'str', 'C')
        current_step.add_artifact('d', 'str', 'D')
        expected_result = {
            'tssc-results': {
                'step1': {
                    'step-name': 'step1',
                    'sub-step-name': 'one',
                    'sub-step-implementer-name': 'sub1',
                    'success': True, 'message': '',
                    'artifacts': {
                        'a': {'description': 'A', 'type': 'str', 'value': 'str'},
                        'b': {'description': 'B', 'type': 'str', 'value': 'str'},
                        'c': {'description': 'C', 'type': 'str', 'value': 'str'},
                        'd': {'description': 'D', 'type': 'str', 'value': 'str'},
                    }
                }
            }
        }
        test_results.add_step_result(current_step)
        self.assertEqual(
            expected_result,
            test_results.get_step_result('step1')
        )

    def test_get_artifact(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete_file(result_file)
        workflow_results = WorkflowResult.load_from_pickle_file(result_file)

        # add step
        current_step = StepResult('step1', 'one', 'sub1')
        current_step.add_artifact('a', 'A')
        current_step.add_artifact('b', 'B')
        current_step.add_artifact('z', 'Z')
        workflow_results.add_step_result(current_step)

        # add another step
        current_step = StepResult('step2', 'two', 'sub2')
        current_step.add_artifact('c', 'C')
        current_step.add_artifact('d', 'D')
        workflow_results.add_step_result(current_step)

        # dump memory
        workflow_results.write_to_pickle_file(result_file)

        # dump read file
        test_results = WorkflowResult.load_from_pickle_file(result_file)

        # TEST: look-up FIRST ARTIFACT C (any step)
        expected_result = {'description': '', 'type': 'str', 'value': 'C'}
        self.assertEqual(
            test_results.get_artifact(artifact='c', step_name='step2'),
            expected_result
        )
        self.assertEqual(
            test_results.get_artifact(artifact='c'),
            expected_result
        )

        # TEST: look-up something not there
        expected_result = None
        self.assertEqual(
            test_results.get_artifact(artifact='c', step_name='bad'),
            expected_result
        )
        self.assertEqual(
            test_results.get_artifact(artifact='k'),
            expected_result
        )

    def test_more(self):
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete_file(result_file)
        workflow_results = WorkflowResult.load_from_pickle_file(result_file)

        # add step
        current_step = StepResult('step1', 'one', 'sub1')
        current_step.add_artifact('a', 'A', 'aA')
        current_step.add_artifact('b', 'B', 'bB', 'file')
        current_step.add_artifact('z', 'Z')
        workflow_results.add_step_result(current_step)

        # add another step
        current_step = StepResult('step2', 'two', 'sub2')
        current_step.add_artifact('c', 'C')
        current_step.add_artifact('d', 'D')
        current_step.message = 'Failure'
        current_step.success = False
        workflow_results.add_step_result(current_step)

        # dump memory
        workflow_results.write_to_pickle_file(result_file)

        # dump read file
        test_results = WorkflowResult.load_from_pickle_file(result_file)
        expected_result = {
            'tssc-results': {
                'step1': {
                    'step-name': 'step1',
                    'sub-step-name': 'one',
                    'sub-step-implementer-name': 'sub1',
                    'success': True,
                    'message': '',
                    'artifacts': {
                        'a': {'description': 'aA', 'type': 'str', 'value': 'A'},
                        'b': {'description': 'bB', 'type': 'file', 'value': 'B'},
                        'z': {'description': '', 'type': 'str', 'value': 'Z'}
                    },
                }
            }
        }
        self.assertEqual(
            test_results.get_step_result('step1'),
            expected_result
        )
        self.assertEqual(
            test_results.get_artifact('z'),
            {'description': '', 'type': 'str', 'value': 'Z'}
        )
        expected_result = {
            'tssc-results': {
                'step2': {
                    'step-name': 'step2',
                    'sub-step-name': 'two',
                    'sub-step-implementer-name': 'sub2',
                    'success': False,
                    'message': 'Failure',
                    'artifacts': {
                        'c': {'description': '', 'type': 'str', 'value': 'C'},
                        'd': {'description': '', 'type': 'str', 'value': 'D'},
                    },
                }
            }
        }
        self.assertEqual(
            test_results.get_step_result('step2'),
            expected_result
        )
        self.assertEqual(
            test_results.get_artifact('c'),
            {'description': '', 'type': 'str', 'value': 'C'}
        )
