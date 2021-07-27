"""`StepImplementer` for the `unit-test` step using Maven with Surefire plugin.

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
`maven-no-transfer-progress` | No        | `True`  | \
                            `True` to suppress the transfer progress of packages maven downloads.
                            `False` to have the transfer progress printed.\
                            See https://maven.apache.org/ref/current/maven-embedder/cli.html
`maven-additional-arguments` | No        | `[]`    | List of additional arguments to use.
`maven-servers`              | No        |         | Dictionary of dictionaries of \
                                                     id, username, password
`maven-repositories`         | No        |         | Dictionary of dictionaries of \
                                                     id, url, snapshots, releases
`maven-mirrors`              | No        |         | Dictionary of dictionaries of \
                                                     id, url, mirror_of
`fail-on-no-tests`           | Yes       | `True ` | `True` to fail if there are not tests to run. \
                                                     `False` to ignore if there are no tests to run.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`maven-output`      | Path to Stdout and Stderr from invoking Maven.
`surefile-reports`  | Path to Surefire reports generated from invoking Maven.
"""
import os

from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.step_implementers.shared.maven_generic import \
    MavenGeneric

DEFAULT_CONFIG = {
    'fail-on-no-tests': True
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'pom-file',
    'fail-on-no-tests'
]

class MavenTest(MavenGeneric):
    """`StepImplementer` for the `unit-test` step using Maven with Surefire plugin.
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

        pom_file = self.get_value('pom-file')
        fail_on_no_tests = self.get_value('fail-on-no-tests')

        # ensure surefire plugin enabled
        # NOTE: should this really be hard requirement?
        maven_surefire_plugin = self._get_effective_pom_element(
            element_path=MavenGeneric.SUREFIRE_PLUGIN_XML_ELEMENT_PATH
        )
        if maven_surefire_plugin is None:
            step_result.success = False
            step_result.message = 'Unit test dependency "maven-surefire-plugin" ' \
                f'missing from effective pom ({self._get_effective_pom()}).'
            return step_result

        # get surefire test results dir
        reports_dir = self._get_effective_pom_element(
            element_path=MavenGeneric.SUREFIRE_PLUGIN_REPORTS_DIR_XML_ELEMENT_PATH
        )
        if reports_dir is not None:
            if os.path.isabs(reports_dir.text):
                test_results_dir = reports_dir.text
            else:
                test_results_dir = os.path.join(
                    os.path.dirname(os.path.abspath(pom_file)),
                    reports_dir.text
                )
        else:
            test_results_dir = os.path.join(
                os.path.dirname(os.path.abspath(pom_file)),
                MavenGeneric.DEFAULT_SUREFIRE_PLUGIN_REPORTS_DIR
            )

        # run the tests
        mvn_output_file_path = self.write_working_file('mvn_output.txt')
        try:
            # execute maven step (params come from config)
            self._run_maven_step(
                mvn_output_file_path=mvn_output_file_path
            )

            # check if any tests were run
            if not os.path.isdir(test_results_dir) or len(os.listdir(test_results_dir)) == 0:
                if fail_on_no_tests:
                    step_result.message = 'No unit tests defined.'
                    step_result.success = False
                else:
                    step_result.message = "No unit tests defined, but 'fail-on-no-tests' is False."
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running 'maven test' to run unit tests. " \
                "More details maybe found in 'maven-output' and `surefire-reports` " \
                f"report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value=mvn_output_file_path
            )
            step_result.add_artifact(
                description="Surefire reports generated by maven.",
                name='surefire-reports',
                value=test_results_dir
            )

        return step_result
