"""Step Implementer for the 'validate-environment-config' step for configlint.

The Configlint step executes the config-lint against yml files for user-defined
rules.   The inputs to this step include:

  - Rules defined by the user in a specified file:

    * Reference:  https://stelligent.github.io/config-lint/#/

  - File path of yml files to lint

    * Specify as a runtime argument, or
    * Use results from previous step such as ConfilintFromArgocd

Step Configuration
------------------

Step configuration key(s) for this step:

| Key               | Required | Default                   | Description
|-------------------|----------|---------------------------|-----------
| `rules`           | False    | ./config_lint.rules       | File containing user-defined rules

Expected Previous Step Results
------------------------------

Results expected from previous steps:

| Step Name           |  Key                | Description
|---------------------|---------------------|------------
| `validate`          | `options.yml_path`  | Provides the path to the yml files
| `environment-`      |                     | to be evaluated
| `configuration`     |                     |

Results
-------

Results output by this step:

| Key                              | Description
|----------------------------------|------------
| `result`                         | A dictionary describing the output \
                                     of this step
| `report-artifacts`               | An array of dictionaries describing \
                                     artifacts generated by this step
| `options`                        | A dictionary of non-standard options \
                                     used by this step implementer

Elements in `result` dictionary:

| Key          | Description
|--------------|------------
| `success`    | Boolean value describing success/failure of this step
| `message`    | Human readable message describing results of this step

Elements in `report-artifacts` dictionary:

|  Key         | Description
|--------------|------------
| `name`       | Human readable name for report artifact generated by this step
| `path`       | Absolute path (including transport protocol) to the step report artifact


Examples
--------

**Example: Step Configuration (minimal)**

    validate-environment-configuration:
    - implementer: ConfiglintFromArgocd
    - implementer: Configlint
      config:
        rules: 'config_lint.rules'

.. Note:: The configuration example above uses the ConfiglintFromArgocd step to \
provide the yml_path option.

**Example: Generated Config Lint Call (runtime)**

    config-lint -verbose
        -rules rules.yml /home/user/tssc-working/deploy/file.yml

**Example: Existing Rules File (minimal)**

    version: 1
    description: Rules for Kubernetes spec files
    type: Kubernetes
    files:
      - "*.yml"
    rules:
    - id: TSSC_EXAMPLE
      severity: FAILURE
      message: Deployment must have istio
      resource: Deployment
      assertions:
        - key: spec.template.metadata.annotations
          op: contains
          value: '"sidecar.istio.io/inject": false'

Example: Results

    'tssc-results': {
        'validate-environment-configuration': {
            'result': {
                'success': True,
                'message': 'config-lint step completed'
            }
            'options': {
                'yml_path': '/home/user/tssc-working/file.yml'
            }
            'report-artifacts': [
                {
                    'name' : 'configlint-result-set',
                    'path': 'file://f/validate/configlint_results_file.txt'
                }
            ]

    }

.. Note:: The configuration example above used the ConfiglintFromArgocd step to \
provide the yml_path option.

"""

import os
import sh
from tssc import StepImplementer

DEFAULT_CONFIG = {
    'rules': './config-lint.rules'
}

REQUIRED_CONFIG_KEYS = {
}

AUTHENTICATION_CONFIG = {
}

class Configlint(StepImplementer):
    """
    StepImplementer for the tag-source step for Config_lint.
    """

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

    def _run_step(self):
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

        # yml_path is required
        yml_path = self.get_config_value('yml_path')
        if yml_path is None:
            current_step_results = self.current_step_results()
            if 'options' in current_step_results:
                if 'yml_path' in current_step_results['options']:
                    yml_path = current_step_results['options'].get('yml_path')

        if yml_path is None:
            raise ValueError('yml_path not specified in runtime args or in options')

        if not os.path.exists(yml_path):
            raise ValueError(f'Specified file in yml_path not found: {yml_path}')

        # Required: rules and exists
        rules_file = self.get_config_value('rules')
        if not os.path.exists(rules_file):
            raise ValueError(f'Rules file specified in tssc config not found: {rules_file}')

        try:

            configlint_results_file = self.write_working_file(
                'configlint_results_file.txt',
                b''
            )
            # Hint:  Call config-lint with sh.config_lint
            sh.config_lint(  # pylint: disable=no-member
                "-verbose",
                "-debug",
                "-rules",
                rules_file,
                yml_path,
                _out=configlint_results_file,
                _err_to_out=True
            )

            sh.cat(configlint_results_file) # pylint: disable=no-member

        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking config-lint: {all}'.format(all=error)) from error

        results = {
            'result': {
                'success': True,
                'message': 'configlint step completed',
            },
            'report-artifacts': [
                {
                    'name' : 'configlint-result-set',
                    'path': f'file://{configlint_results_file}'
                }
            ]
        }
        return results
