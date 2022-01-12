"""`StepImplementer` for a generic NPM step for testing. It supports the parsing of xunit style results.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default    | Description
-----------------------------|-----------|------------|------------
`test-reports-dirs`          | Yes       |            | Location of test result files
`test-reports-dir`           | Yes       |            | Alias for `test-reports-dirs`
`npm-test-script`            | Yes       |            | NPM script to run the test
`target-host-env-var-name`   | No        |            | It is assumed that integration tests need to know a URL
                                                         endpoint to run the tests against,
                                                         and we are standardizing on passing this in via an
                                                         environment variable. There is no standard name for this
                                                         environment variable, so it is user defined.
`npm-envs`                   | No        |            | Additional environment variable key value pairs

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`npm-output`        | Path to Stdout and Stderr from invoking NPM.
`test-report`       | Directory containing the test reports generated from running this step.
"""  # pylint: disable=line-too-long

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementers.shared.maven_test_reporting_mixin import \
    MavenTestReportingMixin
from ploigos_step_runner.step_implementers.shared.npm_generic import NpmGeneric

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    ['test-reports-dirs','test-reports-dir'],
    'target-host-env-var-name',
    'npm-test-script'
]

DEFAULT_CONFIG = {}


class NpmXunitGeneric(NpmGeneric, MavenTestReportingMixin):
    """`StepImplementer` for the `uat` step using npm by invoking a
    use specified npm script.
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

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # NOTE:
        #   at some point may need to do smarter logic if a deployable has more then one deployed
        #   host URL to do UAT against all of them, but for now, use first one as target of UAT
        deployed_host_urls = self.get_value('deployed-host-urls')
        target_host_url = "unset"
        if isinstance(deployed_host_urls, list):
            target_host_url = deployed_host_urls[0]
            if len(deployed_host_urls) > 1:
                step_result.message = \
                    f"Given more than one deployed host URL ({deployed_host_urls})," \
                    f" targeting first one ({target_host_url}) for test."
                print(step_result.message)
        elif deployed_host_urls:
            target_host_url = deployed_host_urls
        else:
            target_host_url = self.get_value('target-host-url')

        # run the tests
        npm_output_file_path = self.write_working_file('npm_output.txt')
        try:
            self.npm_args = ['run', self.get_value('npm-test-script')]

            additional_envs = None
            if self.get_value("target-host-env-var-name"):
                additional_envs = {self.get_value(
                    "target-host-env-var-name"): target_host_url}

            # execute npm step
            self._run_npm_step(
                npm_output_file_path=npm_output_file_path,
                step_implementer_additional_envs=additional_envs
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = f"Error running npm. More details maybe found in report artifacts: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from npm.",
                name='npm-output',
                value=npm_output_file_path
            )

        test_report_dirs = self.get_value(['test-reports-dir','test-reports-dirs'])
        if test_report_dirs:
            step_result.add_artifact(
                description="Test report generated when running tests.",
                name='test-report',
                value=test_report_dirs
            )

            # gather test report evidence
            self._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=step_result,
                test_report_dirs=test_report_dirs
            )

        # return result
        return step_result
