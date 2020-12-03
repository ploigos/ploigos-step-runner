"""Step Implementer for the 'validate-environment-config' step for configlint.
The Configlint step executes the config-lint against yml files for user-defined
rules.   The inputs to this step include:

  - Rules defined by the user in a specified file:
    * Reference:  https://stelligent.github.io/config-lint/#/
  - File path of yml files to lint
    * Specify as a runtime argument, OR
    * Use results from previous step such as ConfilintFromArgocd

Step Configuration
------------------
Step configuration expected as input to this step.  Could come from either
configuration file or from runtime configuration.

| Configuration Key       | Required | Default               | Description
|-------------------------|----------|-----------------------|-----------------------------------
| `rules`                 | False    | ./config_lint.rules   | File containing user-defined rules
| `configlint-yml-file`   | False    | None                  | File to be linted

Expected Previous Step Results
------------------------------
Results expected from previous steps that this step requires.

| Step Name     | Key                     | Required | Description
|---------------|-------------------------|----------|------------
| validate-     | `configlint-yml-file`   | False    | File to be linted
| environment-  |                         |          |
| configuration |                         |          |

Results
-------
Results output by this step.

| Result Key              | Description
|-------------------------|------------
| `configlint-yml-file`   | File that was linted
| `configlint-result-set` | Result of configlint in a text file


Examples
--------
**Example: Step Configuration (minimal)**

    validate-environment-configuration:
    - implementer: ConfiglintFromArgocd
    - implementer: Configlint
      config:
        rules: 'config_lint.rules'

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

.. Note:: The configuration examples above uses the ConfiglintFromArgocd step to \
provide the configlint-yml-path.
"""

import os
import sys
from urllib.parse import urlparse

import sh
from tssc.utils.io import create_sh_redirect_to_multiple_streams_fn_callback
from tssc import StepImplementer
from tssc.step_result import StepResult

DEFAULT_CONFIG = {
    'rules': './config-lint.rules'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'configlint-yml-path'
]


class Configlint(StepImplementer):
    """
    StepImplementer for the validate-environment-configuration sub-step ConfiglintFromArgocd
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
        step_result = StepResult.from_step_implementer(self)

        # configlint-yml-path is required
        configlint_yml_path = self.get_value('configlint-yml-path')

        # configlint_yml_path expected format:  file:///folder/file.yml
        yml_path = urlparse(configlint_yml_path).path
        if not os.path.exists(yml_path):
            step_result.success = False
            step_result.message = f'File specified in configlint-yml-path not found: {yml_path}'
            return step_result

        # Required: rules and exists
        rules_file = self.get_value('rules')
        rules_file = urlparse(rules_file).path
        if not os.path.exists(rules_file):
            step_result.success = False
            step_result.message = f'File specified in rules not found: {rules_file}'
            return step_result

        configlint_results_file_path = self.write_working_file('configlint_results_file.txt')
        try:
            # run config-lint writing stdout and stderr to the standard streams
            # as well as to a results file.
            with open(configlint_results_file_path, 'w') as configlint_results_file:
                out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stdout,
                    configlint_results_file
                ])
                err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stderr,
                    configlint_results_file
                ])

                sh.config_lint(  # pylint: disable=no-member
                    "-verbose",
                    "-debug",
                    "-rules",
                    rules_file,
                    yml_path,
                    _encoding='UTF-8',
                    _out=out_callback,
                    _err=err_callback,
                    _tee='err'
                )
        except sh.ErrorReturnCode_255 as error:  # pylint: disable=no-member
            # NOTE: expected failure condition,
            #       aka, the config lint run, but found an issue
            step_result.success = False
            step_result.message = 'Failed config-lint scan.'
        except sh.ErrorReturnCode as error:
            # NOTE: un-expected failure condition
            #       aka, the config lint failed to run for some reason
            raise RuntimeError(f'Unexpected Error invoking config-lint: {error}') from error

        step_result.add_artifact(
            name='configlint-result-set',
            value=configlint_results_file_path
        )
        step_result.add_artifact(
            name='configlint-yml-path',
            value=yml_path
        )
        return step_result
