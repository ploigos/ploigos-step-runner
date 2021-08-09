"""A mixin class designed to add Maven test reporting functionality to
MavenGeneric based StepImplementers.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default     | Description
-----------------------------|-----------|-------------|-----------
`pom-file`                   | Yes       | `'pom.xml'` | pom used when executing maven.
`tls-verify`                 | No        | `True`      | Disables TLS Verification if set to False
`maven-phases-and-goals`     | Yes       |             | List of maven phases and/or goals to execute.
`maven-profiles`             | No        | `[]`        | List of maven profiles to use.
"""# pylint: disable=line-too-long

import os

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.maven import \
    get_plugin_configuration_absolute_path_values
from ploigos_step_runner.utils.xml import \
    aggregate_xml_element_attribute_values


class MavenTestReportingMixin:
    """A mixin class designed to add Maven test reporting functionality to
    MavenGeneric based StepImplementers.
    """

    SUREFIRE_PLUGIN_NAME = 'maven-surefire-plugin'
    SUREFIRE_PLUGIN_REPORTS_DIR_CONFIG_NAME = 'reportsDirectory'
    FAILSAFE_PLUGIN_NAME = 'maven-failsafe-plugin'
    FAILSAFE_PLUGIN_REPORTS_DIR_CONFIG_NAME = 'reportsDirectory'
    SUREFIRE_PLUGIN_DEFAULT_REPORTS_DIR = 'target/surefire-reports'
    FAILSAFE_PLUGIN_DEFAULT_REPORTS_DIR = 'target/failsafe-reports'
    TESTSUITE_EVIDENCE_ATTRIBUTES = ["time", "tests", "errors", "skipped", "failures"]

    def _attempt_get_test_report_directory(
        self,
        plugin_name,
        configuration_key,
        default,
        require_phase_execution_config=False
    ):
        """Does it's darndest to dynamically determine the test report directory.

        Parameters
        ----------
        plugin_name : str
            Name of the Maven plugin to look for test report directory configuration.
        configuration_key : str
            Maven plugin configuration to look for the test directory path.
        default : str
            Value to use if can't find any user configured configuration.
        require_phase_execution_config : str
            True if the user supplied configuration via the pom should be for
            the specified phase or goals.
            False if the user supplied configuration via the pom does not
            need to be specific for the phase and goal.

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
            f' maven test plugin ({plugin_name}).'
        )
        try:
            test_report_dirs = get_plugin_configuration_absolute_path_values(
                plugin_name=plugin_name,
                configuration_key=configuration_key,
                work_dir_path=self.work_dir_path,
                pom_file=self.get_value('pom-file'),
                profiles=self.get_value('maven-profiles'),
                phases_and_goals=self.maven_phases_and_goals,
                require_phase_execution_config=require_phase_execution_config
            )

            # if found at least one test report dir
            # else plugin exists but could not find config, use default
            if test_report_dirs:
                if len(test_report_dirs) > 1:
                    print(
                        'WARNING: In best attempt to dynamically determine where the the test'
                        ' report directory is, we were to successful and found more then one.'
                        ' This is not wholly unexpected because there is enumerable maven plugins,'
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
                    f' ({configuration_key}) for maven test plugin ({plugin_name}),'
                    f' using default ({default}).'
                )
                test_report_dir = default

        except RuntimeError as error:
            # NOTE: this should only happen if couldn't find the plugin
            raise StepRunnerException(
                f'Error getting configuration ({configuration_key}) from'
                f' maven plugin ({plugin_name}): {error}'
            ) from error

        return test_report_dir

    @staticmethod
    def _gather_evidence_from_test_report_directory_testsuite_elements(
        step_result,
        test_report_dir
    ):
        """Given a test report directory containing XML files with 'testsuite' xml elements
        collects evidence from those files and elements.

        Parameters
        ----------
        step_result : StepResult
            StepResult to add the evidence to.
        test_report_dir : str
            Directory to search for 'testsuite' xml elements in to collect evidence from.
        """
        if os.path.exists(test_report_dir):
            test_report_evidence_attributes = MavenTestReportingMixin.TESTSUITE_EVIDENCE_ATTRIBUTES
            test_report_evidence_element = 'testsuite'

            not_found_attribs = []
            report_results = aggregate_xml_element_attribute_values(
                xml_file_paths=test_report_dir,
                xml_element=test_report_evidence_element,
                attribs=test_report_evidence_attributes
            )

            for attribute in test_report_evidence_attributes:
                if attribute in report_results:
                    step_result.add_evidence(
                        name=attribute,
                        value=report_results[attribute]
                    )
                else:
                    not_found_attribs.append(attribute)
            if not_found_attribs:
                step_result.message += "\nWARNING: could not find expected evidence" \
                    f" attributes ({not_found_attribs}) on xml element" \
                    f" ({test_report_evidence_element}) in test report" \
                    f" directory ({test_report_dir})."
        else:
            step_result.message += f"\nWARNING: test report directory ({test_report_dir})" \
                " does not exist to gather evidence from"
