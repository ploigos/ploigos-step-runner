import os

from ploigos_step_runner.results import WorkflowResult
from ploigos_step_runner.step_implementers.shared import AdHoc
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestAdHoc(BaseStepImplementerTestCase):

    def test_run_step_fails_if_command_not_provided(self):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured like:
            step_implementer = self.create_step_implementer(test_dir, {})

            # WHEN I run the step
            step_result = step_implementer._run_step()

            # THEN it should return a StepResult
            self.assertIsNotNone(step_result)

            # AND the StepResult should have an artifact with the default message
            self.assertEqual(step_result.success, False)

    def test_run_step_with_command(self):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured like:
            config = {
                'command': 'echo "Hello World!"'
            }
            step_implementer = self.create_step_implementer(test_dir, config)

            # WHEN I run the step
            step_result = step_implementer._run_step()

            # THEN it should return a StepResult
            self.assertIsNotNone(step_result)

            # AND the StepResult should have an artifact with the default message
            self.assertIsNotNone(step_result.get_artifact('command-output').value)


    def test__required_config_or_result_keys(self):
        required_keys = AdHoc._required_config_or_result_keys()
        self.assertEqual(required_keys, ['command'])

    def create_step_implementer(self, test_dir, step_config):
        parent_work_dir_path = os.path.join(test_dir.path, 'working')
        return self.create_given_step_implementer(
            step_implementer=AdHoc,
            step_config=step_config,
            step_name='adhoc',
            implementer='AdHoc',
            workflow_result=WorkflowResult(),
            parent_work_dir_path=parent_work_dir_path
        )
