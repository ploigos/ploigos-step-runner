from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from tests.helpers.test_utils import Any
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.uat.schemathesis import Schemathesis
from ploigos_step_runner import StepResult
 
 
class TestStepImplementerSchemathesis(BaseStepImplementerTestCase):
   def create_step_implementer(
       self,
       workflow_result=None,
       step_config={},
       parent_work_dir_path=''
   ):
       return self.create_given_step_implementer(
           step_implementer=Schemathesis,
           step_config=step_config,
           step_name='uat',
           implementer='Schemathesis',
           workflow_result=workflow_result,
           parent_work_dir_path=parent_work_dir_path
       )
 
   def test_step_implementer_config_defaults(self):
       defaults = Schemathesis.step_implementer_config_defaults()
       expected_defaults = {'name': 'World'}
       self.assertEqual(defaults, expected_defaults)
 
   def test_required_config_or_result_keys(self):
       required_keys = Schemathesis._required_config_or_result_keys()
       expected_required_keys = ['name']
       self.assertEqual(required_keys, expected_required_keys)
 
   def test_run_step_default(self):
       schemathesis = self.create_step_implementer()
 
       result = schemathesis._run_step()
       self.assertEqual(result.artifacts['message'].as_dict(),
                        {'name': 'message',
                        'value': 'Schemathesis Hello World!',
                        'description': ''})
 
   def test_run_step_with_name(self):
       schemathesis = self.create_step_implementer(
           step_config={'name': "test name"})
 
       result = schemathesis._run_step()
       self.assertEqual(result.artifacts['message'].as_dict(),
                        {'name': 'message',
                        'value': 'Schemathesis Hello test name!',
                        'description': ''})
