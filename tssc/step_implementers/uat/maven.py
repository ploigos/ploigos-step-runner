"""Step Implementer for the UAT step for Maven generating Cucumber reports.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key  | Required? | Default            | Description
|--------------------|-----------|--------------------|------------
| `fail-on-no-tests` | True      | True               | Value to specify whether unit-test \
                                                        step can succeed when no tests are defined
| `pom-file`         | True      | `pom.xml`          | pom used to run tests and check \
                                                        for existence of custom reportsDirectory
| `selenium-hub-url` | True      |                    | URL where the Selenium Hub is running
| `target-base-url`  | True      | result from deploy | URL where the UAT application is running
| `report-dir`       | False     | `cucumber`         | Directory to put cucumber tests

Expected Previous Step Results
------------------------------
Results expected from previous steps that this step may require.

| Step Name | Result Key            | Description
|-----------|-----------------------|------------
| `deploy`  | `deploy-endpoint-url` | The git tag to apply to the config repo

Results
-------
Results output by this step.

| Result Key         | Description
|--------------------|------------
| `uat-pom-path`     |
| `uat-results`      |
| `fail-on-no-tests` |

"""
import sys
import os
import sh

from tssc import StepImplementer
from tssc.utils.xml import get_xml_element_by_path

from tssc.utils.maven import generate_maven_settings
from tssc.config import ConfigValue
from tssc.step_result import StepResult

DEFAULT_CONFIG = {
    'fail-on-no-tests': True,
    'pom-file': 'pom.xml',
    'target-base-url': None,
    'report-dir': 'cucumber'
}

REQUIRED_CONFIG_KEYS = [
    'fail-on-no-tests',
    'pom-file',
    'selenium-hub-url',
    'report-dir'
]


class Maven(StepImplementer):
    """
    StepImplementer for the unit-test step for Maven generating Cucumber reports.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

        Returns
        -------
        dict
            Default values to use for step configuration values.

        Notes
        -----
        These are the lowest precedence configuration values.
        """
        return DEFAULT_CONFIG

    @staticmethod
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.

        See Also
        --------
        _validate_runtime_step_config
        """
        return REQUIRED_CONFIG_KEYS

    def _get_target_base_url(self):
        """Gets the target-base-url.
        Gets the target-base-url first from the configs. If not found
        attempt to pull it from a previous deploy step.
        If still unable to find, then throw ValueError.
        """
        target_base_url = self.get_config_value('target-base-url')
        if target_base_url is None:
            target_base_url = self.get_result_value('deploy-endpoint-url')

        return target_base_url

    def _generate_maven_settings(self):
        # ----- build settings.xml
        maven_servers = ConfigValue.convert_leaves_to_values(
            self.get_config_value('maven-servers')
        )
        maven_repositories = ConfigValue.convert_leaves_to_values(
            self.get_config_value('maven-repositories')
        )
        maven_mirrors = ConfigValue.convert_leaves_to_values(
            self.get_config_value('maven-mirrors')
        )
        return generate_maven_settings(self.work_dir_path,
                                       maven_servers,
                                       maven_repositories,
                                       maven_mirrors)

    def _run_step(self):
        """
        Runs the TSSC step implemented by this StepImplementer.
        Returns
        -------
        dict
            Results of running this step.
        """
        step_result = StepResult.from_step_implementer(self)

        settings_file = self._generate_maven_settings()
        pom_file = self.get_config_value('pom-file')
        fail_on_no_tests = self.get_config_value('fail-on-no-tests')
        selenium_hub_url = self.get_config_value('selenium-hub-url')
        report_dir = self.get_config_value('report-dir')
        target_base_url = self._get_target_base_url()
        if target_base_url is None:
            step_result.success = False
            step_result.message = "Key target-base-url not found"
            return step_result

        if not os.path.exists(pom_file):
            step_result.success = False
            step_result.message = f'Given pom file does not exist: {pom_file}'
            return step_result

        surefire_path = 'mvn:build/mvn:plugins/mvn:plugin/[mvn:artifactId="maven-surefire-plugin"]'
        maven_surefire_plugin = get_xml_element_by_path(
            pom_file,
            surefire_path,
            default_namespace='mvn')

        if maven_surefire_plugin is None:
            step_result.success = False
            step_result.message = 'Uat dependency "maven-surefire-plugin" missing from POM.'
            return step_result

        reports_dir = get_xml_element_by_path(
            pom_file,
            f'{surefire_path}/mvn:configuration/mvn:reportsDirectory',
            default_namespace='mvn'
        )
        if reports_dir is not None:
            test_results_dir = reports_dir.text
        else:
            test_results_dir = os.path.join(
                os.path.dirname(os.path.abspath(pom_file)),
                'target/surefire-reports')

        try:
            sh.mvn(  # pylint: disable=no-member
                'clean',
                '-Pintegration-test',
                f'-Dselenium.hub.url={selenium_hub_url}',
                f'-Dtarget.base.url={target_base_url}',
                f'-Dcucumber.plugin=html:target/{report_dir}/cucumber.html,' \
                f'json:target/{report_dir}/cucumber.json',
                'test',
                '-f', pom_file,
                '-s', settings_file,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise RuntimeError(f'Error invoking mvn: {error}') from error

        if not os.path.isdir(test_results_dir) or len(os.listdir(test_results_dir)) == 0:
            if fail_on_no_tests is not True:
                step_result.message = 'Uat step run successfully, but no tests were found'
                step_result.add_artifact(
                    name='fail-on-no-tests',
                    value=f'file://{os.path.dirname(os.path.abspath(pom_file))}/target/{report_dir}'
                )
            else:  # pragma: no cover
                # Added 'no cover' to bypass missing uat step coverage error
                # that is covered by the following test:
                #   test_uat_run_attempt_fails_fail_on_no_tests_flag_true
                step_result.success = False
                step_result.message = 'Error: No uat defined'
        else:
            step_result.add_artifact(
                name='uat-results',
                value=f'file://{os.path.dirname(os.path.abspath(pom_file))}/target/{report_dir}'
            )

        step_result.add_artifact(
            name='uat-pom-path',
            value=f'file://{pom_file}'
        )
        return step_result
