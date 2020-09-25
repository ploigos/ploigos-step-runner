from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tssc.step_result import StepResult

class TestStepResultTest(BaseTSSCTestCase):

    def test_add_artifact(self):
        step_result_expected = {
            'step1': {
                'step-name': 'step1',
                'step-implementer-name': 'implementer1',
                'success': True,
                'message': '',
                'artifacts': {
                    'artifact1': {
                        'description': 'description1',
                        'type': 'type1',
                        'value': 'value1'
                    },
                    'artifact2': {
                        'description': 'description2',
                        'type': 'type2',
                        'value': 'value2'
                    },
                    'artifact3': {
                        'description': '',
                        'type': 'str',
                        'value': 'value3'
                    }
                }
            }
        }
        step_result = StepResult('step1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1', 'type1')
        step_result.add_artifact('artifact2', 'value2', 'description2', 'type2')
        step_result.add_artifact('artifact3', 'value3')
        self.assertEqual(step_result.get_step_result(), step_result_expected)

    def test_get_specific_artifact(self):
        step_result_expected = {
            'description': 'description1',
            'type': 'type1',
            'value': 'value1'
        }
        step_result = StepResult('step1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1', 'type1')
        self.assertEqual(step_result.get_artifact('artifact1'), step_result_expected)
