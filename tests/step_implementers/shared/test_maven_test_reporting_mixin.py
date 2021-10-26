
import os
import unittest
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

@patch.object(MavenTestReportingMixin, '_collect_report_results')
class TestMavenTestReportingMixin__gather_evidence_from_test_report_directory_testsuite_elements(
    unittest.TestCase
):
    def test_found_all_attributes(self, mock_collect_report_results):
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
            mock_collect_report_results.return_value = [
                {
                    "time": 1.42,
                    "tests": 42,
                    "errors": 3,
                    "skipped": 2,
                    "failures": 1
                },
                []
            ]

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dirs=test_report_dir
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
            mock_collect_report_results.assert_called_once_with(
                test_report_dirs=[test_report_dir]
            )

    def test_found_dir_found_no_attributes(self, mock_collect_report_results):
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
            mock_collect_report_results.return_value = [
                {
                    "time": 1.42,
                    "tests": 42,
                },
                []
            ]

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dirs=test_report_dir
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
                f" directory (['{test_report_dir}'])."
            self.assertEqual(actual_step_result, expected_step_result)
            mock_collect_report_results.assert_called_once_with(
                test_report_dirs=[test_report_dir]
            )

    def test_found_dir_found_some_attributes(self, mock_collect_report_results):
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
            mock_collect_report_results.return_value = [
                {},
                []
            ]

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dirs=test_report_dir
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
                f" directory (['{test_report_dir}'])."
            self.assertEqual(actual_step_result, expected_step_result)
            mock_collect_report_results.assert_called_once_with(
                test_report_dirs=[test_report_dir]
            )

    def test_test_report_dir_does_not_exist(self, mock_collect_report_results):
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
            mock_collect_report_results.return_value = [
                {},
                []
            ]

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dirs=test_report_dir
            )

            # verify results
            expected_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            expected_step_result.message += "\nWARNING: could not find expected evidence" \
                " attributes (['time', 'tests', 'errors', 'skipped', 'failures'])" \
                f" on xml element (testsuite) in test report directory (['{test_report_dir}'])."
            self.assertEqual(actual_step_result, expected_step_result)
            mock_collect_report_results.assert_called_once_with(
                test_report_dirs=[test_report_dir]
            )

    def test_found_all_attributes_multiple_test_dirs(self, mock_collect_report_results):
        with TempDirectory() as test_dir:
            # setup test
            actual_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            test_report_dir1 = os.path.join(
                test_dir.path,
                'mock-test-results1'
            )
            os.mkdir(test_report_dir1)
            test_report_dir2 = os.path.join(
                test_dir.path,
                'mock-test-results2'
            )
            os.mkdir(test_report_dir2)
            test_report_dirs = [
                test_report_dir1,
                test_report_dir2
            ]

            # setup mocks
            mock_collect_report_results.return_value = [
                {
                    "time": 1.42,
                    "tests": 42,
                    "errors": 3,
                    "skipped": 2,
                    "failures": 1
                },
                []
            ]

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dirs=test_report_dirs
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
            mock_collect_report_results.assert_called_once_with(
                test_report_dirs=test_report_dirs
            )

    def test_found_warning(self, mock_collect_report_results):
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
            mock_collect_report_results.return_value = [
                {
                    "time": 1.42,
                    "tests": 42,
                    "errors": 3,
                    "skipped": 2,
                    "failures": 1
                },
                ['WARNING: mock warning about nothing']
            ]

            # run test
            MavenTestReportingMixin._gather_evidence_from_test_report_directory_testsuite_elements(
                step_result=actual_step_result,
                test_report_dirs=test_report_dir
            )

            # verify results
            expected_step_result = StepResult(
                step_name='mock-maven-test-step',
                sub_step_name='mock-maven-test-sub-step',
                sub_step_implementer_name='MockMavenTestReportingMixinStepImplementer'
            )
            expected_step_result.message = '\nWARNING: mock warning about nothing'
            expected_step_result.add_evidence(name='time', value=1.42)
            expected_step_result.add_evidence(name='tests', value=42)
            expected_step_result.add_evidence(name='errors', value=3)
            expected_step_result.add_evidence(name='skipped', value=2)
            expected_step_result.add_evidence(name='failures', value=1)
            self.assertEqual(actual_step_result, expected_step_result)
            mock_collect_report_results.assert_called_once_with(
                test_report_dirs=[test_report_dir]
            )

# NOTE: really should mock _to_number and get_xml_element but that would be a lot of work
class TestMavenTestReportingMixin__collect_report_results(unittest.TestCase):
    def test_give_dir_with_single_file_find_all_attributes(self):
        with TempDirectory() as test_dir:
            # setup test
            test_dir.write(
                'test_result1.xml',
                b'<testsuite time="1.42" tests="42" errors="3" skipped="2" failures="1" />'
            )

            # run test
            report_results, warnings = MavenTestReportingMixin._collect_report_results(
                test_report_dirs=[test_dir.path]
            )

            # verify results
            self.assertEqual(
                report_results,
                {'time': 1.42, 'tests': 42, 'errors': 3, 'skipped': 2, 'failures': 1}
            )
            self.assertEqual(warnings, [])

    def test_give_single_file_find_all_attributes(self):
        with TempDirectory() as test_dir:
            # setup test
            test_dir.write(
                'test_result1.xml',
                b'<testsuite time="1.42" tests="42" errors="3" skipped="2" failures="1" />'
            )

            # run test
            report_results, warnings = MavenTestReportingMixin._collect_report_results(
                test_report_dirs=[os.path.join(test_dir.path, 'test_result1.xml')]
            )

            # verify results
            self.assertEqual(
                report_results,
                {'time': 1.42, 'tests': 42, 'errors': 3, 'skipped': 2, 'failures': 1}
            )
            self.assertEqual(warnings, [])

    def test_multiple_files_find_all_attributes(self):
        with TempDirectory() as test_dir:
            # setup test
            test_dir.write(
                'test_result1.xml',
                b'<testsuite time="1.42" tests="42" errors="3" skipped="2" failures="1" />'
            )
            test_dir.write(
                'test_result2.xml',
                b'<testsuite time="2.42" tests="24" errors="1" skipped="1" failures="2" />'
            )

            # run test
            report_results, warnings = MavenTestReportingMixin._collect_report_results(
                test_report_dirs=[test_dir.path]
            )

            # verify results
            self.assertEqual(
                report_results,
                {'time': 3.84, 'tests': 66, 'errors': 4, 'skipped': 3, 'failures': 3}
            )
            self.assertEqual(warnings, [])

    def test_single_file_with_warning_about_not_being_able_to_parse_file(self):
        with TempDirectory() as test_dir:
            # setup test
            test_dir.write(
                'test_result1.xml',
                b'<not-a-test-suite time="1.42" tests="42" errors="3" skipped="2" failures="1" />'
            )

            # run test
            report_results, warnings = MavenTestReportingMixin._collect_report_results(
                test_report_dirs=[test_dir.path]
            )

            # verify results
            mock_result_file_path = os.path.join(test_dir.path, "test_result1.xml")
            self.assertEqual(report_results, {})
            self.assertEqual(
                warnings,
                [
                    f'WARNING: could not parse test results in file ({mock_result_file_path}).'
                    ' Ignoring.'
                ]
            )

    def test_single_file_with_warning_about_not_being_able_to_parse_attribute(self):
        with TempDirectory() as test_dir:
            # setup test
            test_dir.write(
                'test_result1.xml',
                b'<testsuite time="mock-bad" tests="42" errors="3" skipped="2" failures="1" />'
            )

            # run test
            report_results, warnings = MavenTestReportingMixin._collect_report_results(
                test_report_dirs=[test_dir.path]
            )

            # verify results
            mock_result_file_path = os.path.join(test_dir.path, "test_result1.xml")
            self.assertEqual(
                report_results,
                {'time': 0, 'tests': 42, 'errors': 3, 'skipped': 2, 'failures': 1}
            )
            self.assertEqual(
                warnings,
                [
                    "WARNING: While parsing test results, expected the value of"
                    f" attribute (time) in file ({mock_result_file_path}) to be a number."
                    f" Value was 'mock-bad'. Ignoring."
                ]
            )
