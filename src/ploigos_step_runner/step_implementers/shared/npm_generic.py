import os

from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.xml import get_xml_element_by_path
from ploigos_step_runner.utils.npm import run_npm

DEFAULT_CONFIG = {
    'package-file': 'package.json',
    'tls-verify': True
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'package-file',
    'npm-run-scripts'
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
        npm_run_scripts=[]
    ):
        self.__npm_run_scripts = npm_run_scripts

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
                f'Given npm package.json file (package-file) does not exist: {package_file}'

    @property
    def npm_run_scripts(self):
        """Property for getting the npm phases and goals to execute which can either come
        from field set on this class via constructor, intended for use by sub classes that want
        to hard code the phases and goals for convenience, or comes from config value
        `npm-phases-and-goals` set by the user.

        Returns
        -------
        str
            Maven phases and/or goals to execute.
        """
        npm_run_scripts = None
        if self.__npm_run_scripts:
            npm_run_scripts = self.__npm_run_scripts
        else:
            npm_run_scripts = self.get_value('npm-run-scripts')

        return npm_run_scripts

    def _run_npm_step(
        self,
        npm_output_file_path
    ):
        """Runs npm using the configuration given to this step runner.

        Parameters
        ----------
        npm_output_file_path : str
            Path to file containing the npm stdout and stderr output.
        step_implementer_additional_arguments : []
            Additional arguments hard coded by the step implementer.

        Raises
        ------
        StepRunnerException
            If npm returns a none 0 exit code.
        """

        run_scripts = self.npm_run_scripts
        package_file = self.get_value('package-file')

        run_npm(
            npm_output_file_path=npm_output_file_path,
            package_file=package_file,
            run_scripts=run_scripts
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

