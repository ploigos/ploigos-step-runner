
"""PSR step for running Unit Tests with Gradle"""
import xml.etree.ElementTree as ET

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results.step_result import StepResult
from ploigos_step_runner.step_implementers.shared.gradle_generic import GradleGeneric
from ploigos_step_runner.step_implementers.shared.gradle_test_reporting_mixin import GradleTestReportingMixin

DEFAULT_CONFIG = {
    'build-file': 'app/build.gradle',
}


REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'build-file'
]

class GradleTest(GradleGeneric, GradleTestReportingMixin):
    """`StepImplementer` for the `uat` step using Gradle by invoking the 'test` gradle phase.
    """

    TEST_RESULTS_ROOT_TAG = "testsuite"
    TEST_RESULTS_ATTRIBUTES = ["time", "tests", "failures", "errors", "skipped"]
    TEST_RESULTS_ATTRIBUTES_REQUIRED = ["time", "tests", "failures"]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None,
        gradle_tasks=None
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
        return {**GradleGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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
        gradle_output_file_path = self.write_working_file('gradle_output.txt')
        try:
            # execute maven step (params come from config)
            self._run_gradle_step(
                gradle_output_file_path=gradle_output_file_path
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running Gradle. " \
                                  f"More details maybe found in report artifacts: {error}"
        finally:

            step_result.add_artifact(
                description="Standard out and standard error from Gradle.",
                name='gradle-output',
                value=gradle_output_file_path
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
        * gradle.properties -> 

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
            test_report_dirs = self._attempt_get_test_report_directory(
                plugin_name=GradleTestReportingMixin.SUREFIRE_PLUGIN_NAME,
                configuration_key=\
                GradleTestReportingMixin.SUREFIRE_PLUGIN_REPORTS_DIR_CONFIG_NAME,
                default=GradleTestReportingMixin.SUREFIRE_PLUGIN_DEFAULT_REPORTS_DIR
            )

        return test_report_dirs

#    def _get_test_report_dir(self):
#       return self.get_value('test-reports-dir')

    def _get_test_results_from_file(self, filename, attributes):
        test_results = dict()
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            if root.tag == self.TEST_RESULTS_ROOT_TAG:
                for attribute in attributes:
                    test_results[attribute] = self._get_test_result(root, attribute)
        except FileNotFoundError as fnfe:
            print(f"WARNING: Error parsing file {filename} \n {fnfe}")
        except Exception as err:
            print(f"WARNING: Error parsing file {filename} \n {err}")

        return test_results

    def _get_test_result(self, root, attribute):
        value = root.attrib[attribute]
        return value

    def _get_missing_required_test_attributes(self, test_results, required_attributes):
        missing_attributes = list()
        for attrib in required_attributes:
            if attrib not in test_results.keys():
                missing_attributes.append(attrib)

        return missing_attributes

    def _get_dict_with_keys_from_list(self, l):
        d = dict()
        for item in l:
            d[item] = 0
        return d

    def _combine_test_results(self, total, current):
        try:
            for k in total.keys():
                if k in current:
                    string = current[k]

                    if '.' in string:

                        num = float(string)
                        total[k] = float(total[k]) + num
                    else:
                        num = int(string)
                        total[k] = int(total[k]) + num
        except ValueError as ve:
            print(f"WARNING: Error converting string to number in file \n {ve}")

        return total
