"""
:return:
"""
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult
from testfixtures import TempDirectory
import filecmp

import os

from tssc.exceptions import TSSCException


class TestStepWorkflowResultTest(BaseTSSCTestCase):
    """
    :return:
    """
    def setup_test(self):
        step_result1 = StepResult('step1', 'sub1', 'implementer1')
        step_result1.add_artifact('artifact1', 'value1', 'description1', 'type1')
        step_result1.add_artifact('artifact2', 'value2')

        step_result2 = StepResult('step2', 'sub2', 'implementer2')
        step_result2.add_artifact('artifact3', 'value3', 'description3', 'type3')
        step_result2.add_artifact('artifact4', 'value4', 'description4', 'type4')

        wfr = WorkflowResult()
        wfr.add_step_result(step_result1)
        wfr.add_step_result(step_result2)

        return wfr

    def test_get_artifact_without_step(self):
        expected_artifact = {
            'description': 'description1',
            'type': 'type1',
            'value': 'value1'
        }
        wfr = self.setup_test()
        self.assertEqual(wfr.get_artifact('artifact1'), expected_artifact)
    
    def test_get_artifact_with_step(self):
        expected_artifact = {
            'description': 'description3',
            'type': 'type3',
            'value': 'value3'
        }
        wfr = self.setup_test()
        self.assertEqual(wfr.get_artifact('artifact3', 'step2', 'sub2'), expected_artifact)

    def test_get_step_result(self):
        expected_step_result = {
            'tssc-results': {
                'step1': {
                    'sub1': {
                        'sub-step-implementer-name': 'implementer1', 
                        'success': True, 
                        'message': '', 
                        'artifacts': {
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
                    }
                }
            }
        }
        wfr = self.setup_test()
        self.assertEqual(wfr.get_step_result('step1'), expected_step_result)
    
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
                            'artifact1': {
                                'description': 'description1', 
                                'type': 'type1', 
                                'value': 'value1'
                            }, 
                            'artifact2': {
                                'description': '', 
                                'type': 'str', 
                                'value': 'value2'
                            },
                            'newartifact': {
                                'description': 'newdescription', 
                                'type': 'newtype', 
                                'value': 'newvalue'
                            }
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
            wfr.add_step_result("NotAStepResult")
    
    # def test_search_for_artifact(self):
    
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
                    description: ''
                    type: str
                    value: value2
            message: ''
            sub-step-implementer-name: implementer1
            success: true
    step2:
        sub2:
            artifacts:
                artifact3:
                    description: description3
                    type: type3
                    value: value3
                artifact4:
                    description: description4
                    type: type4
                    value: value4
            message: ''
            sub-step-implementer-name: implementer2
            success: true
"""
        wfr = self.setup_test()
        with TempDirectory() as temp_dir:
            yml_file = temp_dir.path + '/test-results.yml'
            wfr.write_results_to_yml_file(yml_file)

            expected_yml_file = temp_dir.path + '/test-expected-results.yml'
            with open(expected_yml_file, 'w') as f:
                f.write(expected_yml_result)

            self.assertTrue(filecmp.cmp(yml_file, expected_yml_file))
    
    def test_write_results_to_yml_file_exception(self):
        wfr = self.setup_test()

        with self.assertRaisesRegex(
                RuntimeError,
                r"error dumping"):
            wfr.write_results_to_yml_file("NotAStepResult/dir/test.yml")
    
#     def test_write_results_to_json_file(self):
#         expected_json_result = """{
#     "tssc-results": {
#         "step1": {
#             "sub1": {
#                 "sub-step-implementer-name": "implementer1",
#                 "success": true,
#                 "message": "",
#                 "artifacts": {
#                     "artifact1": {
#                         "description": "description1",
#                         "type": "type1",
#                         "value": "value1"
#                     },
#                     "artifact2": {
#                         "description": "",
#                         "type": "str",
#                         "value": "value2"
#                     }
#                 }
#             }
#         },
#         "step2": {
#             "sub2": {
#                 "sub-step-implementer-name": "implementer2",
#                 "success": true,
#                 "message": "",
#                 "artifacts": {
#                     "artifact3": {
#                         "description": "description3",
#                         "type": "type3",
#                         "value": "value3"
#                     },
#                     "artifact4": {
#                         "description": "description4",
#                         "type": "type4",
#                         "value": "value4"
#                     }
#                 }
#             }
#         }
#     }
# }
# """
#         wfr = self.setup_test()
#         with TempDirectory() as temp_dir:
#             json_file = temp_dir.path + '/test-results.json'
#             wfr.write_results_to_json_file(json_file)

#             expected_json_file = temp_dir.path + '/test-expected-results.json'
#             with open(expected_json_file, 'w') as f:
#                 f.write("hello")
#                 f.write(expected_json_result)

#                 print('xxxxxxxxxxxxxxxxxxxxxxxxxxx')
#                 print(open(json_file).read())
#                 print('xxxxxxxxxxxxxxxxxxxxxxxxxxx')
#                 print(open(expected_json_file).read())
#                 print('xxxxxxxxxxxxxxxxxxxxxxxxxxx')

#             self.assertTrue(filecmp.cmp(json_file, expected_json_file))
        
    def test_write_results_to_json_file_exception(self):
        wfr = self.setup_test()

        with self.assertRaisesRegex(
                RuntimeError,
                r"error dumping"):
            wfr.write_results_to_json_file("NotAStepResult/dir/test.json")

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
