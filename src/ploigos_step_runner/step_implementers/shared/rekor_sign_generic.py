"""`StepImplementer` for the `automated-governance` step using Rekor.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key       | Required? | Default | Description
-------------------     |-----------|---------|-----------
`rekor-server-url`      | Yes       |         | URL for Rekor server to upload artifact(s) to.
`signer-pgp-private-key`| Yes       |         | PGP Private Key used to sign the image

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`rekor-uuid`        | UUID of Rekor entry created by artifact upload.
`rekor-entry`       | DEPRECIATED. Will likely be removed in next release.
"""

from base64 import b64encode
import json
import sys
from io import StringIO
import sh
from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.utils.file import base64_encode, get_file_hash,\
    download_source_to_destination
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback
from ploigos_step_runner.utils.pgp import detach_sign_with_pgp_key
from ploigos_step_runner.utils.pgp import import_pgp_key
from ploigos_step_runner.utils.pgp import export_pgp_public_key


DEFAULT_CONFIG = {}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'rekor-server-url',
    'signer-pgp-private-key'
]
class RekorSignGeneric(StepImplementer):  # pylint: disable=too-few-public-methods
    """`StepImplementer` for the generic Rekor class.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        artifact_to_sign_uri_config_key,
        environment=None
    ):
        self.__artifact_to_sign_uri_config_key = artifact_to_sign_uri_config_key
        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment
        )

    @property
    def artifact_to_sign_uri_config_key(self):
        """Getter for the artifact to sign config key.

        Returns
        -------
        str
            Config key that is used to obtain the artifact
            that needs to be signed
        """
        return self.__artifact_to_sign_uri_config_key

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

    def _create_rekor_entry( # pylint: disable=no-self-use
        self,
        signer_pgp_public_key,
        signer_pgp_private_key_fingerprint,
        path_to_file,
        artifact_to_sign_uri
    ):
        """Method to generate a rekor entry

        Parameters
        ----------
        signer_pgp_public_key: str
            Public key obtained from the private key fingerprint
        signer_pgp_private_key_fingerprint: str
            PGP fingerprint obtained from importing the private key
        path_to_file: str
            Path to file to be signed
        artifact_to_sign_uri: str
            URI where artifact was pulled from

        Returns
        -------
        dict
            Dictionary containing the rekor generated entry.


        """

        file_hash = get_file_hash(path_to_file)
        sig_file = path_to_file + '.asc'

        base64_public_key = b64encode(signer_pgp_public_key.encode('utf-8')).decode('utf-8')

        detach_sign_with_pgp_key(
            output_signature_path=sig_file,
            file_to_sign_path=path_to_file,
            pgp_private_key_fingerprint=signer_pgp_private_key_fingerprint
        )

        #Base 64 encode the file

        with open(path_to_file, 'rb') as file_bytes:
            base64_encoded_data = b64encode(file_bytes.read()).decode('utf-8')

        rekor_entry = {
            "kind": "rekord",
            "apiVersion": "0.0.1",
            "spec": {
                "signature": {
                    "format": "pgp",
                    "content": base64_encode(sig_file),
                    "publicKey": {
                        "content": base64_public_key
                    }
                },
                "data": {
                    "content": base64_encoded_data,
                    "hash": {
                        "algorithm": "sha256",
                        "value": file_hash
                    }
                },
                "extraData": {
                    "signed-artifact-uri": artifact_to_sign_uri

                }
            }
        }
        return rekor_entry

    def _upload_to_rekor(
        self,
        rekor_server,
        rekor_entry
    ):
        """Method to upload a rekor entry to provided rekor server

        Parameters
        ----------
        rekor_server: str
            URL to rekor server
        signer_pgp_private_key_fingerprint: str
            PGP fingerprint obtained from importing the private key
        path_to_file: str
            Path to file to be signed
        artifact_to_sign_uri: str
            URI where artifact was pulled from

        Returns
        -------
        str:
            Returns rekor uuid returned from upload command

        """

        rekor_entry_path = self.write_working_file(
            filename='entry.json',
            contents=bytes(json.dumps(rekor_entry), 'utf-8')
        )
        rekor_upload_stdout_result = StringIO()
        rekor_upload_stdout_callback = create_sh_redirect_to_multiple_streams_fn_callback([
            sys.stdout,
            rekor_upload_stdout_result
        ])
        rekor = sh.rekor( # pylint: disable=no-member
            'upload',
            '--rekor_server',
            rekor_server,
            '--entry',
            rekor_entry_path,
            _out=rekor_upload_stdout_callback,
            _err_to_out=True,
            _tee='out'
        )
        rekor_uuid = str(rekor).rsplit('/', maxsplit=1)[-1].strip(' \n')
        return rekor_uuid

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)
        rekor_server = self.get_value('rekor-server-url')

        work_dir = self.work_dir_path
        artifact_to_sign_uri = self.get_value(self.artifact_to_sign_uri_config_key)
        #Download artifact that needs to be signed and place at work_dir.
        #Path to file is returned as string
        path_to_file = download_source_to_destination(
            artifact_to_sign_uri,
            work_dir)

        # get the pgp private key to sign the image with
        signer_pgp_private_key = self.get_value(
            'signer-pgp-private-key'
        )

        # import the PGP key and get the finger print
        signer_pgp_private_key_fingerprint = import_pgp_key(
            pgp_private_key=signer_pgp_private_key
        )

        signer_pgp_public_key = export_pgp_public_key(signer_pgp_private_key_fingerprint)

        rekor_entry = self._create_rekor_entry(
            signer_pgp_public_key,
            signer_pgp_private_key_fingerprint,
            path_to_file,
            artifact_to_sign_uri
        )

        rekor_uuid = self._upload_to_rekor(
            rekor_server,
            rekor_entry
        )
        step_result.add_artifact(
                name='rekor-entry',
                value=rekor_entry
        )
        step_result.add_artifact(
                name='rekor-uuid',
                value=rekor_uuid
        )
        rekor_uri = rekor_server + '/api/v1/log/entries/' + rekor_uuid
        step_result.add_artifact(
                name='rekor-entry-uri',
                value=rekor_uri
        )
        return step_result
