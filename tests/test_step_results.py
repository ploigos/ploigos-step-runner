"""
:return:
"""
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult

class TestStepResultTest(BaseTSSCTestCase):
    """
    :return:
    """

    def test_basic(self):
        """
        :return:
        """
        result_file = 'tssc-results.pkl'
        WorkflowResult.delete(result_file)
        workflow_results = WorkflowResult.load(result_file)

        step_1 = StepResult('step1', 'one')
        step_1.message = 'hello dolly!'
        step_1.add_artifact('version',
                            'v0.10.0+23',
                            'semantic version',
                            'string',
                            )
        # # update the workflow by adding step_1
        workflow_results.add_step_result(step_1)
        workflow_results.dump_pickle(result_file)
        workflow_results.dump_yml('tssc-results.yml')

        #
        step_2 = StepResult('step2', 'one')
        step_2.success = False
        step_2.message = 'looser'
        step_2.add_artifact('simple', 'a value')
        workflow_results.add_step_result(step_2)

        workflow_results.dump_pickle(result_file)
        workflow_results.dump_yml('tssc-results.yml')
        workflow_results.dump_json('tssc-results.json')



        # above we created one entry, let's read it
        workflow_test = WorkflowResult.load(result_file)
        workflow_test.print_json()

        workflow_test.get_artifact('bad')
        version = workflow_test.get_artifact('version')
        print(version)
        simple = workflow_test.get_artifact('simple')
        print(simple)