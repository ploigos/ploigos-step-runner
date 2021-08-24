"""`StepImplementer` for the `generate_evidence` step which builds and pushes and artifacts archive.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key           | Required? | Default | Description
----------------------------|-----------|---------|-------------
`organization`              | True      |         | Organization that this workflow is for. \
                                                    Used in archive name.
`application-name`          | True      |         | Application that this workflow is for. \
                                                    Used in archive name.
`service-name`              | True      |         | Service that this workflow is for. \
                                                    Used in archive name.
`version`                   | True      |         | Version of applicaiton service that this \
                                                    workflow is for. \
                                                    Used in archive name. \
`evidence-destination-url` \
                            | False     |         | URL to upload the results archive to.\
                                                    NOTE: TODO describe how URI is formed
                                                    <br /><br />\
                                                    Must start with `/` or `file://` to upload \
                                                    to local file path. \
                                                    <br /><br />\
                                                    Or must start with `http://` or `https://` to \
                                                    upload via a `PUT` to a remote location.
`evidence-destination-username` \
                            | No        |         | Username to use when doing upload via http(s).
`evidence-destination-password` \
                            | No        |         | Password to use when doing upload via http(s).

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key              | Description
---------------------------------|------------
`evidence-path`                  | Absolute path to the generated evidence JSON file.
`evidence-uri`                   | URI of the uploaded results archive.
`evidence-upload-results`        | Results of uploading the results archive to \
                                   the given destination.

"""

import json
import os

from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.utils.file import upload_file

DEFAULT_CONFIG = {

}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'organization',
    'application-name',
    'service-name',
    'version'
]
class GenerateEvidence(StepImplementer):
    """`StepImplementer` for the `report` step which builds and pushes and artifacts archive.
    """

    API_VERSION = "automated-governance/v1alpha1"
    KIND = "WorkflowEvidence"

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

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
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        #Gather all evidence from steps/sub steps
        evidence = self.__gather_evidence()

        #If no evidence is found then return a step result reflecting that status.
        if not evidence:
            step_result.add_artifact(
                name='result-generate-evidence',
                value='No evidence to generate.',
                description='Evidence from all previously run steps.'
            )
            step_result.message = "No evidence generated from previously run steps"
            return step_result

        org = self.get_value('organization')
        app = self.get_value('application-name')
        service = self.get_value('service-name')
        version = self.get_value('version')

        result_evidence_name = f"{org}-{app}-{service}-{version}-evidence.json"

        work_dir = self.work_dir_path

        evidence_path = os.path.join(work_dir, result_evidence_name)

        #Format into json and write out to file in working directory
        with open(evidence_path, "w", encoding='utf-8') as evidence_file:
            json.dump(evidence, evidence_file, indent=4)

        evidence_destination_url = self.get_value('evidence-destination-url')
        evidence_destination_uri = f"{evidence_destination_url}/" \
                f"{org}/{app}/{service}/{result_evidence_name}"

        #Upload file to datastore
        if evidence_file and evidence_destination_url:
            try:
                upload_result = upload_file(
                    file_path=evidence_path,
                    destination_uri=evidence_destination_uri,
                    username=self.get_value('evidence-destination-username'),
                    password=self.get_value('evidence-destination-password')
                )
                step_result.add_artifact(
                    name='evidence-upload-results',
                    description='Results of uploading the evidence JSON file ' \
                        'to the given destination.',
                    value=upload_result
                )
                step_result.add_artifact(
                    name='evidence-uri',
                    description='URI of the uploaded results archive.',
                    value=evidence_destination_uri
                )

                step_result.success = True
                step_result.message = 'Evidence successfully packaged ' \
                'in JSON file and uploaded to data store.'

            except RuntimeError as error:
                step_result.success = False
                step_result.message = str(error)
                return step_result
        else:
            step_result.success = True
            step_result.message = 'Evidence successfully packaged ' \
            'in JSON file but was not uploaded to data store (no '\
            'destination URI specified).'


        step_result.add_artifact(
            name='evidence-path',
            value=evidence_path,
            description='File path of evidence.'
        )

        return step_result

    def __gather_evidence(self):
        """Gather all collected evidence

        Returns
        -------
        dict
            Dictionary containing evidence (values) for each step (key) that
            has collected evidence.

        """

        gathered_evidence = None
        attestations_keyword = 'attestations'
        workflow_dict = {}

        #Iterate over all previous step results
        for previous_step_result in self.workflow_result.workflow_list:
            step_name = previous_step_result.step_name
            if step_name not in workflow_dict:
                workflow_dict[step_name] = {}

            workflow_dict[step_name][attestations_keyword] = {}

            evidence = previous_step_result.evidence
            for piece_of_evidence in evidence.values():
                workflow_dict[step_name]\
                [attestations_keyword][piece_of_evidence.name]\
                 = {
                    'name': piece_of_evidence.name,
                    'value': piece_of_evidence.value,
                    'description': piece_of_evidence.description,
                 }
                if previous_step_result.environment:
                    workflow_dict[step_name]\
                    [attestations_keyword][piece_of_evidence.name]\
                     ['environment'] = previous_step_result.environment

        #Add step to workflow dictionary
        if workflow_dict:
            gathered_evidence = {
                'apiVersion': GenerateEvidence.API_VERSION,
                'kind': GenerateEvidence.KIND,
                'workflow': workflow_dict
            }

        return gathered_evidence
