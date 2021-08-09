
"""`StepImplementer` for the `uat` step using Maven by invoking the 'integration-test` maven phase.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default | Description
-----------------------------|-----------|---------|------------
`pom-file`                   | Yes       | `'pom.xml'` | pom used when executing maven.
`tls-verify`                 | No        | `True`  | Disables TLS Verification if set to False
`maven-profiles`             | No        | `[]`    | List of maven profiles to use.
`maven-no-transfer-progress` | No        | `True`  | `True` to suppress the transfer progress of packages maven downloads.
                                                     `False` to have the transfer progress printed.\
                                                      See https://maven.apache.org/ref/current/maven-embedder/cli.html
`maven-additional-arguments` | No        | `['-DskipTests']` \
                                                   | List of additional arguments to use. \
                                                     Default is because when running `integration-test` phase the `test` phase will also be run, \
                                                     so this is a "good" way to not re-run the `test` phase tests again.
`maven-servers`              | No        |         | Dictionary of dictionaries of id, username, password
`maven-repositories`         | No        |         | Dictionary of dictionaries of id, url, snapshots, releases
`maven-mirrors`              | No        |         | Dictionary of dictionaries of id, url, mirror_of
`test-reports-dir`           | No        |         | Default is to try and dynamically determine where the test reports directory is \
                                                     based on configuration in the given `pom-file`, but it is impossible task to do \
                                                     in all cases. \
                                                     So, this parameter provides a way for the user to specify where the test results \
                                                     are if our attempts at dynamically figuring it out are failing your unique pom.
`target-host-url-maven-argument-name` \
                             | Yes       |         | It is assumed that integration tests need to know a URL endpoint to run the tests against, \
                                                     but there is not standardized way for integration tests to receive that information. \
                                                     Therefor this parameter takes the name of a maven -D flag that should be set with the \
                                                     target host url to then be read by the integration tests.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`maven-output`      | Path to Stdout and Stderr from invoking Maven.
`test-report`       | Directory containing the test reports generated from running this step.
"""# pylint: disable=line-too-long

from ploigos_step_runner import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared import (
    MavenGeneric, MavenTestReportingMixin)

DEFAULT_CONFIG = {
    'maven-additional-arguments': ['-DskipTests']
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'pom-file',
    'target-host-url-maven-argument-name'
]

class MavenIntegrationTest(MavenGeneric, MavenTestReportingMixin):
    """`StepImplementer` for the `uat` step using Maven by invoking the
    'integration-test` maven phase.
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
            maven_phases_and_goals=['integration-test', 'verify']
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
        return {**MavenGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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
        if isinstance(deployed_host_urls, list):
            target_host_url = deployed_host_urls[0]
            if len(deployed_host_urls) > 1:
                step_result.message = \
                    f"Given more then one deployed host URL ({deployed_host_urls})," \
                    f" targeting first one ({target_host_url}) for user acceptance test (UAT)."
                print(step_result.message)
        elif deployed_host_urls:
            target_host_url = deployed_host_urls
        else:
            target_host_url = self.get_value('target-host-url')

        # run the tests
        print("Run user acceptance tests (UAT)")
        mvn_output_file_path = self.write_working_file('mvn_output.txt')
        try:
            # execute maven step (params come from config)
            self._run_maven_step(
                mvn_output_file_path=mvn_output_file_path,
                step_implementer_additional_arguments=[
                    f'-D{self.get_value("target-host-url-maven-argument-name")}={target_host_url}'
                ]
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running maven. " \
                f"More details maybe found in report artifacts: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value=mvn_output_file_path
            )

        # get test report dir
        test_report_dir = self.__get_test_report_dir()
        if test_report_dir:
            step_result.add_artifact(
                description="Test report generated when running unit tests.",
                name='test-report',
                value=test_report_dir
            )

            # gather test report evidence
            self._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=step_result,
                test_report_dir=test_report_dir
            )

        # return result
        return step_result

    def __get_test_report_dir(self):
        """Gets the test report directory.

        Search Priority:
        * values -> 'test-reports-dir'
        * pom.xml -> maven-failsafe-plugin -> reportsDirectory
        * pom.xml -> maven-surefire-plugin (for integration-test phase or goal) -> reportsDirectory

        Returns
        -------
        str
            Path to the directory containing the test reports.
        """
        # user supplied where the test reports go, just use that
        test_report_dir = self.get_value('test-reports-dir')

        # else do our best to find them
        if not test_report_dir:
            # attempt to get failsafe test report dir, if not, try for surefire
            test_report_dir = None
            try:
                test_report_dir = self._attempt_get_test_report_directory(
                    plugin_name=MavenTestReportingMixin.FAILSAFE_PLUGIN_NAME,
                    configuration_key=MavenTestReportingMixin.FAILSAFE_PLUGIN_REPORTS_DIR_CONFIG_NAME,
                    default=MavenTestReportingMixin.FAILSAFE_PLUGIN_DEFAULT_REPORTS_DIR
                )
            except StepRunnerException:
                # this means the failsafe plugin was not found, so try looking for the surefire plugin,
                # configured for this phase
                try:
                    # NOTE: when looking for surefire plugin configuration as part of the integration
                    #       test phase ensure that it is configured for correct phase, since its
                    #       default phases are for test rather then integration test.
                    test_report_dir = self._attempt_get_test_report_directory(
                        plugin_name=MavenTestReportingMixin.SUREFIRE_PLUGIN_NAME,
                        configuration_key=\
                            MavenTestReportingMixin.SUREFIRE_PLUGIN_REPORTS_DIR_CONFIG_NAME,
                        default=MavenTestReportingMixin.SUREFIRE_PLUGIN_DEFAULT_REPORTS_DIR,
                        require_phase_execution_config=True
                    )
                except StepRunnerException:
                    print(
                        'WARNING: Did not find any expected test reporting plugin'
                        f' ({MavenTestReportingMixin.FAILSAFE_PLUGIN_NAME},'
                        f' {MavenTestReportingMixin.SUREFIRE_PLUGIN_NAME})'
                        ' to read artifacts and evidence from.'
                        ' This is not wholly unexpected because there is enumerable maven plugins,'
                        ' and enumerable ways to configure them.'
                        ' Rather then relying on this step implementer to try and figure out'
                        ' where the test reports are you can configure it manually via the'
                        ' step implementer config (test-reports-dir).'
                    )

        return test_report_dir
