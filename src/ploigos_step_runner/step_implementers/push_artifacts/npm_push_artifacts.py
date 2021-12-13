"""`StepImplementer` for the `push-artifacts` step using npm.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key            | Required? | Default | Description
-----------------------------|-----------|---------|-----------
`package-file`               | No        | `'package.json'` | package.json file for reference app.
`npm-envs`                   | No        |                  | Environment vars to pass to NPM.
`npm-args`                   | Yes       | `None`           | Arguments to pass to the npm command.
'npm-registry'               | Yes       | `None`           | Push artifacts to this registry.
'npm-user'                   | Yes       | `None`           | Authenticate to the registry as this
                                                              user.
'npm-password'               | Yes       | `None`           | Authenticate to the registry with
                                                              this password.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
"""

from base64 import b64encode
from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.step_implementers.shared.npm_generic import NpmGeneric

DEFAULT_CONFIG = {}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'npm-registry',
    'npm-user',
    'npm-password'
]

class NpmPushArtifacts(NpmGeneric):
    """`StepImplementer` for the `push-artifacts` step using Maven.
    """
    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None
    ):
        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment,
            npm_args='publish',
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
        return {**NpmGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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

    def _run_step(self): # pylint: disable=too-many-locals
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """

        step_result = StepResult.from_step_implementer(self)

        try:
            self._execute_npm_publish()
        except StepRunnerException as error:
            self._handle_step_runner_exception(step_result, error)
        finally:
            pass

        return step_result

    def _execute_npm_publish(self):
        self._run_npm_step(
            npm_output_file_path=self.write_working_file('npm_publish_output.txt'),
            step_implementer_additional_envs=self._generate_npm_env_args()
        )

    def _generate_npm_env_args(self):
        auth_string = self.get_value('npm-user') + ':' + self.get_value('npm-password')
        encoded_auth_string = b64encode(auth_string.encode()).decode()
        env = {
            'NPM_CONFIG_REGISTRY': self.get_value('npm-registry'),
            'NPM_CONFIG__AUTH': encoded_auth_string
        }
        return env

    @staticmethod
    def _handle_step_runner_exception(step_result, error):
        step_result.message = "NPM publish failure.  See 'npm_publish_output.txt' " \
                              f"report artifacts for details: {error}"
        step_result.success = False
