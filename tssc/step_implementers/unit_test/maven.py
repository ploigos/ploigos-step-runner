"""Step Implementer for the unit-test step for Maven generating JUnit reports.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key  | Required? | Default     | Description
|--------------------|-----------|-------------|-----------
| `fail-on-no-tests` | True      | True        | Value to specify whether unit-test
                                                 step can succeed when no tests are defined
| `pom-file`         | True      | `'pom.xml'` | pom used to run tests and check
                                                 for existence of custom reportsDirectory

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

None.

Results
-------

Results output by this step.

| Result Key          | Description
|---------------------|------------
| `pom-path`          | Absolute path to the pom used to run tests
| `surefile-reports`  |

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
    'pom-file': 'pom.xml'
}

REQUIRED_CONFIG_KEYS = [
    'fail-on-no-tests',
    'pom-file'
]


class Maven(StepImplementer):
    """
    StepImplementer for the unit-test step for Maven generating JUnit reports.
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
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        step_result
            Object with results of running this step.
        """
        step_result = StepResult.from_step_implementer(self)

        pom_file = self.get_config_value('pom-file')
        fail_on_no_tests = self.get_config_value('fail-on-no-tests')

        if not os.path.exists(pom_file):
            step_result.success = False
            step_result.message = 'Given pom file does not exist:  ' + pom_file
            return step_result

        surefire_path = 'mvn:build/mvn:plugins/mvn:plugin/[mvn:artifactId="maven-surefire-plugin"]'
        maven_surefire_plugin = get_xml_element_by_path(
            pom_file,
            surefire_path,
            default_namespace='mvn'
        )
        if maven_surefire_plugin is None:
            step_result.success = False
            step_result.message = 'Unit test dependency "maven-surefire-plugin" missing from POM'
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

        settings_file = self._generate_maven_settings()

        try:
            sh.mvn(  # pylint: disable=no-member
                'clean',
                'test',
                '-f', pom_file,
                '-s', settings_file,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise RuntimeError(f'Error invoking mvn: {error}') from error

        test_results_output_path = test_results_dir

        if not os.path.isdir(test_results_dir) or \
            len(os.listdir(test_results_dir)) == 0:
            if fail_on_no_tests is not True:
                step_result.message = 'unit test step run successfully, but no tests were found'
            else:# pragma: no cover
                # Added 'no cover' to bypass missing unit-test step coverage error
                # that is covered by the following unit test:
                #   test_unit_test_run_attempt_fails_fail_on_no_tests_flag_true
                step_result.message = 'Error: No unit tests defined'
                step_result.success = False
                return step_result
        else:
            step_result.add_artifact(
                description='maven unit test results generated using junit',
                name='surefire-reports',
                value=f'file://{test_results_output_path}',
                value_type='file'
            )

        step_result.add_artifact(
            name='pom-path',
            value=f'file://{pom_file}',
            value_type='file'
        )

        return step_result
