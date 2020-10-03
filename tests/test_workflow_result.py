"""
:return:
"""
import filecmp
from testfixtures import TempDirectory

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult
from tssc.exceptions import TSSCException


class TestStepWorkflowResultTest(BaseTSSCTestCase):
    """
    :return:
    """

    def setup_test(self):
        step_result1 = StepResult('step1', 'sub1', 'implementer1')
        step_result1.add_artifact('artifact1', 'value1', 'description1', 'type1')
        step_result1.add_artifact('artifact2', 'value2', 'description2')
        step_result1.add_artifact('artifact3', 'value3')
        step_result1.add_artifact('artifact4', False)

        step_result2 = StepResult('step2', 'sub2', 'implementer2')
        step_result2.add_artifact('artifact1', True)
        step_result2.add_artifact('artifact2', False)
        step_result2.add_artifact('artifact5', 'value5')

        wfr = WorkflowResult()
        wfr.add_step_result(step_result1)
        wfr.add_step_result(step_result2)

        return wfr

    def test_get_artifact_value_without_step(self):
        wfr = self.setup_test()

        expected_artifact = 'value1'
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

    def test_get_artifact_value_with_step(self):
        wfr = self.setup_test()

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

    def test_get_artifact_value_with_step_sub_step(self):
        wfr = self.setup_test()

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

    def test_get_step_result(self):
        wfr = self.setup_test()
        expected_step_result = {
            'tssc-results': {
                'step1': {
                    'sub1': {
                        'sub-step-implementer-name': 'implementer1',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'artifact1': {'description': 'description1', 'type': 'type1', 'value': 'value1'},
                            'artifact2': {'description': 'description2', 'type': 'str', 'value': 'value2'},
                            'artifact3': {'description': '', 'type': 'str', 'value': 'value3'},
                            'artifact4': {'description': '', 'type': 'bool', 'value': False}
                        }
                    }
                }
            }
        }
        self.assertEqual(
            expected_step_result,
            wfr.get_step_result('step1')
        )

    def test_add_step_result_new(self):
        expected_step_result = {
            'tssc-results': {
                'teststep': {
                    'testsub': {
                        'sub-step-implementer-name': 'testimplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {}
                    }
                }
            }
        }
        test_step_result = StepResult('teststep', 'testsub', 'testimplementer')
        wfr = self.setup_test()
        wfr.add_step_result(test_step_result)
        self.assertEqual(wfr.get_step_result('teststep'), expected_step_result)

    def test_add_step_result_update(self):
        expected_step_result = {
            'tssc-results': {
                'step1': {
                    'sub1': {
                        'sub-step-implementer-name': 'implementer1',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'artifact1': {'description': 'description1', 'type': 'type1', 'value': 'value1'},
                            'artifact2': {'description': 'description2', 'type': 'str', 'value': 'value2'},
                            'artifact3': {'description': '', 'type': 'str', 'value': 'value3'},
                            'artifact4': {'description': '', 'type': 'bool', 'value': False},
                            'newartifact': {'description': 'newdescription', 'type': 'newtype', 'value': 'newvalue'}
                        }
                    }
                }
            }
        }
        update_step_result = StepResult('step1', 'sub1', 'implementer1')
        update_step_result.add_artifact('newartifact', 'newvalue', 'newdescription', 'newtype')

        wfr = self.setup_test()
        wfr.add_step_result(update_step_result)
        self.assertEqual(wfr.get_step_result('step1'), expected_step_result)

    def test_add_step_result_exception(self):
        wfr = self.setup_test()

        with self.assertRaisesRegex(
                TSSCException,
                r"expect StepResult instance type"):
            wfr.add_step_result(step_result="bad")

    def test_write_results_to_yml_file(self):
        expected_yml_result = """tssc-results:
    step1:
        sub1:
            artifacts:
                artifact1:
                    description: description1
                    type: type1
                    value: value1
                artifact2:
                    description: description2
                    type: str
                    value: value2
                artifact3:
                    description: ''
                    type: str
                    value: value3
                artifact4:
                    description: ''
                    type: bool
                    value: false
            message: ''
            sub-step-implementer-name: implementer1
            success: true
    step2:
        sub2:
            artifacts:
                artifact1:
                    description: ''
                    type: bool
                    value: true
                artifact2:
                    description: ''
                    type: bool
                    value: false
                artifact5:
                    description: ''
                    type: str
                    value: value5
            message: ''
            sub-step-implementer-name: implementer2
            success: true
"""
        wfr = self.setup_test()
        with TempDirectory() as temp_dir:
            yml_file = temp_dir.path + '/test-results.yml'
            wfr.write_results_to_yml_file(yml_file)

            expected_yml_file = temp_dir.path + '/test-expected-results.yml'
            with open(expected_yml_file, 'w') as file:
                file.write(expected_yml_result)

            self.assertTrue(filecmp.cmp(yml_file, expected_yml_file))

    def test_write_results_to_yml_file_exception(self):
        wfr = self.setup_test()

        # the sub-folders will be created
        with TempDirectory() as temp_dir:
            wfr.write_results_to_yml_file(f'{temp_dir.path}/NotAStepResult/dir/test.yml')

    def test_write_results_to_json_file_exception(self):
        wfr = self.setup_test()

        # the sub-folders will be created
        with TempDirectory() as temp_dir:
            wfr.write_results_to_json_file(f'{temp_dir.path}/NotAStepResult/dir/test.json')

    def test_load_from_pickle_file_no_file(self):
        pickle_wfr = WorkflowResult.load_from_pickle_file('test.pkl')
        expected_wfr = WorkflowResult()
        self.assertEqual(pickle_wfr.get_all_step_results(), expected_wfr.get_all_step_results())

    def test_load_from_pickle_file_empty_file(self):
        with TempDirectory() as temp_dir:
            pickle_file = temp_dir.path + '/test.pkl'
            open(pickle_file, 'a').close()
            pickle_wfr = WorkflowResult.load_from_pickle_file(pickle_file)
            expected_wfr = WorkflowResult()
            self.assertEqual(pickle_wfr.get_all_step_results(), expected_wfr.get_all_step_results())

    # def test_write_to_pickle_file(self):

    # def test_delete_file(self):
