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

    def test_search_for_artifact_and_verbose(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete_file(result_file)
        workflow_results = WorkflowResult.load_from_file(result_file)

        current_step = StepResult('step1', 'one')
        current_step.add_artifact('version', 'v0.10.0+23', 'semantic version')
        current_step.add_artifact('a', 'A')
        # update the workflow by adding current_step
        workflow_results.add_step_result(current_step)
        workflow_results.write_to_pickle_file(result_file)
        workflow_results.write_tssc_results_to_yml_file('tssc-results.yml')
        workflow_results.write_tssc_results_to_json_file('tssc-results.json')

        expected_result = {
            'description': 'semantic version',
            'type': 'str',
            'value': 'v0.10.0+23'
        }
        self.assertEqual(
            workflow_results.search_for_artifact('version'),
            expected_result
        )
        expected_result = {
            'step1': {
                'step-implementer-name': 'one',
                'step-name': 'step1',
                'sub-step-name': '',
                'artifacts': {
                    'a': {
                        'description': '',
                        'type': 'str',
                        'value': 'A'
                    },
                    'version': {
                        'description': 'semantic version',
                        'type': 'str',
                        'value': 'v0.10.0+23'
                    }
                },
                'message': '',
                'success': True
            }
        }
        self.assertEqual(
            workflow_results.search_for_artifact('version', True),
            expected_result
        )

    def test_dump_then_load(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete_file(result_file)
        workflow_results = WorkflowResult.load_from_file(result_file)

        current_step = StepResult('step1', 'one')
        current_step.add_artifact('version', 'v0.10.0+23', 'semantic version')
        # update the workflow by adding current_step
        workflow_results.add_step_result(current_step)
        workflow_results.write_to_pickle_file(result_file)

        test_results = WorkflowResult.load_from_file(result_file)
        expected_result = {
            'description': 'semantic version',
            'type': 'str',
            'value': 'v0.10.0+23'
        }
        self.assertEqual(
            test_results.search_for_artifact('version'),
            expected_result
        )

    def test_dump_then_load_search_for_artifact(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete_file(result_file)
        workflow_results = WorkflowResult.load_from_file(result_file)

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
        workflow_results.write_to_pickle_file(result_file)

        # dump read file
        test_results = WorkflowResult.load_from_file(result_file)

        # TEST: look-up FIRST ARTIFACT C (any step)
        expected_result = {
            'description': '',
            'type': 'str',
            'value': 'C'
        }
        self.assertEqual(
            test_results.search_for_artifact('c'),
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

    def test_dump_then_load_from_file_look_at_results(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete_file(result_file)
        workflow_results = WorkflowResult.load_from_file(result_file)

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
        workflow_results.write_to_pickle_file(result_file)

        # dump read file
        test_results = WorkflowResult.load_from_file(result_file)
        expected_result = {
            'tssc-results': {
                'step1': {
                    'artifacts': {
                        'a': {'description': 'aA', 'type': 'str', 'value': 'A'},
                        'b': {'description': 'bB', 'type': 'file', 'value': 'B'},
                        'z': {'description': '', 'type': 'str', 'value': 'Z'}
                    },
                    'message': '',
                    'step-implementer-name': 'one',
                    'step-name': 'step1',
                    'sub-step-name': '',
                    'success': True
                }
            }
        }
        self.assertEqual(
            test_results.get_tssc_step_result('step1'),
            expected_result
        )
        expected_result = {
            'tssc-results': {
                'step2': {
                    'artifacts': {
                        'c': {'description': '', 'type': 'str', 'value': 'C'},
                        'd': {'description': '', 'type': 'str', 'value': 'D'},
                    },
                    'message': 'Failure',
                    'success': False,
                    'step-implementer-name': 'two',
                    'step-name': 'step2',
                    'sub-step-name': '',
                }
            }
        }
        self.assertEqual(
            test_results.get_tssc_step_result('step2'),
            expected_result
        )

    def test_get_all_tssc_step_result(self):
        # testing the contents of the list
        # specifically focused on the order of using the add step

        # start with an empty file
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete_file(result_file)
        workflow_results = WorkflowResult.load_from_file(result_file)

        # create 'empty' steps
        past_1 = StepResult('past_1', 'one')
        past_2 = StepResult('past_2', 'two')
        current_step = StepResult('current_step', 'wip')

        # add 'empty' steps to workflow
        workflow_results.add_step_result(past_1)
        workflow_results.add_step_result(past_2)
        workflow_results.add_step_result(current_step)

        # update steps
        past_1.add_artifact('a', 'A', 'aA')
        past_1.add_artifact('b', 'B', 'bB', 'file')
        past_1.add_artifact('z', 'Z')
        past_2.add_artifact('c', 'C')
        past_2.add_artifact('d', 'D')
        past_2.message = 'Failure'
        past_2.success = False
        current_step.add_artifact('x', 'X')
        current_step.add_artifact('y', 'Y')
        current_step.add_artifact('z', 'Z')
        current_step.message = 'Work in progress'

        # expect all three steps to be in the workflow_result
        expected_result = {
            'tssc-results': {
                'past_1': {
                    'artifacts': {
                        'a': {'description': 'aA', 'type': 'str', 'value': 'A'},
                        'b': {'description': 'bB', 'type': 'file', 'value': 'B'},
                        'z': {'description': '', 'type': 'str', 'value': 'Z'}
                    },
                    'message': '',
                    'step-implementer-name': 'one',
                    'step-name': 'past_1',
                    'sub-step-name': '',
                    'success': True
                },
                'past_2': {
                    'artifacts': {
                        'c': {'description': '', 'type': 'str', 'value': 'C'},
                        'd': {'description': '', 'type': 'str', 'value': 'D'},
                    },
                    'message': 'Failure',
                    'success': False,
                    'step-implementer-name': 'two',
                    'step-name': 'past_2',
                    'sub-step-name': '',
                },
                'current_step': {
                    'artifacts': {
                        'x': {'description': '', 'type': 'str', 'value': 'X'},
                        'y': {'description': '', 'type': 'str', 'value': 'Y'},
                        'z': {'description': '', 'type': 'str', 'value': 'Z'},
                    },
                    'message': 'Work in progress',
                    'success': True,
                    'step-implementer-name': 'wip',
                    'step-name': 'current_step',
                    'sub-step-name': '',
                }
            }
        }
        # test the steps in memory
        self.assertEqual(
            workflow_results.get_all_tssc_step_result(),
            expected_result
        )

        # push the steps to files
        workflow_results.write_to_pickle_file(result_file)
        workflow_results.write_tssc_results_to_yml_file('tssc-results.yml')
        workflow_results.write_tssc_results_to_json_file('tssc-results.json')

        # load from file and ensure the memory is still correct
        recap = WorkflowResult.load_from_file(result_file)
        # re-test the steps in memory
        self.assertEqual(
            recap.get_all_tssc_step_result(),
            expected_result
        )

        workflow_results.write_to_pickle_file(result_file)
        workflow_results.write_tssc_results_to_yml_file('tssc-results.yml')
        workflow_results.write_tssc_results_to_json_file('tssc-results.json')

    def test_merge_artifacts(self):
        # testing the contents of the list
        # specifically focused on the order of using the add step

        # start with an empty file
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete_file(result_file)
        workflow_results = WorkflowResult.load_from_file(result_file)

        # create 'empty' steps
        current_step = StepResult('current_step', 'wip')
        # add 'empty' steps to workflow
        workflow_results.add_step_result(current_step)
        # update steps
        current_step.add_artifact('x', 'X')
        current_step.success = False
        current_step.message = 'XXX'

        # expect all three steps to be in the workflow_result
        expected_result = {
            'tssc-results': {
                'current_step': {
                    'artifacts': {
                        'x': {'description': '', 'type': 'str', 'value': 'X'},
                    },
                    'message': 'XXX',
                    'success': False,
                    'step-implementer-name': 'wip',
                    'step-name': 'current_step',
                    'sub-step-name': '',
                }
            }
        }
        # test the steps in memory
        self.assertEqual(
            expected_result,
            workflow_results.get_all_tssc_step_result()
        )

        # push the current step to file
        workflow_results.write_to_pickle_file(result_file)

        # load from file and ensure the memory is still correct
        recap = WorkflowResult.load_from_file(result_file)
        match_step = StepResult('current_step', 'wip')
        recap.add_step_result(match_step)

        match_step.success = True
        match_step.message = 'UPDATED'
        match_step.add_artifact('a', 'A')

        recap_expected_result = {
            'tssc-results': {
                'current_step': {
                    'artifacts': {
                        'x': {'description': '', 'type': 'str', 'value': 'X'},
                        'a': {'description': '', 'type': 'str', 'value': 'A'},
                    },
                    'message': 'UPDATED',
                    'success': True,
                    'step-implementer-name': 'wip',
                    'step-name': 'current_step',
                    'sub-step-name': '',
                }
            }
        }
        # re-test the steps in memory
        self.assertEqual(
            recap.get_all_tssc_step_result(),
            recap_expected_result
        )

        #
        # # now add artifact to existing
        # current_step = StepResult('current_step', 'wip')
        # current_step.success = False
        # current_step.message = 'second time failed'
        # current_step.add_artifact('a', 'A')
        # workflow_results.write_to_pickle_file(result_file)
        # #
        # self.assertEqual(
        #     recap.get_all_tssc_step_result(),
        #     expected_result
        # )
        # expected_result_additions = {
        #     'tssc-results': {
        #         'current_step': {
        #             'artifacts': {
        #                 'a': {'description': '', 'type': 'str', 'value': 'A'},
        #                 'x': {'description': '', 'type': 'str', 'value': 'X'},
        #             },
        #             'message': 'Second time failed',
        #             'success': False,
        #             'step-implementer-name': 'wip',
        #             'step-name': 'current_step',
        #         }
        #     }
        # }
        # self.assertEqual(
        #     expected_result_additions,
        #     recap.get_all_tssc_step_result()
        # )
        # test the steps in memory
