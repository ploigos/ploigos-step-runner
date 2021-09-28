"""`StepImplementer` for the `unit_test` step using NPM by invoking a configurable command. Test results should be in xunit format.
   Unit tests run via NPM will receive their configurable parameters via environment variables passed through this step implementer.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default    | Description
-----------------------------|-----------|------------|------------
`npm-test-script`            | No        | 'test'     | NPM script to run the integration test
`test-reports-dir`           | Yes       |            | Location of test result files
`npm-envs`                   | No        |            | Additional environment variable key value pairs

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`npm-output`        | Path to Stdout and Stderr from invoking NPM.
`test-report`       | Directory containing the test reports generated from running this step.
"""  # pylint: disable=line-too-long

from ploigos_step_runner.step_implementers.shared import NpmXunitGeneric
from ploigos_step_runner.step_implementers.shared import MavenTestReportingMixin

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'test-reports-dir',
]

DEFAULT_CONFIG = {'npm-test-script': 'test'}


class NpmXunitTest(NpmXunitGeneric, MavenTestReportingMixin):
    """`StepImplementer` for the `unit_test` step using npm by invoking a
    user specified npm script.
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
        return {**NpmXunitGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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
