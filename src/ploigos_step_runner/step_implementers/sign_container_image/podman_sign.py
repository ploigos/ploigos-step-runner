"""`StepImplementer` for the `sign-container-image` step using Podman to create an image signature.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key                        | Required? | Default  | Description
-----------------------------------------|-----------|----------|-------------
`container-image-signer-pgp-private-key` | Yes       |          | PGP Private Key used to \
                                                                  sign the image
`container-image-tag`                    | Yes       |          | Tag of the container image to sign

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                   | Description
--------------------------------------|------------
`container-image-signature-private-key-fingerprint` | Fingerprint for the private key used to sign \
                                                      the container image.
`container-image-signature-file-path`               | File path to create image signature.
`container-image-signature-name`                    | Fully qualified name of the \
                                                      name of the image signature, \
                                                      including: organization, repo, \
                                                      and hash. <br/>\
                                                      ex: user/hello-node@sha256=\
                                                      2cbdb73c9177e63e85d267f738e9\
                                                      9e368db3f806eab4c541f5c6b719\
                                                      e69f1a2b/signature-1
"""
import glob
import os
import re
import sys
from io import StringIO

import sh
from ploigos_step_runner import StepImplementer
from ploigos_step_runner.step_result import StepResult
from ploigos_step_runner.utils.io import create_sh_redirect_to_multiple_streams_fn_callback
from ploigos_step_runner.exceptions import StepRunnerException

DEFAULT_CONFIG = {
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'container-image-signer-pgp-private-key',
    'container-image-tag'
]

class PodmanSign(StepImplementer):
    """`StepImplementer` for the `sign-container-image` step using Podman to create
    an image signature.
    """

    # Example input to match on:
    #   sec:-:3072:1:CF4AC14A3D109637:1601483310:1664555310::-:::scESC::::::23::0:
    #   fpr:::::::::DD7208BA0A6359F65B906B29CF4AC14A3D109637:
    #   grp:::::::::A483EE079EC1D58A954E3AAF3BCC61EDD7596BF0:
    GPG_IMPORT_FINGER_PRINT_REGEX = re.compile(r"^fpr:+([^:]+):$", re.MULTILINE)

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

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # get the pgp private key to sign the image with
        image_signer_pgp_private_key = self.get_value(
            'container-image-signer-pgp-private-key'
        )

        # get the uri to the image to sign
        container_image_tag = self.get_value('container-image-tag')

        image_signatures_directory = self.create_working_dir_sub_dir(
            sub_dir_relative_path='image-signature'
        )

        # import the PGP key and get the finger print
        try:
            image_signer_pgp_private_key_fingerprint = PodmanSign.__import_pgp_key(
                pgp_private_key=image_signer_pgp_private_key
            )
            step_result.add_artifact(
                name='container-image-signature-private-key-fingerprint',
                value=image_signer_pgp_private_key_fingerprint
            )

            # sign the image
            signature_file_path = PodmanSign.__sign_image(
                pgp_private_key_fingerprint=image_signer_pgp_private_key_fingerprint,
                image_signatures_directory=image_signatures_directory,
                container_image_tag=container_image_tag
            )
            step_result.add_artifact(
                name='container-image-signature-file-path',
                value=signature_file_path,
            )
            signature_name = os.path.relpath(signature_file_path, image_signatures_directory)
            step_result.add_artifact(
                name='container-image-signature-name',
                value=signature_name
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = str(error)

        return step_result

    @staticmethod
    def __import_pgp_key(
        pgp_private_key
    ):
        print("Import PGP private key to sign container image(s) with")
        try:
            # import the key

            # NOTE: GPG is weird in that it sends "none error" output to stderr even on success...
            #       so merge the stderr into stdout
            gpg_import_stdout_result = StringIO()
            gpg_import_stdout_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stdout,
                gpg_import_stdout_result
            ])
            sh.gpg( # pylint: disable=no-member
                '--import',
                '--fingerprint',
                '--with-colons',
                '--import-options=import-show',
                _in=pgp_private_key,
                _out=gpg_import_stdout_callback,
                _err_to_out=True,
                _tee='out'
            )

            # get the fingerprint of the imported key
            #
            # NOTE: if more then one match just using first one...
            gpg_imported_pgp_private_key_fingerprints = re.findall(
                PodmanSign.GPG_IMPORT_FINGER_PRINT_REGEX,
                gpg_import_stdout_result.getvalue()
            )
            if len(gpg_imported_pgp_private_key_fingerprints) < 1:
                raise StepRunnerException(
                    "Error getting PGP fingerprint for PGP key"
                    " to sign container image(s) with. See stdout and stderr for more info."
                )
            pgp_private_key_fingerprint = gpg_imported_pgp_private_key_fingerprints[0]

            print(
                "Imported PGP private key to sign container image(s) with: "
                f"fingerprint='{pgp_private_key_fingerprint}'"
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error importing pgp private key: {error}"
            ) from error

        return pgp_private_key_fingerprint

    @staticmethod
    def __sign_image(
        pgp_private_key_fingerprint,
        image_signatures_directory,
        container_image_tag
    ):
        # sign image
        print(
            f"Sign image ({container_image_tag}) "
            f"with PGP private key ({pgp_private_key_fingerprint})"
        )
        try:
            # NOTE: for some reason the output from podman sign goes to stderr so....
            #       merge the two streams
            sh.podman.image( # pylint: disable=no-member
                "sign",
                f"--sign-by={pgp_private_key_fingerprint}",
                f"--directory={image_signatures_directory}",
                f"docker://{container_image_tag}",
                _out=sys.stdout,
                _err_to_out=True,
                _tee='out'
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error signing image ({container_image_tag}): {error}"
            ) from error

        # get image signature file path
        signature_file_paths = glob.glob(
            f"{image_signatures_directory}/**/signature-*",
            recursive=True
        )

        if len(signature_file_paths) != 1:
            raise StepRunnerException(
                f"Unexpected number of signature files, expected 1: {signature_file_paths}"
            )

        signature_file_path = signature_file_paths[0]
        print(
            f"Signed image ({container_image_tag}) with PGP private key "
            f"({pgp_private_key_fingerprint}): '{signature_file_path}'"
        )

        return signature_file_path
