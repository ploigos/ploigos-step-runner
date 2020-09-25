"""
:return:
"""
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult
from tssc.workflow_result import WorkflowFile
from tssc.workflow_result import Wrapper


class TestStepResultTest(BaseTSSCTestCase):
    """
    :return:
    """

    def test_clear(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        # instantiate a new workflow file
        workflow_file = WorkflowFile(result_file)
        # clear the file
        workflow_file.clear()

        # load the empty file into the workflow
        workflow_1 = workflow_file.load()
        # if nothing is loaded (no workflow_results, instantiate workflow_results)
        if workflow_1 is None:
            workflow_1 = WorkflowResult()

        # create a test step
        step_1 = StepResult('step1', 'one')
        step_1.message = 'hello dolly!'
        step_1.runtime_config = {'config': 'test'}
        step_1.add_artifact('version',
                            'semantic version',
                            'string',
                            'v0.10.0+23'
                            )

        # update the workflow by adding step_1
        workflow_1.add_step_result(step_1)
        print(workflow_1.get_step_result('step1'))

        # put the workflow into a pickle file
        workflow_file.dump(workflow_1)

    def test_load_one(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        workflow_file = WorkflowFile(result_file)

        if workflow_file is None:
            workflow_2 = WorkflowResult()
        else:
            workflow_2 = workflow_file.load()

        # use the print __str__
        step_2 = StepResult('step2', 'one')
        step_2.success = False
        step_2.add_artifact('notversion',
                             'semantic version',
                             'string',
                             'v0.10.0+23'
                             )
        workflow_2.add_step_result(step_2)
        workflow_file.dump(workflow_2)

    def test_load_two(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        workflow_file = WorkflowFile(result_file)
        if workflow_file is None:
            workflow_3 = WorkflowResult()
        else:
            workflow_3 = workflow_file.load()

        step_3 = StepResult('step3', 'one')
        step_3.success = False
        step_3.message = 'failed'
        step_3.add_artifact('notnotversion',
                            'semantic version',
                            'string',
                            'v0.10.0+33'
                            )
        workflow_3.add_step_result(step_3)
        workflow_file.dump(workflow_3)

        current_step = StepResult('newstep', 'news')
        current_step.add_artifact('newstep_1', 'reporter', 'file', 'file://hello.txt')
        current_step.add_artifact('newstep_2', 'reporter', 'url', 'http://www.google.com')
        current_step.runtime_config = {'quick': 'test'}

        workflow_3.add_step_result(current_step)
        print('---------------- yml results')
        workflow_3.print_yml()
        print('---------------- json results')
        workflow_3.print_json()
        print('---------------- a result')
        print(workflow_3.get_step_result('newstep'))
        print('---------------- a result artifacts')
        print(workflow_3.get_step_artifacts('newstep'))
        workflow_file.dump(workflow_3)

    def test_final(self):
        result_file = 'tssc-results.pkl'
        workflow_file = WorkflowFile(result_file)
        if workflow_file is None:
            workflow_3 = WorkflowResult()
        else:
            workflow_3 = workflow_file.load()
        workflow_3.print_yml()


    def test_wrapper(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        # instantiate a new workflow file
        workflow = Wrapper(result_file)

        # create a test step
        step_1 = StepResult('call911', 'one')
        step_1.message = 'hello dolly!'
        step_1.runtime_config = {'config': 'test'}
        step_1.add_artifact('version',
                            'semantic version',
                            'string',
                            'v0.10.0+23'
                            )
        step_1.add_artifact_misc({'help': 'fallen'})

        # put the workflow into a pickle file
        workflow.write(step_1)

        workflow_2 = Wrapper(result_file)
        workflow_2.results.print_json()
