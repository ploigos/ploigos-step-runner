"""`StepImplementer` for the `uat` step using Maven by invoking the 'test` maven phase."

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default | Description
-----------------------------|-----------|---------|-----------
`pom-file`                   | Yes       | `'pom.xml'` | pom used when executing maven.
`tls-verify`                 | No        | `True`  | Disables TLS Verification if set to False
`maven-profiles`             | No        | `[]`    | List of maven profiles to use.
`maven-no-transfer-progress` | No        | `True`  | `True` to suppress the transfer progress of packages maven downloads.
                                                     `False` to have the transfer progress printed.\
                                                      See https://maven.apache.org/ref/current/maven-embedder/cli.html
`maven-additional-arguments` | No        | `[]`    | List of additional arguments to use.
`maven-servers`              | No        |         | Dictionary of dictionaries of id, username, password
`maven-repositories`         | No        |         | Dictionary of dictionaries of id, url, snapshots, releases
`maven-mirrors`              | No        |         | Dictionary of dictionaries of id, url, mirror_of
`test-reports-dirs`          | No        |         | Default is to try and dynamically determine where the test reports directory is \
                                                     based on configuration in the given `pom-file`, but it is impossible task to do \
                                                     in all cases. \
                                                     So, this parameter provides a way for the user to specify where the test results \
                                                     are if our attempts at dynamically figuring it out are failing your unique pom.
`test-reports-dir`           | No        |         | Alias for `test-reports-dirs`


Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`maven-output`      | Path to Stdout and Stderr from invoking Maven.
`test-report`       | Directory containing the test reports generated from running this step.
"""# pylint: disable=line-too-long

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared import (
    MavenGeneric, MavenTestReportingMixin)

DEFAULT_CONFIG = {}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'pom-file'
]

class MavenTest(MavenGeneric, MavenTestReportingMixin):
    """`StepImplementer` for the `uat` step using Maven by invoking the 'test` maven phase.
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
            maven_phases_and_goals=['test']
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

        # run the tests
        print("Run unit tests")
        mvn_output_file_path = self.write_working_file('mvn_output.txt')
        try:
            # execute maven step (params come from config)
            self._run_maven_step(
                mvn_output_file_path=mvn_output_file_path
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
        test_report_dirs = self.__get_test_report_dirs()
        if test_report_dirs:
            step_result.add_artifact(
                description="Test report generated when running unit tests.",
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

    def __get_test_report_dirs(self):
        """Gets the test report directory(s)

        Search Priority:
        * values -> 'test-reports-dir'
        * pom.xml -> maven-surefire-plugin -> reportsDirectory

        Returns
        -------
        [str] or str
            Path(s) to the directory containing the test reports.
        """
        # user supplied where the test reports go, just use that
        test_report_dirs = self.get_value(['test-reports-dir','test-reports-dirs'])

        # else do our best to find them
        if not test_report_dirs:
            # attempt to get failsafe test report dir, if not, try for surefire
            test_report_dirs = None
            try:
                test_report_dirs = self._attempt_get_test_report_directory(
                    plugin_name=MavenTestReportingMixin.SUREFIRE_PLUGIN_NAME,
                    configuration_key=\
                        MavenTestReportingMixin.SUREFIRE_PLUGIN_REPORTS_DIR_CONFIG_NAME,
                    default=MavenTestReportingMixin.SUREFIRE_PLUGIN_DEFAULT_REPORTS_DIR
                )
            except StepRunnerException:
                print(
                    'WARNING: Did not find any expected test reporting plugin'
                    f' ({MavenTestReportingMixin.SUREFIRE_PLUGIN_NAME})'
                    ' to read artifacts and evidence from.'
                    ' This is not wholly unexpected because there is enumerable maven plugins,'
                    ' and enumerable ways to configure them.'
                    ' Rather then relying on this step implementer to try and figure out'
                    ' where the test reports are you can configure it manually via the'
                    ' step implementer config (test-reports-dir).'
                )

        return test_report_dirs
