"""`StepImplementer` for the `automated-governance` step using Rekor.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key  | Required? | Default | Description
-------------------|-----------|---------|-----------
`rekor-server-url` | Yes       |         | URL for Rekor server to upload artifact(s) to.
`signer-pgp-public-key-path` \
                   | Yes       |         | DEPRECIATED. Will be removed in next release in favor \
                                           of automatically getting public key from private key. \
                                           Path to PGP public key corresponding to private key \
                                           that will be used to sign the Rekor artifact.
`signer-pgp-private-key-user` \
                   | Yes       |         | DEPRECIATED. Will be removed in next release in favor \
                                           of `signer-pgp-private-key` which will import a given \
                                           PGP private key and automatically determine the \
                                           PGP private key fingerprint.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`rekor-uuid`        | UUID of Rekor entry created by artifact upload.
`rekor-entry`       | DEPRECIATED. Will likely be removed in next release.
"""

import json
import os
import sys
from io import StringIO
from pathlib import Path

import sh
from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.utils.file import base64_encode, get_file_hash
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback
from ploigos_step_runner.utils.pgp import detach_sign_with_pgp_key


DEFAULT_CONFIG = {}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'rekor-server-url',
    'signer-pgp-public-key-path',
    'signer-pgp-private-key-user'
]
class Rekor(StepImplementer):  # pylint: disable=too-few-public-methods
    """`StepImplementer` for the `automated-governance` step using Rekor.
    """

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

    @staticmethod
    def create_rekor_entry(
        signer_pgp_public_key_path,
        signer_pgp_private_key_user,
        extra_data_file
    ):
        """TODO: function will be refactored in next release. will doc then.
        """
        file_hash = get_file_hash(extra_data_file)
        sig_file = extra_data_file + '.asc'
        sig_file_path = Path(sig_file)
        if sig_file_path.exists():
            sig_file_path.unlink()
        detach_sign_with_pgp_key(
            output_signature_path=sig_file,
            file_to_sign_path=extra_data_file,
            pgp_private_key_fingerprint=signer_pgp_private_key_user
        )
        base64_encoded_extra_data = base64_encode(extra_data_file)
        rekor_entry = {
            "kind": "rekord",
            "apiVersion": "0.0.1",
            "spec": {
                "signature": {
                    "format": "pgp",
                    "content": base64_encode(sig_file),
                    "publicKey": {
                        "content": base64_encode(signer_pgp_public_key_path)
                    }
                },
                "data": {
                    "content": base64_encoded_extra_data,
                    "hash": {
                        "algorithm": "sha256",
                        "value": file_hash
                    }
                },
                "extraData": base64_encoded_extra_data
            }
        }
        return rekor_entry

    def upload_to_rekor(
        self,
        rekor_server,
        extra_data_file,
        signer_pgp_public_key_path,
        signer_pgp_private_key_user
    ):
        """TODO: function will be refactored in next release. will doc then.
        """
        rekor_entry = Rekor.create_rekor_entry(
            signer_pgp_public_key_path=signer_pgp_public_key_path,
            signer_pgp_private_key_user=signer_pgp_private_key_user,
            extra_data_file=extra_data_file
        )

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
        rekor_uuid = str(rekor).split('/')[-1].strip(' \n')
        return rekor_entry, rekor_uuid

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)
        rekor_server = self.get_value('rekor-server-url')
        extra_data_file = os.path.join(self.work_dir_path, self.step_name+'.json')
        extra_data_file_path = Path(extra_data_file)
        if extra_data_file_path.exists():
            extra_data_file_path.unlink()
        self.workflow_result.write_results_to_json_file(extra_data_file_path)
        rekor_entry, rekor_uuid = self.upload_to_rekor(
            rekor_server=rekor_server,
            extra_data_file=extra_data_file,
            signer_pgp_public_key_path=self.get_value('signer-pgp-public-key-path'),
            signer_pgp_private_key_user=self.get_value('signer-pgp-private-key-user')
        )
        step_result.add_artifact(
                name='rekor-entry',
                value=rekor_entry
        )
        step_result.add_artifact(
                name='rekor-uuid',
                value=rekor_uuid
        )
        return step_result
