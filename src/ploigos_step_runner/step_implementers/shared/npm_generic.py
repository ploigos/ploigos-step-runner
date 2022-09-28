"""
Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default          | Description
-----------------------------|-----------|------------------|-----------
`package-file`               | No        | `'package.json'` | package.json file for reference app.
`npm-envs`                   | No        |                  | Environment vars to pass to NPM.
`npm-args`                   | Yes       | `None`           | Arguments to pass to the npm command.
"""


import os
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.shell import Shell

DEFAULT_CONFIG = {
    'package-file': 'package.json'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'package-file',
    'npm-args'
]


class NpmGeneric(StepImplementer):
    """Abstract parent class for StepImplementers that use npm.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None,
        npm_args=None,
        npm_envs=None
    ):
        self.__npm_args = npm_args
        self.__npm_envs = npm_envs

        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment
        )

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

        Returns
        -------
        dict
            Default values to use for step configuration values.

        Notes
        -----
        These are the lowest precedence configuration values.
        """
        return DEFAULT_CONFIG

    @staticmethod
    def _required_config_or_result_keys():
        """Getter for step configuration or previous step result artifacts that are required before
        running this step.

        See Also
        --------
        _validate_required_config_or_previous_step_result_artifact_keys

        Returns
        -------
        array_list
            Array of configuration keys or previous step result artifacts
            that are required before running the step.
        """
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * given 'package-file' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # if package-file has value verify file exists
        # If it doesn't have value and is required function will have already failed
        package_file = self.get_value('package-file')
        if package_file is not None:
            assert os.path.exists(package_file), \
                f'Given npm package file (package-file) does not exist: {package_file}'

    @property
    def npm_args(self):
        """Property for getting the npm arguments to be passed to the npm command.

        Returns
        -------
        str
            npm arguments
        """
        npm_args = None
        if self.__npm_args:
            npm_args = self.__npm_args
        else:
            npm_args = self.get_value('npm-args')

        return npm_args

    @npm_args.setter
    def npm_args(self, value):
        self.__npm_args = value

    @property
    def npm_envs(self):
        """Property for getting option environment variables that should be accessible to the npm
        command

        Returns
        -------
        dict
            Key value pairs representing environment variables
        """
        npm_envs = None
        if self.__npm_envs:
            npm_envs = self.__npm_envs
        else:
            npm_envs = self.get_value('npm-envs')

        return npm_envs

    def _run_npm_step(
        self,
        npm_output_file_path,
        step_implementer_additional_envs=None,
        npm_args=None,
    ):
        """Runs npm using the configuration given to this step runner.

        Parameters
        ----------
        npm_output_file_path : str
            Path to file containing the npm stdout and stderr output.
        step_implementer_additional_envs : {}
            Additional environment variables injected by the step implementer.
        npm_args : str
            Arguments to pass to npm. Defaults to self.npm_args.

        Raises
        ------
        StepRunnerException
            If npm returns a non 0 exit code.
        """

        if not npm_args:
            npm_args = self.npm_args

        npm_envs = None

        if step_implementer_additional_envs:
            npm_envs = step_implementer_additional_envs

        if self.npm_envs:
            if npm_envs:
                npm_envs.update(self.npm_envs)
            else:
                npm_envs = self.npm_envs

        Shell().run(
            'npm',
            output_file_path=npm_output_file_path,
            args=npm_args,
            envs=npm_envs
        )

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # package the artifacts
        npm_output_file_path = self.write_working_file('npm_output.txt')
        try:
            # execute npm step (params come from config)
            self._run_npm_step(
                npm_output_file_path=npm_output_file_path
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running npm. " \
                f"More details maybe found in 'npm-output' report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from npm.",
                name='npm-output',
                value=npm_output_file_path
            )

        return step_result
