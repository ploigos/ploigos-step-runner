"""`StepImplementer` for the `hello-world` step using LongGreeting.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key             | Required? | Default                  | Description
------------------------------|-----------|--------------------------|-----------
`greeting-name`               | No        | `World`                  | Name to use in greeting message.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key    | Description
-----------------------|------------
`message`              | Message that was printed
"""  # pylint: disable=line-too-long

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer


class HelloWorld(StepImplementer):
    """
    Example of a simple StepImplementer
    """

    # Overridden to specify default values for this StepImplementer's configuration.
    @staticmethod
    def step_implementer_config_defaults():
        return []  # No defaults

    # Overridden to specify required configuration values. These can be specified in
    # the configuration file or calculated by previous steps in the workflow.
    @staticmethod
    def _required_config_or_result_keys():
        return {
            'greeting-name': 'World'
        }

    # Overridden to implement the behavior of this StepImplementer.
    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        greeting = self.get_value('greeting-name')  # Read from configuration

        message = f"Hello {greeting}!"
        step_result.add_artifact(
            name='message',
            value=message
        )

        try:
            print(message)

        # This won't happen for the print statement, but real
        # utilities in the PSR framework throw StepRunnerExcaptions if something goes wrong
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = str(error)
            return step_result

        return step_result
