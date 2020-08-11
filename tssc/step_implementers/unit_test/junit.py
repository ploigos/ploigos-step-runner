"""Step Implementer for the unit-test step for JUnit.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default     | Description
|-------------------|-----------|-------------|-----------
| `pom-file`        | True      | `'pom.xml'` | pom used to check for reportsDirectory definition

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

None.

Results
-------

Results output by this step.

| Result Key  | Description
|-------------|------------
| `junit`     | A dictionary of JUnit unit test result dictionaries


**junit**
Keys in the `junit` dictionary element in the `unit-test` dictionary of the step results.

| `junit` Key     | Description
|-----------------|------------
| `pom-path`      | Absolute path to the pom used to run tests
| `test-results`  | Absolute path to the unit test results
"""
import sys
import os
import sh

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

from xml.etree import ElementTree

DEFAULT_CONFIG = {
    'pom-file': 'pom.xml'
}

REQUIRED_CONFIG_KEYS = [
    'pom-file'
]

class JUnit(StepImplementer):
    """
    StepImplementer for the unit-test step for JUnit.
    """

    @staticmethod
    def step_name():
        """
        Getter for the TSSC Step name implemented by this step.

        Returns
        -------
        str
            TSSC step name implemented by this step.
        """
        return DefaultSteps.UNIT_TEST

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

        Notes
        -----
        These are the lowest precedence configuration values.

        Returns
        -------
        dict
            Default values to use for step configuration values.
        """
        return DEFAULT_CONFIG

    @staticmethod
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.

        See Also
        --------
        _validate_runtime_step_config

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.
        """
        return REQUIRED_CONFIG_KEYS

    def _run_step(self, runtime_step_config):
        """
        Runs the TSSC step implemented by this StepImplementer.

        Parameters
        ----------
        runtime_step_config : dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.

        Returns
        -------
        dict
            Results of running this step.
        """
        pom_file = runtime_step_config['pom-file']

        if not os.path.exists(pom_file):
            raise ValueError('Given pom file does not exist: ' + pom_file)

        reports_dir = self.find_reports_dir(pom_file)
        if reports_dir is not None:
            default_test_results_dir = reports_dir
        else:
            default_test_results_dir = os.path.join(
                os.path.dirname(os.path.abspath(pom_file)),
                'target/surefire-reports')

        # TODO: Make method for identification/creation of this dir to be shared among steps
        test_results_output_path = "tssc-results/unit-test/junit"

        try:
            sh.mvn(  # pylint: disable=no-member,
                'clean',
                'test',
                '-f', pom_file,
                _out=sys.stdout
            )
        except sh.ErrorReturnCode as error:
            raise RuntimeError("Error invoking mvn: {error}".format(error=error))

        os.system("mkdir -p " + test_results_output_path)
        os.system("cp -r " + default_test_results_dir + "/. " + test_results_output_path)

        # Consider adding specific results: Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
        results = {
            'junit': {
                'pom-path': pom_file,
                'test-results': test_results_output_path
            }
        }
        return results
    
    @staticmethod
    def find_reports_dir(pom_file):
        """ Return the report directory specified in the pom """
        # TODO: Figure out the pom namespace to make this work
        ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        tree = ElementTree.parse(pom_file)
        root = tree.getroot()

        plugins = root.find('maven:build/maven:plugins', ns)
        for plugin in plugins.findall('maven:plugin', ns):
            config = plugin.find('maven:configuration', ns)
            if config is not None:
                reports_dir = config.find('maven:reportsDirectory', ns)
                if reports_dir is not None:
                    return reports_dir.text
        return None

# register step implementer
TSSCFactory.register_step_implementer(JUnit)
