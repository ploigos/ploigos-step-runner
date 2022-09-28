"""Example StepImplementer that executes a shell command. This is a good starting point if you are writing
a step implementer that is meant to run an external command line tool.

You can run this example from the command line by creating a file named psr.yaml with these contents:

```
step-runner-config:

  examples:
    - implementer: HelloShell
      config:
        greeting-name: Folks
```

And then running the command `psr -s examples -c psr.yaml`

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
`echo-output`              | Message that was printed
"""  # pylint: disable=line-too-long

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.shell import Shell


class HelloShell(StepImplementer):
    """
    Example StepImplementer that uses the echo shell command to print a message.
    """

    # Overridden to specify default values for this StepImplementer's configuration.
    @staticmethod
    def step_implementer_config_defaults():
        return {
            'greeting-name': 'World'
        }

    # Overridden to specify required configuration values. These can be specified in
    # the configuration file or calculated by previous steps in the workflow.
    @staticmethod
    def _required_config_or_result_keys():
        return []  # No required values without defaults

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

        try:
            # Log STDOUT and STDERR to this file
            output_file_path = self.write_working_file('greeting-output.txt')

            # Run the command
            Shell().run(
                'echo',
                args=[message],
                output_file_path=output_file_path
            )

        except StepRunnerException as error:
            step_result.success = False
            step_result.message = str(error)
            return step_result
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from the echo command",
                name='greeting-output',
                value=output_file_path
            )
        return step_result
