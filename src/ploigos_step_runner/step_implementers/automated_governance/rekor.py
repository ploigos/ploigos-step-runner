"""`StepImplementer` for the `automated-governance` step using Rekor.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key | Required? | Default        | Description
------------------|-----------|----------------|-----------
`rekor-server`     | True |         | Version to use when building the container image

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------------|------------
`container-image-version` | Container version to tag built image with
`image-tar-file`          | Path to the built container image as a tar file
`image-tar-hash`          | Path to the built container image as a tar file
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
    'rekor-server',
    'gpg-key',
    'gpg-user'
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
        public_key_path,
        gpg_user,
        extra_data_file
    ):
        """Creates a rekor entry as a dict object.

        Returns
        -------
        StepResult
            Dict that contains rekor entry for upload with the cli
        """
        file_hash = get_file_hash(extra_data_file)
        sig_file = extra_data_file + '.asc'
        sig_file_path = Path(sig_file)
        if sig_file_path.exists():
            sig_file_path.unlink()
        detach_sign_with_pgp_key(
            output_signature_path=sig_file,
            file_to_sign_path=extra_data_file,
            pgp_private_key_fingerprint=gpg_user
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
                        "content": base64_encode(public_key_path)
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

    @staticmethod
    def upload_to_rekor(rekor_server, extra_data_file, gpg_key, gpg_user, work_dir_path):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        rekor_entry = Rekor.create_rekor_entry(gpg_key, gpg_user, extra_data_file)
        print("Rekor Entry: " + str(rekor_entry))
        rekor_entry_path = Path(os.path.join(work_dir_path, 'entry.json'))

        if rekor_entry_path.exists():
            rekor_entry_path.unlink()
        rekor_entry_path_name = os.path.join(work_dir_path, 'entry.json')
        rekor_entry_path.write_text(json.dumps(rekor_entry))
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
            rekor_entry_path_name,
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
        rekor_server = self.get_value('rekor-server')
        extra_data_file = os.path.join(self.work_dir_path, self.step_name+'.json')
        extra_data_file_path = Path(extra_data_file)
        if extra_data_file_path.exists():
            extra_data_file_path.unlink()
        self.workflow_result.write_results_to_json_file(extra_data_file_path)
        rekor_entry, rekor_uuid = self.upload_to_rekor(
            rekor_server,
            extra_data_file,
            self.get_value('gpg-key'),
            self.get_value('gpg-user'),
            self.work_dir_path
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
