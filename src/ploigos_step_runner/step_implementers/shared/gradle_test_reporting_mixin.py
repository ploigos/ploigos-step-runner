"""A mixin class designed to add Gradle test reporting functionality to
GradleGeneric based StepImplementers.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default          | Description
-----------------------------|-----------|------------------|-----------
`build-file`                 | Yes       | `'build.gradle'` | Bulid file for Gradle
`gradle-tasks`               | No        | ['build']        | Tasks to execute in Gradle
"""# pylint: disable=line-too-long

import os
import glob

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.gradle import get_plugin_configuration_absolute_path_values
from ploigos_step_runner.utils.xml import get_xml_element_if_present


class GradleTestReportingMixin:
    """A mixin class designed to add Gradle test reporting functionality to
    GradleGeneric based StepImplementers.
    """

    SUREFIRE_PLUGIN_NAME = 'gradle-surefire-plugin'
    SUREFIRE_PLUGIN_REPORTS_DIR_CONFIG_NAME = 'reportsDirectory'
    FAILSAFE_PLUGIN_NAME = 'gradle-failsafe-plugin'
    FAILSAFE_PLUGIN_REPORTS_DIR_CONFIG_NAME = 'reportsDirectory'
    SUREFIRE_PLUGIN_DEFAULT_REPORTS_DIR = 'target/surefire-reports'
    FAILSAFE_PLUGIN_DEFAULT_REPORTS_DIR = 'target/failsafe-reports'
    TESTSUITE_EVIDENCE_ATTRIBUTES = ["time", "tests", "failures", "errors", "skipped"]
    TESTSUITE_EVIDENCE_ATTRIBUTES_REQUIRED = ["time", "tests", "failures"]
    TESTSUITE_EVIDENCE_ELEMENTS = ["testsuites", "testsuite"]

    def _attempt_get_test_report_directory(
        self,
        plugin_name,
        configuration_key,
        default,
    ):
        """Does it's darndest to dynamically determine the test report directory.

        Parameters
        ----------
        plugin_name : str
            Name of the Gradle plugin to look for test report directory configuration.
        configuration_key : str
            Gradle plugin configuration to look for the test directory path.
        default : str
            Value to use if can't find any user configured configuration.

        Returns
        -------
        str
            Determined test reports directory path.

        Raises
        ------
        StepRunnerException
            If can not find the given plugin to get configuration from.
        """
        test_report_dir = None

        print(
            'Attempt to get test report directory configuration'
            f' ({configuration_key}) for'
            f' gradle test plugin ({plugin_name}).'
        )

        try:
            test_report_dirs = get_plugin_configuration_absolute_path_values(
                plugin_name=plugin_name,
                configuration_key=configuration_key,
                work_dir_path=self.work_dir_path,
                build_file='build.gradle'
            )

            # if found at least one test report dir
            # else plugin exists but could not find config, use default
            if test_report_dirs:
                if len(test_report_dirs) > 1:
                    print(
                        'WARNING: In best attempt to dynamically determine where the the test'
                        ' report directory is, we were to successful and found more then one.'
                        ' This is not wholly unexpected because there is enumerable gradle plugins,'
                        ' and enumerable ways to configure them.'
                        ' Randomly picking first match and hoping it is correct.'
                        ' Rather then relying on this step implementer to try and figure out'
                        ' where the test reports are you can configure it manually via the'
                        ' step implementer config (test-reports-dir).'
                    )

                test_report_dir = test_report_dirs[0]
            else:
                print(
                    'Did not find test report directory configuration'
                    f' ({configuration_key}) for gradle test plugin ({plugin_name}),'
                    f' using default ({default}).'
                )
                test_report_dir = default

        except RuntimeError as error:
            # NOTE: this should only happen if couldn't find the plugin
            raise StepRunnerException(
                f'Error getting configuration ({configuration_key}) from'
                f' gradle plugin ({plugin_name}): {error}'
            ) from error

        #properties = {}

        #properties_file = 'gradle.properrties'

        # if not os.path.exists(properties_file):

        #     return test_report_dir

        # with open(properties_file, 'r', encoding='utf-8') as inf:

        #     for line in inf.readlines():
        #         # Skip comments and empty lines
        #         line = line.strip()
        #         if line and not line.startswith("#"):
        #             key, value = line.split("=", 1)  # Split on the first '='
        #             properties[key] = value

        # test_report_dir = properties.get('test_report_dir', default)

        return test_report_dir

    @staticmethod
    def _gather_evidence_from_test_report_directory_testsuite_elements(
        step_result,
        test_report_dirs
    ):
        """Given a test report directory containing XML files with 'testsuite' xml elements
        collects evidence from those files and elements.

        Parameters
        ----------
        step_result : StepResult
            StepResult to add the evidence to.
        test_report_dirs : str or [str]
            Directory(s) to search for 'testsuite' xml elements in to collect evidence from.
        """

        # standardize input
        if not isinstance(test_report_dirs, list):
            test_report_dirs = [test_report_dirs]

         # gather evidence
        report_results, collection_warnings = GradleTestReportingMixin._collect_report_results(
            test_report_dirs=test_report_dirs
        )

        # Add the test results to the evidence
        missing_attributes = []
        for attribute in GradleTestReportingMixin.TESTSUITE_EVIDENCE_ATTRIBUTES:
            if attribute in report_results:
                step_result.add_evidence(
                    name=attribute,
                    value=report_results[attribute]
                )
            elif attribute in GradleTestReportingMixin.TESTSUITE_EVIDENCE_ATTRIBUTES_REQUIRED:
                missing_attributes.append(attribute)

        # Add a warning to the step_result for required attributes that were not found
        if missing_attributes:
            step_result.message += "\nWARNING: could not find expected evidence" \
                f" attributes ({missing_attributes}) on a recognized xml root element" \
                f" ({GradleTestReportingMixin.TESTSUITE_EVIDENCE_ELEMENTS}) in test report" \
                f" directory ({test_report_dirs})."

        # Add any warnings encountered during collecting the test results to the step_result
        for warning in collection_warnings:
            step_result.message += f"\n{warning}"

    @staticmethod
    def _collect_report_results(
        test_report_dirs
    ):
        report_results = {}
        warnings = []

        # collect all the xml file paths
        xml_files = []
        for xml_file_path in test_report_dirs:
            if os.path.isdir(xml_file_path):
                xml_files += glob.glob(xml_file_path + '/*.xml', recursive=False)
            elif os.path.isfile(xml_file_path):
                xml_files += [xml_file_path]

        # Iterate over each file that contains test results
        for file in xml_files:
            element = GradleTestReportingMixin._read_evidence_element(file)

            # If this file does not have an element that contains evidence, warn but continue processing other files.
            if element is None: # Elements that exist but have no child elements are falsy!
                warnings += [f"WARNING: could not parse test results in file ({file}). Ignoring."]
                continue

            # Iterate over the XML attributes that are evidence
            for attrib in element.attrib:
                if attrib in GradleTestReportingMixin.TESTSUITE_EVIDENCE_ATTRIBUTES: # Is this attribute evidence?

                    # Parse each attribute as a number
                    attrib_value = 0
                    try:
                        attrib_value = GradleTestReportingMixin._to_number(element.attrib[attrib])
                    except ValueError:
                        warnings += [
                            "WARNING: While parsing test results, expected the value of"
                            f" attribute ({attrib}) in file ({file}) to be a number."
                            f" Value was '{element.attrib[attrib]}'. Ignoring."
                        ]

                    # Add up the totals across all files
                    if attrib in report_results:
                        report_results[attrib] += attrib_value
                    else:
                        report_results[attrib] = attrib_value

        return report_results, warnings

    @staticmethod
    def _read_evidence_element(file):
        # Check if the base xml element of the file has one of the element names that is allowed
        for candidate in GradleTestReportingMixin.TESTSUITE_EVIDENCE_ELEMENTS:
            element = get_xml_element_if_present(file, candidate)
            if element is not None: # Elements that exist but have no child elements are falsy!
                return element
        return None

    @staticmethod
    def _to_number(string):
        if string.isnumeric():
            return int(string)
        return float(string)
