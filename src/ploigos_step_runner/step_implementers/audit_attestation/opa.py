"""`StepImplementer` for the `opa` step using Open Policy Agent.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key       | Required? | Default | Description
-------------------     |-----------|---------|-----------
`workflow-policy-uri`   | Yes       |         | URI to policy used to audit attestations

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`audit-results`     | Results of opa audit of workflow attestations
"""

import sys
from io import StringIO
import sh
from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.utils.file import download_source_to_destination
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback


DEFAULT_CONFIG = {}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'workflow-policy-uri'
]
class OpenPolicyAgent(StepImplementer):  # pylint: disable=too-few-public-methods
    """`StepImplementer` for the generic Rekor class.
    """

    DEFAULT_WORKFLOW_POLICY_QUERY = "data.workflowResult.passAll"
    DEFAULT_WORKFLOW_POLICY_DATA_QUERY = "data"

    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None
    ):

        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment
        )

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

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

    def _audit_attestation(self, # pylint: disable=no-self-use
        workflow_attestation_file_path,
        workflow_policy_file_path,
        workflow_policy_query):

        opa_attestation_stdout_result = StringIO()
        opa_attestation_stdout_callback = create_sh_redirect_to_multiple_streams_fn_callback([
            sys.stdout,
            opa_attestation_stdout_result
        ])
        sh.opa( # pylint: disable=no-member
            'opa',
            'eval',
            '--fail',
            '--entry',
            '-i',
            workflow_attestation_file_path,
            '-d',
            workflow_policy_file_path,
            workflow_policy_query,
            _out=opa_attestation_stdout_callback,
            _err_to_out=True,
            _tee='out'
        )

        return_code = sh.ErrorReturnCode

        return opa_attestation_stdout_callback, return_code





    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        work_dir = self.work_dir_path

        uri_artifact_key = 'evidence-uri'

        #workflow attestation uri
        workflow_attestation_uri = self.get_value(uri_artifact_key)

        if workflow_attestation_uri is None:
            step_result.success = False
            step_result.message = "No value found for " + uri_artifact_key
            return step_result

        workflow_attestation_file_path = download_source_to_destination(
            workflow_attestation_uri,
            work_dir
        )

        workflow_policy_uri = self.get_value('workflow-policy-uri')

        #Download workflow policy from configured uri
        workflow_policy_file_path = download_source_to_destination(
            workflow_policy_uri,
            work_dir)

        audit_results, return_code = self._audit_attestation(workflow_attestation_file_path,
            workflow_policy_file_path,
            self.DEFAULT_WORKFLOW_POLICY_QUERY)

        if return_code == 1:
            step_result.success = False
            step_result.message = "Attestation error: " + audit_results

            detailed_report, return_code = self._audit_attestation(workflow_attestation_file_path,
                workflow_policy_file_path,
                self.DEFAULT_WORKFLOW_POLICY_DATA_QUERY)
            audit_results = detailed_report

        else:
            step_result.message = "Audit was successful"
            audit_results = "Audit was successful"


        step_result.add_artifact(
                name='audit-results',
                value=audit_results
        )

        return step_result
