import os

from ploigos_step_runner.results import WorkflowResult
from ploigos_step_runner.step_implementers.examples import HelloWorld
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestHelloWorld(BaseStepImplementerTestCase):

    def test_step_run_step_result(self):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured like:
            step_implementer = self.create_step_implementer(test_dir, {})

            # WHEN I run the step
            step_result = step_implementer._run_step()

            # THEN it should return a StepResult
            self.assertIsNotNone(step_result)

            # AND the StepResult should have an artifact with the default message
            self.assertEqual(step_result.get_artifact('greeting-output').value, 'Hello World!')

    def test_run_step_configuration(self):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured with a non-default message
            step_implementer = self.create_step_implementer(test_dir, {
                'greeting-name': 'Everyone'
            })

            # WHEN I run the step
            step_result = step_implementer._run_step()

            # THEN it should return a StepResult
            self.assertIsNotNone(step_result)

            # AND the StepResult should have an artifact with the configured message
            self.assertEqual(step_result.get_artifact('greeting-output').value, 'Hello Everyone!')

    def test__required_config_or_result_keys(self):
        required_keys = HelloWorld._required_config_or_result_keys()
        self.assertEqual(required_keys, [])

    def create_step_implementer(self, test_dir, step_config):
        parent_work_dir_path = os.path.join(test_dir.path, 'working')
        return self.create_given_step_implementer(
            step_implementer=HelloWorld,
            step_config=step_config,
            step_name='examples',
            implementer='HelloWorld',
            workflow_result=WorkflowResult(),
            parent_work_dir_path=parent_work_dir_path
        )
