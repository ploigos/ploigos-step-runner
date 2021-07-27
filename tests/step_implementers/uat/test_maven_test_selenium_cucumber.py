import os
from pathlib import Path
from unittest.mock import Mock, patch

from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.uat import MavenTestSeleniumCucumber
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class BaseTestStepImplementerSharedMavenTestSeleniumCucumber(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=MavenTestSeleniumCucumber,
            step_config=step_config,
            step_name='uat',
            implementer='MavenTestSeleniumCucumber',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

@patch("ploigos_step_runner.step_implementers.shared.MavenGeneric.__init__")
class TestStepImplementerMavenTestMavenTestSeleniumCucumber___init__(BaseStepImplementerTestCase):
    def test_defaults(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenTestSeleniumCucumber(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None,
            maven_phases_and_goals=['test']
        )

    def test_given_environment(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        MavenTestSeleniumCucumber(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='mock-env'
        )

        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='mock-env',
            maven_phases_and_goals=['test']
        )

class TestStepImplementerMavenTestMavenTestSeleniumCucumber_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenTestSeleniumCucumber.step_implementer_config_defaults(),
            {
                'pom-file': 'pom.xml',
                'tls-verify': True,
                'maven-profiles': [],
                'maven-additional-arguments': [],
                'maven-no-transfer-progress': True,
                'maven-profiles': ['integration-test'],
                'fail-on-no-tests': True
            }
        )

class TestStepImplementerMavenTestMavenTestSeleniumCucumber__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenTestSeleniumCucumber._required_config_or_result_keys(),
            [
                'pom-file',
                'fail-on-no-tests',
                'selenium-hub-url',
            ]
        )

@patch("ploigos_step_runner.step_implementers.shared.MavenGeneric._validate_required_config_or_previous_step_result_artifact_keys")
class TestStepImplementerSharedMavenGeneric__validate_required_config_or_previous_step_result_artifact_keys(
    BaseTestStepImplementerSharedMavenTestSeleniumCucumber
):
    def test_valid_target_host_url(self, mock_super_validate):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {
                'target-host-url': 'https://mock-target-host-url.ploigos.com'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
            mock_super_validate.assert_called_once_with()

    def test_valid_deployed_host_urls(self, mock_super_validate):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {
                'deployed-host-urls': ['https://mock-deployed-host-url1.ploigos.com']
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
            mock_super_validate.assert_called_once_with()

    def test_fail_no_target_host_url_or_deployed_host_urls(self, mock_super_validate):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                "Either 'target-host-url' or 'deployed-host-urls' needs " \
                    "to be supplied but neither were."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once_with()

@patch.object(MavenTestSeleniumCucumber, '_run_maven_step')
@patch.object(MavenTestSeleniumCucumber, 'write_working_file', return_value='/mock/mvn_output.txt')
@patch(
    'ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values',
    return_value={
        'time': '42',
        'tests': '42',
        'errors': '0',
        'skipped': '0',
        'failures': '0'
    })
class TestStepImplementerMavenTestMavenTestSeleniumCucumber__run_step(
    BaseTestStepImplementerSharedMavenTestSeleniumCucumber
):
    def __expected_step_result_base(self):
        expected_step_result = StepResult(
            step_name='uat',
            sub_step_name='MavenTestSeleniumCucumber',
            sub_step_implementer_name='MavenTestSeleniumCucumber'
        )

        return expected_step_result

    def __expected_step_result_with_artifacts(self, parent_work_dir_path, surefire_reports_dir):
        cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
        cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
        expected_step_result = self.__expected_step_result_base()
        expected_step_result.add_artifact(
            description="Standard out and standard error from maven.",
            name='maven-output',
            value='/mock/mvn_output.txt'
        )
        expected_step_result.add_artifact(
            description="Surefire reports generated by maven.",
            name='surefire-reports',
            value=surefire_reports_dir
        )
        expected_step_result.add_artifact(
            description="Cucumber (HTML) report generated by maven.",
            name='cucumber-report-html',
            value=cucumber_html_report_path
        )
        expected_step_result.add_artifact(
            description="Cucumber (JSON) report generated by maven.",
            name='cucumber-report-json',
            value=cucumber_json_report_path
        )

        return expected_step_result

    def __expected_step_result_with_artifacts_and_evidence(
        self,
        parent_work_dir_path,
        surefire_reports_dir
    ):
        expected_step_result = self.__expected_step_result_with_artifacts(
            parent_work_dir_path=parent_work_dir_path,
            surefire_reports_dir=surefire_reports_dir
        )
        expected_step_result.add_evidence(
            name='uat-evidence-time',
            description='Surefire report value for time',
            value='42'
        )
        expected_step_result.add_evidence(
            name='uat-evidence-tests',
            description='Surefire report value for tests',
            value='42'
        )
        expected_step_result.add_evidence(
            name='uat-evidence-errors',
            description='Surefire report value for errors',
            value='0'
        )
        expected_step_result.add_evidence(
            name='uat-evidence-skipped',
            description='Surefire report value for skipped',
            value='0'
        )
        expected_step_result.add_evidence(
            name='uat-evidence-failures',
            description='Surefire report value for failures',
            value='0'
        )

        return expected_step_result


    def __create_run_maven_side_effect(self, surefire_reports_dir):
        group_id = 'com.ploigos.app'
        artifact_id = 'my-app'
        surefire_artifact_names = [
            f'{group_id}.{artifact_id}.ClassNameTest.txt',
            f'TEST-{group_id}.{artifact_id}.ClassNameTest.xml'
        ]
        def run_maven_side_effect(**kargs):
            os.makedirs(surefire_reports_dir, exist_ok=True)

            for artifact_name in surefire_artifact_names:
                artifact_path = os.path.join(
                    surefire_reports_dir,
                    artifact_name
                )
                Path(artifact_path).touch()

        return run_maven_side_effect

    @patch.object(
        MavenTestSeleniumCucumber,
        '_get_effective_pom_element',
        side_effect=['mock surefire element', None]
    )
    def test_success_target_host_url_default_reports_dir(
        self,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'target-host-url': target_base_url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            mock_run_maven_step.side_effect = self.__create_run_maven_side_effect(
                surefire_reports_dir=surefire_reports_dir
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
            cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
            expected_step_result = self.__expected_step_result_with_artifacts_and_evidence(
                parent_work_dir_path=parent_work_dir_path,
                surefire_reports_dir=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    f'-Dselenium.hub.url={selenium_hub_url}',
                    f'-Dtarget.base.url={target_base_url}',
                    f'-Dcucumber.plugin=' \
                        f'html:{cucumber_html_report_path},' \
                        f'json:{cucumber_json_report_path}',
                ]
            )

    @patch.object(
        MavenTestSeleniumCucumber,
        '_get_effective_pom_element',
        side_effect=['mock surefire element', None]
    )
    def test_success_single_deployed_host_url_default_reports_dir(
        self,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'deployed-host-urls': target_base_url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            mock_run_maven_step.side_effect = self.__create_run_maven_side_effect(
                surefire_reports_dir=surefire_reports_dir
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
            cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
            expected_step_result = self.__expected_step_result_with_artifacts_and_evidence(
                parent_work_dir_path=parent_work_dir_path,
                surefire_reports_dir=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    f'-Dselenium.hub.url={selenium_hub_url}',
                    f'-Dtarget.base.url={target_base_url}',
                    f'-Dcucumber.plugin=' \
                        f'html:{cucumber_html_report_path},' \
                        f'json:{cucumber_json_report_path}',
                ]
            )

    @patch.object(
        MavenTestSeleniumCucumber,
        '_get_effective_pom_element',
        side_effect=['mock surefire element', None]
    )
    def test_success_multiple_deployed_host_url_default_reports_dir(
        self,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            deployed_host_urls = [target_base_url, 'https://mock-app-ignored.ploigos.com']
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'deployed-host-urls': deployed_host_urls
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            mock_run_maven_step.side_effect = self.__create_run_maven_side_effect(
                surefire_reports_dir=surefire_reports_dir
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
            cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
            expected_step_result = self.__expected_step_result_with_artifacts_and_evidence(
                parent_work_dir_path=parent_work_dir_path,
                surefire_reports_dir=surefire_reports_dir
            )
            expected_step_result.message = \
                f"Given more then one deployed host URL ({deployed_host_urls})," \
                f" targeting first one ({target_base_url}) for user acceptance test (UAT)."

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    f'-Dselenium.hub.url={selenium_hub_url}',
                    f'-Dtarget.base.url={target_base_url}',
                    f'-Dcucumber.plugin=' \
                        f'html:{cucumber_html_report_path},' \
                        f'json:{cucumber_json_report_path}',
                ]
            )

    @patch.object(
        MavenTestSeleniumCucumber,
        '_get_effective_pom_element',
        side_effect=['mock surefire element', Mock(text='mock/fake/reports')]
    )
    def test_success_target_host_url_pom_specified_relative_reports_dir(
        self,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'target-host-url': target_base_url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'mock/fake/reports')
            mock_run_maven_step.side_effect = self.__create_run_maven_side_effect(
                surefire_reports_dir=surefire_reports_dir
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
            cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
            expected_step_result = self.__expected_step_result_with_artifacts_and_evidence(
                parent_work_dir_path=parent_work_dir_path,
                surefire_reports_dir=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    f'-Dselenium.hub.url={selenium_hub_url}',
                    f'-Dtarget.base.url={target_base_url}',
                    f'-Dcucumber.plugin=' \
                        f'html:{cucumber_html_report_path},' \
                        f'json:{cucumber_json_report_path}',
                ]
            )

    @patch.object(MavenTestSeleniumCucumber, '_get_effective_pom_element')
    def test_success_target_host_url_pom_specified_absolute_reports_dir(
        self,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'target-host-url': target_base_url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'mock-abs/fake/reports')
            mock_effective_pom_element.side_effect = [
                'mock surefire element',
                Mock(text=surefire_reports_dir)
            ]
            mock_run_maven_step.side_effect = self.__create_run_maven_side_effect(
                surefire_reports_dir=surefire_reports_dir
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
            cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
            expected_step_result = self.__expected_step_result_with_artifacts_and_evidence(
                parent_work_dir_path=parent_work_dir_path,
                surefire_reports_dir=surefire_reports_dir
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    f'-Dselenium.hub.url={selenium_hub_url}',
                    f'-Dtarget.base.url={target_base_url}',
                    f'-Dcucumber.plugin=' \
                        f'html:{cucumber_html_report_path},' \
                        f'json:{cucumber_json_report_path}',
                ]
            )

    @patch.object(MavenTestSeleniumCucumber, '_get_effective_pom_element', side_effect=[None, None])
    @patch.object(MavenTestSeleniumCucumber, '_get_effective_pom', return_value='mock-effective-pom.xml')
    def test_fail_no_surefire_plugin(
        self,
        mock_effective_pom,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'target-host-url': target_base_url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            mock_run_maven_step.side_effect = self.__create_run_maven_side_effect(
                surefire_reports_dir=surefire_reports_dir
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = self.__expected_step_result_base()
            expected_step_result.success = False
            expected_step_result.message = 'Unit test dependency "maven-surefire-plugin" ' \
                'missing from effective pom (mock-effective-pom.xml).'

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_run_maven_step.assert_not_called()

    @patch.object(
        MavenTestSeleniumCucumber,
        '_get_effective_pom_element',
        side_effect=['mock surefire element', None]
    )
    def test_fail_no_tests(
        self,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'target-host-url': target_base_url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
            cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
            expected_step_result = self.__expected_step_result_with_artifacts(
                parent_work_dir_path=parent_work_dir_path,
                surefire_reports_dir=surefire_reports_dir
            )
            expected_step_result.success = False
            expected_step_result.message = "No user acceptance tests defined" \
                f" using maven profile (['integration-test'])."

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    f'-Dselenium.hub.url={selenium_hub_url}',
                    f'-Dtarget.base.url={target_base_url}',
                    f'-Dcucumber.plugin=' \
                        f'html:{cucumber_html_report_path},' \
                        f'json:{cucumber_json_report_path}',
                ]
            )

    @patch.object(
        MavenTestSeleniumCucumber,
        '_get_effective_pom_element',
        side_effect=['mock surefire element', None]
    )
    def test_success_but_no_tests(
        self,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'target-host-url': target_base_url,
                'fail-on-no-tests': False
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
            cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
            expected_step_result = self.__expected_step_result_with_artifacts(
                parent_work_dir_path=parent_work_dir_path,
                surefire_reports_dir=surefire_reports_dir
            )
            expected_step_result.message = "No user acceptance tests defined" \
                " using maven profile (['integration-test'])," \
                " but 'fail-on-no-tests' is False."

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    f'-Dselenium.hub.url={selenium_hub_url}',
                    f'-Dtarget.base.url={target_base_url}',
                    f'-Dcucumber.plugin=' \
                        f'html:{cucumber_html_report_path},' \
                        f'json:{cucumber_json_report_path}',
                ]
            )

    @patch.object(
        MavenTestSeleniumCucumber,
        '_get_effective_pom_element',
        side_effect=['mock surefire element', None]
    )
    def test_could_not_find_expected_evidence(
        self,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'target-host-url': target_base_url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            mock_run_maven_step.side_effect = self.__create_run_maven_side_effect(
                surefire_reports_dir=surefire_reports_dir
            )
            mock_aggregate_xml_element_attribute_values.return_value = {}

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
            cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
            expected_step_result = self.__expected_step_result_with_artifacts(
                parent_work_dir_path=parent_work_dir_path,
                surefire_reports_dir=surefire_reports_dir
            )
            expected_step_result.success = False
            attribs = ["time", "tests", "errors", "skipped", "failures"]
            expected_step_result.message = "Error gathering evidence from "\
                f"surefire report, expected attribute(s) ({attribs}) "\
                f"not found in report ({surefire_reports_dir})"

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    f'-Dselenium.hub.url={selenium_hub_url}',
                    f'-Dtarget.base.url={target_base_url}',
                    f'-Dcucumber.plugin=' \
                        f'html:{cucumber_html_report_path},' \
                        f'json:{cucumber_json_report_path}',
                ]
            )

    @patch.object(
        MavenTestSeleniumCucumber,
        '_get_effective_pom_element',
        side_effect=['mock surefire element', None]
    )
    def test_fail_maven_error(
        self,
        mock_effective_pom_element,
        mock_aggregate_xml_element_attribute_values,
        mock_write_working_file,
        mock_run_maven_step
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file = os.path.join(test_dir.path, 'mock-pom.xml')
            selenium_hub_url = 'https://mock-selenium-hub.ploigos.com'
            target_base_url = 'https://mock-app.ploigos.com'
            step_config = {
                'pom-file': pom_file,
                'selenium-hub-url': selenium_hub_url,
                'target-host-url': target_base_url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # setup sideeffects
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            mock_run_maven_step.side_effect = StepRunnerException('mock maven error')

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
            cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')
            expected_step_result = self.__expected_step_result_with_artifacts(
                parent_work_dir_path=parent_work_dir_path,
                surefire_reports_dir=surefire_reports_dir
            )
            expected_step_result.success = False
            expected_step_result.message = "Error running 'maven test' to run user acceptance tests. " \
                "More details maybe found in 'maven-output', `surefire-reports`, " \
                "`cucumber-report-html`, and `cucumber-report-json` " \
                "report artifact: mock maven error"

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt',
                step_implementer_additional_arguments=[
                    f'-Dselenium.hub.url={selenium_hub_url}',
                    f'-Dtarget.base.url={target_base_url}',
                    f'-Dcucumber.plugin=' \
                        f'html:{cucumber_html_report_path},' \
                        f'json:{cucumber_json_report_path}',
                ]
            )

# class TestStepImplementerMavenTestSeleniumCucumberBase(MaveStepImplementerTestCase):
#     def create_step_implementer(
#             self,
#             step_config={},
#             parent_work_dir_path=''
#     ):
#         return self.create_given_step_implementer(
#             step_implementer=MavenTestSeleniumCucumber,
#             step_config=step_config,
#             step_name='uat',
#             implementer='MavenTestSeleniumCucumber',
#             parent_work_dir_path=parent_work_dir_path
#         )

# class TestStepImplementerDeployMavenTestSeleniumCucumber_validate_required_config_or_previous_step_result_artifact_keys(
#     TestStepImplementerMavenTestSeleniumCucumberBase
# ):
#     def test_MavenTestSeleniumCucumber_validate_required_config_or_previous_step_result_artifact_keys_success_target_host_url(self):
#         with TempDirectory() as temp_dir:
#             parent_work_dir_path = os.path.join(temp_dir.path, 'working')

#             pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
#             Path(pom_file_path).touch()
#             step_config = {
#                 'selenium-hub-url': 'https://selenium.ploigos.xyz',
#                 'pom-file': pom_file_path,
#                 'target-host-url': 'https://foo.test.ploigos.xyz'
#             }
#             step_implementer = self.create_step_implementer(
#                 step_config=step_config,
#                 parent_work_dir_path=parent_work_dir_path,
#             )

#             step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

#     def test_MavenTestSeleniumCucumber_validate_required_config_or_previous_step_result_artifact_keys_success_deployed_host_urls_1(self):
#         with TempDirectory() as temp_dir:
#             parent_work_dir_path = os.path.join(temp_dir.path, 'working')

#             pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
#             Path(pom_file_path).touch()
#             step_config = {
#                 'selenium-hub-url': 'https://selenium.ploigos.xyz',
#                 'pom-file': pom_file_path,
#                 'deployed-host-urls': ['https://foo.test.ploigos.xyz']
#             }
#             step_implementer = self.create_step_implementer(
#                 step_config=step_config,
#                 parent_work_dir_path=parent_work_dir_path,
#             )

#             step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

#     def test_MavenTestSeleniumCucumber_validate_required_config_or_previous_step_result_artifact_keys_success_deployed_host_urls_2(self):
#         with TempDirectory() as temp_dir:
#             parent_work_dir_path = os.path.join(temp_dir.path, 'working')

#             pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
#             Path(pom_file_path).touch()
#             step_config = {
#                 'selenium-hub-url': 'https://selenium.ploigos.xyz',
#                 'pom-file': pom_file_path,
#                 'deployed-host-urls': ['https://foo.test.ploigos.xyz', 'https://bar.test.ploigos.xyz']
#             }
#             step_implementer = self.create_step_implementer(
#                 step_config=step_config,
#                 parent_work_dir_path=parent_work_dir_path,
#             )

#             step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

#     def test_MavenTestSeleniumCucumber_validate_required_config_or_previous_step_result_artifact_keys_fail_no_target_urls(self):
#         with TempDirectory() as temp_dir:
#             parent_work_dir_path = os.path.join(temp_dir.path, 'working')

#             pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
#             Path(pom_file_path).touch()
#             step_config = {
#                 'selenium-hub-url': 'https://selenium.ploigos.xyz',
#                 'pom-file': pom_file_path
#             }
#             step_implementer = self.create_step_implementer(
#                 step_config=step_config,
#                 parent_work_dir_path=parent_work_dir_path,
#             )

#             with self.assertRaisesRegex(
#                 StepRunnerException,
#                 rf"Either 'target-host-url' or 'deployed-host-urls' needs to be supplied but"
#                 " neither were."
#             ):
#                 step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

# class TestStepImplementerMavenTestSeleniumCucumber_Other(TestStepImplementerMavenTestSeleniumCucumberBase):
#     def test_step_implementer_config_defaults(self):
#         actual_defaults = MavenTestSeleniumCucumber.step_implementer_config_defaults()
#         expected_defaults = {
#             'fail-on-no-tests': True,
#             'pom-file': 'pom.xml',
#             'tls-verify': True,
#             'uat-maven-profile': 'integration-test'
#         }
#         self.assertEqual(expected_defaults, actual_defaults)

#     def test__required_config_or_result_keys(self):
#         actual_required_keys = MavenTestSeleniumCucumber._required_config_or_result_keys()
#         expected_required_keys = [
#             'fail-on-no-tests',
#             'pom-file',
#             'selenium-hub-url',
#             'uat-maven-profile'
#         ]
#         self.assertEqual(expected_required_keys, actual_required_keys)

#     def __run__run_step_test(
#         self,
#         test_dir,
#         mvn_mock,
#         write_effective_pom_mock,
#         generate_maven_settings_mock,
#         pom_content,
#         group_id,
#         artifact_id,
#         surefire_reports_dir,
#         selenium_hub_url,
#         target_host_url=None,
#         deployed_host_urls=None,
#         write_mock_test_results=True,
#         assert_mvn_called=True,
#         assert_report_artifact=True,
#         assert_evidence=True,
#         expected_result_success=True,
#         expected_result_message='',
#         fail_on_no_tests=None,
#         uat_maven_profile=None,
#         pom_file_name='pom.xml',
#         raise_error_on_tests=False,
#         set_tls_verify_false=False,
#         aggregate_xml_element_attribute_values_mock=False,
#         aggregate_xml_element_attribute_values_mock_fail=False
#     ):
#         parent_work_dir_path = os.path.join(test_dir.path, 'working')

#         cucumber_html_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.html')
#         cucumber_json_report_path = os.path.join(parent_work_dir_path, 'uat', 'cucumber.json')

#         test_dir.write(pom_file_name, pom_content)

#         pom_file_path = os.path.join(test_dir.path, pom_file_name)
#         step_config = {
#             'pom-file': pom_file_path,
#             'selenium-hub-url': selenium_hub_url,
#             'tls-verify': True
#         }

#         if set_tls_verify_false:
#             step_config['tls-verify'] = False

#         target_base_url = None
#         if deployed_host_urls:
#             step_config['deployed-host-urls'] = deployed_host_urls
#             if isinstance(deployed_host_urls, list):
#                 target_base_url = deployed_host_urls[0]
#             else:
#                target_base_url = deployed_host_urls
#         if target_host_url:
#             step_config['target-host-url'] = target_host_url
#             target_base_url = target_host_url

#         if fail_on_no_tests is not None:
#             step_config['fail-on-no-tests'] = fail_on_no_tests
#         if uat_maven_profile is not None:
#             step_config['uat-maven-profile'] = uat_maven_profile
#         else:
#             uat_maven_profile = 'integration-test'
#         step_implementer = self.create_step_implementer(
#             step_config=step_config,
#             parent_work_dir_path=parent_work_dir_path,
#         )

#         # mock generating settings
#         settings_file_path = "/does/not/matter/settings.xml"
#         def generate_maven_settings_side_effect():
#             return settings_file_path
#         generate_maven_settings_mock.side_effect = generate_maven_settings_side_effect

#         # mock effective pom
#         def write_effective_pom_mock_side_effect(pom_file_path, output_path):
#             create_parent_dir(pom_file_path)
#             copyfile(pom_file_path, output_path)
#         write_effective_pom_mock.side_effect = write_effective_pom_mock_side_effect

#         # mock test results
#         if write_mock_test_results:
#             mvn_mock.side_effect = MaveStepImplementerTestCase.create_mvn_side_effect(
#                 pom_file=pom_file_path,
#                 artifact_parent_dir=surefire_reports_dir,
#                 artifact_names=[
#                     f'{group_id}.{artifact_id}.CucumberTest.txt',
#                     f'TEST-{group_id}.{artifact_id}.CucumberTest.xml'
#                 ],
#                 raise_error_on_tests=raise_error_on_tests
#             )

#         # mock evidence
#         if aggregate_xml_element_attribute_values_mock and not aggregate_xml_element_attribute_values_mock_fail:
#             aggregate_xml_element_attribute_values_mock.return_value = {
#                 'time': '42',
#                 'tests': '42',
#                 'errors': '0',
#                 'skipped': '0',
#                 'failures': '0'
#                 }
#         elif aggregate_xml_element_attribute_values_mock_fail:
#             aggregate_xml_element_attribute_values_mock.return_value = {
#                 'time': '42'
#                 }

#         result = step_implementer._run_step()
#         if assert_mvn_called:
#             if not set_tls_verify_false:
#                 mvn_mock.assert_called_once_with(
#                     'clean',
#                     'test',
#                     f'-P{uat_maven_profile}',
#                     f'-Dselenium.hub.url={selenium_hub_url}',
#                     f'-Dtarget.base.url={target_base_url}',
#                     f'-Dcucumber.plugin=' \
#                         f'html:{cucumber_html_report_path},' \
#                         f'json:{cucumber_json_report_path}',
#                     '-f', pom_file_path,
#                     '-s', settings_file_path,
#                     _out=Any(IOBase),
#                     _err=Any(IOBase)
#                 )
#             else:
#                 mvn_mock.assert_called_once_with(
#                     'clean',
#                     'test',
#                     f'-P{uat_maven_profile}',
#                     f'-Dselenium.hub.url={selenium_hub_url}',
#                     f'-Dtarget.base.url={target_base_url}',
#                     f'-Dcucumber.plugin=' \
#                         f'html:{cucumber_html_report_path},' \
#                         f'json:{cucumber_json_report_path}',
#                     '-f', pom_file_path,
#                     '-s', settings_file_path,
#                     '-Dmaven.wagon.http.ssl.insecure=true',
#                     '-Dmaven.wagon.http.ssl.allowall=true',
#                     '-Dmaven.wagon.http.ssl.ignore.validity.dates=true',
#                     _out=Any(IOBase),
#                     _err=Any(IOBase)
#                 )

#         expected_step_result = StepResult(
#             step_name='uat',
#             sub_step_name='MavenTestSeleniumCucumber',
#             sub_step_implementer_name='MavenTestSeleniumCucumber'
#         )
#         expected_step_result.success = expected_result_success
#         expected_step_result.message = expected_result_message

#         if assert_report_artifact:
#             mvn_test_output_file_path = os.path.join(
#                 step_implementer.work_dir_path,
#                 'mvn_test_output.txt'
#             )
#             expected_step_result.add_artifact(
#                 description=f"Standard out and standard error by 'mvn -P{uat_maven_profile} test'.",
#                 name='maven-output',
#                 value=mvn_test_output_file_path
#             )
#             expected_step_result.add_artifact(
#                 description=f"Surefire reports generated by 'mvn -P{uat_maven_profile} test'.",
#                 name='surefire-reports',
#                 value=surefire_reports_dir
#             )
#             expected_step_result.add_artifact(
#                 description=f"Cucumber (HTML) report generated by 'mvn -P{uat_maven_profile} test'.",
#                 name='cucumber-report-html',
#                 value=cucumber_html_report_path
#             )
#             expected_step_result.add_artifact(
#                 description=f"Cucumber (JSON) report generated by 'mvn -P{uat_maven_profile} test'.",
#                 name='cucumber-report-json',
#                 value=cucumber_json_report_path
#             )

#         if assert_evidence and not aggregate_xml_element_attribute_values_mock_fail:
#             expected_step_result.add_evidence(
#                 name='uat-evidence-time',
#                 description='Surefire report value for time',
#                 value='42'
#             )
#             expected_step_result.add_evidence(
#                 name='uat-evidence-tests',
#                 description='Surefire report value for tests',
#                 value='42'
#             )
#             expected_step_result.add_evidence(
#                 name='uat-evidence-errors',
#                 description='Surefire report value for errors',
#                 value='0'
#             )
#             expected_step_result.add_evidence(
#                 name='uat-evidence-skipped',
#                 description='Surefire report value for skipped',
#                 value='0'
#             )
#             expected_step_result.add_evidence(
#                 name='uat-evidence-failures',
#                 description='Surefire report value for failures',
#                 value='0'
#             )
#         elif assert_evidence and aggregate_xml_element_attribute_values_mock_fail:
#             expected_step_result.add_evidence(
#                 name='uat-evidence-time',
#                 description='Surefire report value for time',
#                 value='42'
#             )
#         print(result)
#         self.assertEqual(expected_step_result, result)


#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_success_defaults(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_tls_verify_false(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 set_tls_verify_false=True
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_success__deployed_host_urls_str(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             deployed_host_urls = 'https://foo.ploigos.xyz'
#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 deployed_host_urls=deployed_host_urls
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_success__deployed_host_urls_array_1(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             deployed_host_urls = ['https://foo.ploigos.xyz']
#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 deployed_host_urls=deployed_host_urls
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_success__deployed_host_urls_array_2(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock,
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             deployed_host_urls = ['https://foo.ploigos.xyz', 'https://foo.ploigos.xyz']
#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 deployed_host_urls=deployed_host_urls,
#                 expected_result_message=\
#                     f"Given more then one deployed host URL ({deployed_host_urls})," \
#                     f" targeting first one (https://foo.ploigos.xyz) for user acceptance test (UAT)."
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_success_provided_profile_override(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 uat_maven_profile='custom-uat-profile'
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_success_provided_pom_file_override(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 pom_file_name='custom-pom.xml'
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_success_provided_fail_on_no_tests_false_with_tests(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 fail_on_no_tests=False,
#                 write_mock_test_results=True,
#                 expected_result_success=True
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_success_provided_fail_on_no_tests_false_with_no_tests(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 assert_evidence=False,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 fail_on_no_tests=False,
#                 write_mock_test_results=False,
#                 expected_result_success=True,
#                 expected_result_message="No user acceptance tests defined" \
#                     " using maven profile (integration-test)," \
#                     " but 'fail-on-no-tests' is False."
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_fail_provided_fail_on_no_tests_true_with_no_tests(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 assert_evidence=False,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 fail_on_no_tests=True,
#                 write_mock_test_results=False,
#                 expected_result_success=False,
#                 expected_result_message="No user acceptance tests defined" \
#                     " using maven profile (integration-test)."
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_fail_no_surefire_plugin(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             effective_pom_path = os.path.join(
#                 test_dir.path,
#                 'working',
#                 'uat',
#                 'effective-pom.xml'
#             )
#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 assert_evidence=False,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 expected_result_success=False,
#                 expected_result_message='Unit test dependency "maven-surefire-plugin" ' \
#                     f'missing from effective pom ({effective_pom_path}).',
#                 assert_mvn_called=False,
#                 assert_report_artifact=False
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_success_pom_specified_reports_dir(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#                 <configuration>
#                     <reportsDirectory>{surefire_reports_dir}</reportsDirectory>
#                 </configuration>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version,
#                     surefire_reports_dir=surefire_reports_dir
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 assert_evidence=True,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_fail_mvn_test_failure(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=None,
#                 assert_evidence=False,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 raise_error_on_tests=True,
#                 expected_result_success=False,
#                 expected_result_message="User acceptance test failures. See 'maven-output'" \
#                     ", 'surefire-reports', 'cucumber-report-html', and 'cucumber-report-json'" \
#                     " report artifacts for details."
#             )

#     @patch('ploigos_step_runner.step_implementers.uat.maven_test_selenium_cucumber.aggregate_xml_element_attribute_values')
#     @patch.object(MavenTestSeleniumCucumber, '_generate_maven_settings')
#     @patch('sh.mvn', create=True)
#     @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
#     def test__run_step_failure_missing_evidence_attribute(
#         self,
#         write_effective_pom_mock,
#         mvn_mock,
#         generate_maven_settings_mock,
#         aggregate_xml_element_attribute_values_mock
#     ):
#         with TempDirectory() as test_dir:
#             group_id = 'com.mycompany.app'
#             artifact_id = 'my-app'
#             version = '1.0'
#             surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
#             pom_content = bytes(
# '''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
# xmlns="http://maven.apache.org/POM/4.0.0"
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#     <modelVersion>4.0.0</modelVersion>
#     <groupId>{group_id}</groupId>
#     <artifactId>{artifact_id}</artifactId>
#     <version>{version}</version>
#     <properties>
#         <maven.compiler.source>1.8</maven.compiler.source>
#         <maven.compiler.target>1.8</maven.compiler.target>
#     </properties>
#     <build>
#         <plugins>
#             <plugin>
#                 <artifactId>maven-surefire-plugin</artifactId>
#                 <version>${{surefire-plugin.version}}</version>
#             </plugin>
#         </plugins>
#     </build>
# </project>'''.format(
#                     group_id=group_id,
#                     artifact_id=artifact_id,
#                     version=version
#                 ), 'utf-8'
#             )

#             self.__run__run_step_test(
#                 test_dir=test_dir,
#                 mvn_mock=mvn_mock,
#                 selenium_hub_url='https://test.xyz:4444',
#                 write_effective_pom_mock=write_effective_pom_mock,
#                 generate_maven_settings_mock=generate_maven_settings_mock,
#                 aggregate_xml_element_attribute_values_mock=aggregate_xml_element_attribute_values_mock,
#                 aggregate_xml_element_attribute_values_mock_fail=True,
#                 assert_evidence=True,
#                 pom_content=pom_content,
#                 group_id=group_id,
#                 artifact_id=artifact_id,
#                 surefire_reports_dir=surefire_reports_dir,
#                 expected_result_success=False,
#                 expected_result_message="Error gathering evidence from "\
#                             "surefire report, expected attribute tests "\
#                             "not found in report " + surefire_reports_dir)
