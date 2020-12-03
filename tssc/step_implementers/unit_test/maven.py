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
import os
import sys

import sh
from tssc import StepImplementer, StepResult
from tssc.step_implementers.shared.maven_generic import MavenGeneric
from tssc.utils import create_sh_redirect_to_multiple_streams_fn_callback

DEFAULT_CONFIG = {
    'fail-on-no-tests': True,
    'pom-file': 'pom.xml'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'fail-on-no-tests',
    'pom-file'
]


class Maven(MavenGeneric):
    """StepImplementer for the unit-test step for Maven generating JUnit reports.
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
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        step_result
            Object with results of running this step.
        """
        step_result = StepResult.from_step_implementer(self)

        pom_file = self.get_value('pom-file')
        fail_on_no_tests = self.get_value('fail-on-no-tests')

        # ensure surefire plugin enabled
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
            test_results_dir = reports_dir.text
        else:
            test_results_dir = os.path.join(
                os.path.dirname(os.path.abspath(pom_file)),
                MavenGeneric.DEFAULT_SUREFIRE_PLUGIN_REPORTS_DIR
            )

        settings_file = self._generate_maven_settings()
        mvn_output_file_path = self.write_working_file('mvn_test_output.txt')
        try:
            with open(mvn_output_file_path, 'w') as mvn_output_file:
                out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stdout,
                    mvn_output_file
                ])
                err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stderr,
                    mvn_output_file
                ])

                sh.mvn( # pylint: disable=no-member
                    'clean',
                    'test',
                    '-f', pom_file,
                    '-s', settings_file,
                    _out=out_callback,
                    _err=err_callback
                )

            if not os.path.isdir(test_results_dir) or len(os.listdir(test_results_dir)) == 0:
                if fail_on_no_tests:
                    step_result.message = 'No unit tests defined.'
                    step_result.success = False
                else:
                    step_result.message = "No unit tests defined, but 'fail-on-no-tests' is False."
        except sh.ErrorReturnCode as error:
            step_result.message = "Unit test failures. See 'maven-output'" \
                f" and 'surefire-reports' report artifacts for details: {error}"
            step_result.success = False
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from 'mvn test'.",
                name='maven-output',
                value=mvn_output_file_path
            )
            step_result.add_artifact(
                description="Surefire reports generated from 'mvn test'.",
                name='surefire-reports',
                value=test_results_dir
            )

        return step_result
