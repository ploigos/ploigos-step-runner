
import os
from unittest.mock import MagicMock, patch

from ploigos_step_runner import StepRunnerException
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementers.shared import \
    MavenTestReportingMixin
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


@patch("ploigos_step_runner.step_implementers.shared.maven_test_reporting_mixin.get_plugin_configuration_absolute_path_values")
class TestMavenTestReportingMixin__attempt_get_test_report_directory(BaseStepImplementerTestCase):
    @staticmethod
    def __get_maven_test_reporting_mixin():
        # create mixin object
        maven_test_reporting_mixin = MavenTestReportingMixin()

        # mock work_dir_path
        maven_test_reporting_mixin.work_dir_path = '/mock/work-dir-path'

        # mock get_value

        def get_value_side_effect(key):
            if key == 'pom-file':
                return 'mock-pom.xml'
            elif key == 'maven-profiles':
                return []
            else:
                return None
        maven_test_reporting_mixin.get_value = MagicMock(
            name='get_value',
            side_effect = get_value_side_effect
        )

        # mock maven_phases_and_goals
        maven_test_reporting_mixin.maven_phases_and_goals = []

        return maven_test_reporting_mixin

    def test_one_found_result(self, get_plugin_configuration_absolute_path_values_mock):
        # create object to test against
        maven_test_reporting_mixin = self.__get_maven_test_reporting_mixin()

        # setup mocks
        get_plugin_configuration_absolute_path_values_mock.return_value = ['/mock/test-dir']

        # run test
        actual_test_report_dir = maven_test_reporting_mixin._attempt_get_test_report_directory(
            plugin_name='mock-maven-test-plugin',
            configuration_key='mock-reports-dir-config-key',
            default='/mock/default',
            require_phase_execution_config=False
        )

        # verify results
        get_plugin_configuration_absolute_path_values_mock.assert_called_once_with(
            plugin_name='mock-maven-test-plugin',
            configuration_key='mock-reports-dir-config-key',
            work_dir_path='/mock/work-dir-path',
            pom_file='mock-pom.xml',
            profiles=[],
            phases_and_goals=[],
            require_phase_execution_config=False
        )

        self.assertEqual(actual_test_report_dir, '/mock/test-dir')

    def test_two_found_results(self, get_plugin_configuration_absolute_path_values_mock):
        # create object to test against
        maven_test_reporting_mixin = self.__get_maven_test_reporting_mixin()

        # setup mocks
        get_plugin_configuration_absolute_path_values_mock.return_value = [
            '/mock/test-dir1',
            '/mock/test-dir2'
        ]

        # run test
        actual_test_report_dir = maven_test_reporting_mixin._attempt_get_test_report_directory(
            plugin_name='mock-maven-test-plugin',
            configuration_key='mock-reports-dir-config-key',
            default='/mock/default',
            require_phase_execution_config=False
        )

        # verify results
        get_plugin_configuration_absolute_path_values_mock.assert_called_once_with(
            plugin_name='mock-maven-test-plugin',
            configuration_key='mock-reports-dir-config-key',
            work_dir_path='/mock/work-dir-path',
            pom_file='mock-pom.xml',
            profiles=[],
            phases_and_goals=[],
            require_phase_execution_config=False
        )

        self.assertEqual(actual_test_report_dir, '/mock/test-dir1')

    def test_found_plugin_but_no_config_use_default(self, get_plugin_configuration_absolute_path_values_mock):
        # create object to test against
        maven_test_reporting_mixin = self.__get_maven_test_reporting_mixin()

        # setup mocks
        get_plugin_configuration_absolute_path_values_mock.return_value = []

        # run test
        actual_test_report_dir = maven_test_reporting_mixin._attempt_get_test_report_directory(
            plugin_name='mock-maven-test-plugin',
            configuration_key='mock-reports-dir-config-key',
            default='/mock/default',
            require_phase_execution_config=False
        )

        # verify results
        get_plugin_configuration_absolute_path_values_mock.assert_called_once_with(
            plugin_name='mock-maven-test-plugin',
            configuration_key='mock-reports-dir-config-key',
            work_dir_path='/mock/work-dir-path',
            pom_file='mock-pom.xml',
            profiles=[],
            phases_and_goals=[],
            require_phase_execution_config=False
        )

        self.assertEqual(actual_test_report_dir, '/mock/default')

    def test_plugin_not_found(self, get_plugin_configuration_absolute_path_values_mock):
        # create object to test against
        maven_test_reporting_mixin = self.__get_maven_test_reporting_mixin()

        # setup mocks
        get_plugin_configuration_absolute_path_values_mock.side_effect = RuntimeError(
            'mock could not find plugin error'
        )

        # run test
        with self.assertRaisesRegex(
            StepRunnerException,
            r"Error getting configuration \(mock-reports-dir-config-key\) from maven"
            r" plugin \(mock-maven-test-plugin\):"
            r" mock could not find plugin error"
        ):
            maven_test_reporting_mixin._attempt_get_test_report_directory(
                plugin_name='mock-maven-test-plugin',
                configuration_key='mock-reports-dir-config-key',
                default='/mock/default',
                require_phase_execution_config=False
            )

        # verify results
        get_plugin_configuration_absolute_path_values_mock.assert_called_once_with(
            plugin_name='mock-maven-test-plugin',
            configuration_key='mock-reports-dir-config-key',
            work_dir_path='/mock/work-dir-path',
            pom_file='mock-pom.xml',
            profiles=[],
            phases_and_goals=[],
            require_phase_execution_config=False
        )

@patch("ploigos_step_runner.step_implementers.shared.maven_test_reporting_mixin.aggregate_xml_element_attribute_values")
class TestMavenTestReportingMixin__gather_evidence_from_test_report_directory_testsuite_elements(
    BaseStepImplementerTestCase
):
    def test_found_all_attributes(self, aggregate_xml_element_attribute_values_mock):
        with TempDirectory() as test_dir:
            # setup test
            actual_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            test_report_dir = os.path.join(
                test_dir.path,
                'mock-test-results'
            )

            # setup mocks
            os.mkdir(test_report_dir)
            aggregate_xml_element_attribute_values_mock.return_value = {
                "time": 1.42,
                "tests": 42,
                "errors": 3,
                "skipped": 2,
                "failures": 1
            }

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dir=test_report_dir
            )

            # verify results
            expected_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            expected_step_result.add_evidence(name='time', value=1.42)
            expected_step_result.add_evidence(name='tests', value=42)
            expected_step_result.add_evidence(name='errors', value=3)
            expected_step_result.add_evidence(name='skipped', value=2)
            expected_step_result.add_evidence(name='failures', value=1)
            self.assertEqual(actual_step_result, expected_step_result)

    def test_found_dir_found_no_attributes(self, aggregate_xml_element_attribute_values_mock):
        with TempDirectory() as test_dir:
            # setup test
            actual_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            test_report_dir = os.path.join(
                test_dir.path,
                'mock-test-results'
            )

            # setup mocks
            os.mkdir(test_report_dir)
            aggregate_xml_element_attribute_values_mock.return_value = {
                "time": 1.42,
                "tests": 42
            }

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dir=test_report_dir
            )

            # verify results
            expected_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            expected_step_result.add_evidence(name='time', value=1.42)
            expected_step_result.add_evidence(name='tests', value=42)
            test_report_evidence_element = 'testsuite'
            not_found_attribs = ["errors", "skipped", "failures"]
            expected_step_result.message += "\nWARNING: could not find expected evidence" \
                f" attributes ({not_found_attribs}) on xml element" \
                f" ({test_report_evidence_element}) in test report" \
                f" directory ({test_report_dir})."
            self.assertEqual(actual_step_result, expected_step_result)

    def test_found_dir_found_some_attributes(self, aggregate_xml_element_attribute_values_mock):
        with TempDirectory() as test_dir:
            # setup test
            actual_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            test_report_dir = os.path.join(
                test_dir.path,
                'mock-test-results'
            )

            # setup mocks
            os.mkdir(test_report_dir)
            aggregate_xml_element_attribute_values_mock.return_value = {}

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dir=test_report_dir
            )

            # verify results
            expected_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            test_report_evidence_element = 'testsuite'
            not_found_attribs = ["time", "tests", "errors", "skipped", "failures"]
            expected_step_result.message += "\nWARNING: could not find expected evidence" \
                f" attributes ({not_found_attribs}) on xml element" \
                f" ({test_report_evidence_element}) in test report" \
                f" directory ({test_report_dir})."
            self.assertEqual(actual_step_result, expected_step_result)

    def test_test_report_dir_does_not_exist(self, aggregate_xml_element_attribute_values_mock):
        with TempDirectory() as test_dir:
            # setup test
            actual_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            test_report_dir = os.path.join(
                test_dir.path,
                'mock-test-results'
            )

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dir=test_report_dir
            )

            # verify results
            expected_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            expected_step_result.message += f"\nWARNING: test report directory ({test_report_dir})" \
                " does not exist to gather evidence from"
            self.assertEqual(actual_step_result, expected_step_result)
