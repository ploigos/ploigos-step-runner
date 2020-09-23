"""
:return:
"""
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tssc.step_results import StepResults
from tssc.step_results_list import StepResultsList


# used for testing...
def test_for_step(my_list, look_for_step, look_for_art):
    """
    :return:
    """
    one = my_list.get_result_step(look_for_step)
    if one is not None:
        print(one)
        print(one.get_artifacts())
        art = one.get_artifact(look_for_art)
        if art is None:
            print(f'artifact {look_for_art} not found for step {look_for_step}')
    else:
        print(f'step {look_for_step} not found')


class TestStepResults(BaseTSSCTestCase):
    """
    :return:
    """

    def test_one(self):
        """
        :return:
        """
        # SETUP for TESTING...
        # this file should be in the "results folder" - look where
        # tssc-results.yml was stored
        # in theory, tssc-results.pkl replaces tssc-results.yml
        result_file = 'tssc-results.pkl'
        tester = StepResultsList(result_file)

        # create a test ... setup for testing... these would be steps running ...
        step_1 = StepResults('stepone', 'Maven')
        test_2 = StepResults('stepone', 'Git')
        test_3 = StepResults('steptwo', 'Yada')

        step_1.set_end_state(True, 'hellodolly')
        test_2.set_end_state(False, 'on no')
        test_3.set_end_state(True, 'good deal')

        test_3.add_artifact('version', 'semantic version', 'string', 'v0.10.0+23')
        test_3.add_artifact('image-tag', 'tag to use for any created images', 'string', 'v0.10.0')
        test_3.add_artifact('runtime-step-config', 'custome report dir from pom', 'filepath',
                        'surefire_reports/custom/results_dir/')

        # create a fake list to test with
        test_list = [step_1, test_2, test_3]
        tester.list_append(test_list)
        tester.list_dump()
        # DONE with test SETUP...

        # Now that I have something setup - play with the methods
        # look at all PREVIOUS results
        previous_result_list = StepResultsList(result_file)
        # just looking at the output ...
        previous_result_list.list_json()
        previous_result_list.list_yml()

        ## create current result set
        current_step = StepResults('newstep', 'news')
        current_step.set_end_state(True, 'it works')
        current_step.add_artifact('newstep_1', 'reporter', 'file', 'file://hello.txt')
        current_step.add_artifact('newtest_2', 'reporter', 'url', 'http://www.google.com')

        ## append to current results
        previous_result_list.list_append(current_step)
        ## write to prevous results do we want to both append to write?
        previous_result_list.list_dump()
        # just looking for fun here ...
        previous_result_list.list_json()

        # try it all again...
        # look new previous results
        test_list = StepResultsList(result_file)
        test_list.list_json()
        test_list.list_yml()

        # i want to get resultSet from previous run...
        test_for_step(test_list, 'newstep', 'newstep_1')
        test_for_step(test_list, 'newstep', 'testformissing')
        test_for_step(test_list, 'testformissing', 'testformissing')
