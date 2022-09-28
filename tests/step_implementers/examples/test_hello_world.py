import os
from unittest.mock import patch
from ploigos_step_runner.results import WorkflowResult
from ploigos_step_runner.step_implementers.examples import HelloWorld
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.exceptions import StepRunnerException


@patch('ploigos_step_runner.step_implementers.shared.npm_generic.Shell.run')  # Given a shell
class TestStepImplementerDotnetPackage(BaseStepImplementerTestCase):

    def test_run_step_executes_echo_command(self, mock_shell):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured like:
            step_implementer = self.create_step_implementer(test_dir, {})

            # WHEN I run the step
            actual_step_result = step_implementer._run_step()

            # THEN it should run a shell command like `echo "Hello World!"`
            expected_output_file_path = os.path.join(test_dir.path, 'working', 'examples', 'greeting-output.txt')
            mock_shell.assert_any_call(
                'echo',
                args=['Hello World!'],
                output_file_path=expected_output_file_path
            )

    def test_run_step_configure_greeting(self, mock_shell):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured with a non-default message
            step_implementer = self.create_step_implementer(test_dir, {
                'greeting-name': 'Everyone'
            })

            # WHEN I run the step
            actual_step_result = step_implementer._run_step()

            # THEN it should run a shell command like 'echo "Hello Everyone!"'
            expected_output_file_path = os.path.join(test_dir.path, 'working', 'examples', 'greeting-output.txt')
            mock_shell.assert_any_call(
                'echo',
                args=['Hello Everyone!'],
                output_file_path=expected_output_file_path
            )

    def test_run_step_result(self, mock_shell):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer configured like:
            step_implementer = self.create_step_implementer(test_dir, {})

            # WHEN I run the step
            step_result = step_implementer._run_step()

            # THEN it should return a StepResult
            self.assertIsNotNone(step_result)

            # AND the StepResult should say that the step was successful
            self.assertEqual(step_result.success, True)

    def test_run_step_success_false_when_shell_command_fails(self, mock_shell):
        with TempDirectory() as test_dir:

            # GIVEN a step implementer
            step_implementer = self.create_step_implementer(test_dir, {})

            # Given that every shell command exits with an error code
            mock_shell.side_effect = StepRunnerException()

            # When I run the step
            step_result = step_implementer.run_step()

            # AND the StepResult should say that the step was not successful
            self.assertEqual(step_result.success, False)

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
