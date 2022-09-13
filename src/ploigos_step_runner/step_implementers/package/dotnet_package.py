"""`StepImplementer` for the `package` step using Dotnet.

Notes
-----

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key            | Required? | Default | Description
-----------------------------|-----------|---------|-----------
`csproj-file`                | Yes       |         | .csproj or .sln file to pass to dotnet command

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------

"""

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.shell import Shell


class DotnetPackage(StepImplementer):
    """
    StepImplementer for the `dotnet publish` command
    """

    @staticmethod
    def step_implementer_config_defaults():
        return []

    @staticmethod
    def _required_config_or_result_keys():
        return [
            "csproj-file"
        ]

    def _run_step(self):
        # Command usage: `dotnet [options] publish [<PROJECT | SOLUTION>]`
        # Build the arguments
        args = []
        args += self._build_options()                # [options]
        args += ["publish"]                          # publish
        csproj_file = self.get_value('csproj-file')
        args += [csproj_file]                        # [<PROJECT | SOLUTION>]

        # STDOUT goes here
        output_file_path = self.write_working_file('dotnet_publish_output.txt')

        # Run the command
        Shell().run(
            'dotnet',
            args=args,
            output_file_path=output_file_path
        )

        return StepResult.from_step_implementer(self)

    def _build_options(self):
        """
        Build the [options] part of the dotnet command
        """
        options = []

        # The 'dotnet' command has a -c flag which stands for 'configuration'.
        # Use it if psr is configured for it.
        config_setting = self.get_value('configuration')
        if config_setting is not None:
            options += ['-c', config_setting]

        return options
