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
`tox-config`                 | Yes       | `'tox.ini'`      | tox.ini file for reference app.
`tox-env`                    | Yes       | `None`           | The tox environment to run against.
`quiet`                      | No        | `True`           | disable quiet mode during execution.
"""


import os
from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.tox import run_tox


DEFAULT_CONFIG = {
    'tox-config': 'tox.ini',
    'quiet': True,
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'tox-config',
    'tox-env'
]


class ToxGeneric(StepImplementer):
    """Abstract parent class for StepImplementers that use tox.
    """

    def __init__( # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None,
        tox_env=None
    ):
        self.__tox_env = tox_env

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
        * given 'tox-config' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # if tox-config has value verify file exists
        # If it doesn't have value and is required function will have already failed
        tox_config = self.get_value('tox-config')
        if tox_config is not None:
            assert os.path.exists(tox_config), \
                f'Given tox config file (tox-config) does not exist: {tox_config}'

    @property
    def tox_env(self):
        """Property for getting the tox arguments.

        Returns
        -------
        str
            Tox arguments
        """
        tox_env = None
        if self.__tox_env:
            tox_env = self.__tox_env
        else:
            tox_env = self.get_value('tox-env')

        return tox_env

    def _run_tox_step(
        self,
        tox_output_file_path
    ):
        """Runs tox using the configuration given to this step runner.

        Parameters
        ----------
        tox_output_file_path : str
            Path to file containing the tox stdout and stderr output.
        step_implementer_additional_arguments : []
            Additional arguments hard coded by the step implementer.

        Raises
        ------
        StepRunnerException
            If tox returns a none 0 exit code.
        """

        tox_env = self.tox_env
        quiet = self.get_value('quiet')

        if quiet:
            tox_args = ('-q', '-e', tox_env,)
        else:
            tox_args = ('-e', tox_env,)

        run_tox(
            tox_output_file_path=tox_output_file_path,
            tox_args=tox_args
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
        tox_output_file_path = self.write_working_file('tox_output.txt')
        try:
            # execute tox step (params come from config)
            self._run_tox_step(
                tox_output_file_path=tox_output_file_path
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running tox. " \
                f"More details maybe found in 'tox-output' report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from tox.",
                name='tox-output',
                value=tox_output_file_path
            )

        return step_result
