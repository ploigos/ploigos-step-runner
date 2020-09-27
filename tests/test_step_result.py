"""
  Test ResultStep
"""
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tssc.step_result import StepResult


class TestStepResultTest(BaseTSSCTestCase):

    def test_step_name(self):
        step_result_expected = 'step1'
        step_result = StepResult('step1', 'implementer1')
        self.assertEqual(step_result.step_name, step_result_expected)

    def test_sub_step_name(self):
        expected = 'sub1'
        step_result = StepResult('step1', 'implementer1', 'sub1')
        self.assertEqual(step_result.sub_step_name, expected)

    def test_add_artifact(self):
        step_result_expected = {
            'step1': {
                'step-name': 'step1',
                'step-implementer-name': 'implementer1',
                'sub-step-name': '',
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

    def test_get_artifact(self):
        step_result_expected = {
            'description': 'description1',
            'type': 'type1',
            'value': 'value1'
        }
        step_result = StepResult('step1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1', 'type1')
        self.assertEqual(step_result.get_artifact('artifact1'), step_result_expected)

    def test_get_artifacts_property(self):
        step_result_expected = {
            'artifact1': {
                'description': 'description1',
                'type': 'type1',
                'value': 'value1'
            },
            'artifact2': {
                'description': '',
                'type': 'str',
                'value': 'value2'
            }
        }
        step_result = StepResult('step1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1', 'type1')
        step_result.add_artifact('artifact2', 'value2')
        self.assertEqual(step_result.artifacts, step_result_expected)

    def test_add_duplicate(self):
        step_result_expected = {
            'artifact1': {
                'description': 'description1',
                'type': 'type1',
                'value': 'value1'
            },
            'artifact2': {
                'description': '',
                'type': 'str',
                'value': 'lastonewins'
            }
        }
        step_result = StepResult('step1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1', 'type1')
        step_result.add_artifact('artifact2', 'here')
        step_result.add_artifact('artifact2', 'andhere')
        step_result.add_artifact('artifact2', 'lastonewins')
        self.assertEqual(step_result.artifacts, step_result_expected)
