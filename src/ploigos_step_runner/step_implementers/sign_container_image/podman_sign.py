"""`StepImplementer` for the `sign-container-image` step using Podman to create an image signature.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key                                | Required? | Default | Description
-------------------------------------------------|-----------|---------|-------------
`signer-pgp-private-key`                         | Yes       |         | PGP Private Key used to sign the image
`container-image-signer-pgp-private-key` (deprecated)\
                                                 | Yes       |         | PGP Private Key used to sign the image
`container-image-signature-destination-url`      | No        |         | URL to upload the container image signature to.\
                                                                         The container image signature name will be appended \
                                                                         to form the container image signature URI. \
                                                                         <br /><br />\
                                                                         Must start with `/` or `file://` to upload \
                                                                         to local file path. \
                                                                         <br /><br />\
                                                                         Or must start with `http://` or `https://` to \
                                                                         upload via a `PUT` to a remote location.
`container-image-signature-destination-username` | No        |         | Username to use when doing upload via http(s).
`container-image-signature-destination-password` | No        |         | Password to use when doing upload via http(s).
`[container-image-pull-registry, \
  container-image-push-registry, \
  container-image-registry]`                     | Maybe    |          | If `use-container-image-short-addres` is `True`, \
                                                                         container image registry to pull container image from when deploying.

`[container-image-pull-repository, \
  container-image-push-repository, \
  container-image-repository]`                   | Yes      |          | Container image repository within the given container image registry \
                                                                         to pull container image from when deploying.
`[container-image-pull-digest,
  container-image-push-digest,
  container-image-digest]                        | Maybe    |          | If `use-container-image-digest` is `True`,
                                                                         container image digest to pull container image with when deploying.
`[container-image-pull-tag,
  container-image-push-tag,
  container-image-tag]                           | Maybe    |          | If `use-container-image-digest` is `False`,
                                                                         container image tag to pull container image with when deploying.
`use-container-image-short-addres`               | No        | `False`  | If `True` then use container image short address (no registry).\
                                                                          If `False` then use container image full address (including registry).
`use-container-image-digest`                     | No       | `True`   | If `True` then use container image digest in container image address when \
                                                                         pulling container image for deployment.<br/>\
                                                                         If `False` then use container image tag in container image address when \
                                                                         pulling container image for deployment.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                        | Description
-------------------------------------------|------------
`container-image-signature-signer-private-key-fingerprint` \
                                           | Fingerprint for the private key used to sign \
                                             the container image.
`container-image-signed-address`           | Container image address that was signed since container image signature includes the address.
`container-image-signature-file-path`      | File path to created image signature.
`container-image-signature-name`           | Fully qualified name of the \
                                             name of the image signature, \
                                             including: organization, repo, \
                                             and hash. <br/>\
                                             ex: user/hello-node@sha256=\
                                             2cbdb73c9177e63e85d267f738e9\
                                             9e368db3f806eab4c541f5c6b719\
                                             e69f1a2b/signature-1
`container-image-signature-uri`            | URI of the uploaded container image signature.
`container-image-signature-upload-results` | Results of uploading the container image \
                                             signature to the given destination.
"""# pylint: disable=line-too-long
import glob
import os
import sys

import sh
from ploigos_step_runner.utils.strutils import strtobool
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared import ContainerDeployMixin
from ploigos_step_runner.utils.containers import container_registries_login
from ploigos_step_runner.utils.file import upload_file
from ploigos_step_runner.utils.pgp import import_pgp_key

DEFAULT_CONFIG = {
    'src-tls-verify': 'true'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    # signer-pgp-private-key - new key name
    # container-image-signer-pgp-private-key - old key name
    ['signer-pgp-private-key', 'container-image-signer-pgp-private-key']
]

class PodmanSign(ContainerDeployMixin, StepImplementer):
    """`StepImplementer` for the `sign-container-image` step using Podman to create
    an image signature.
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
        return {**ContainerDeployMixin.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS + \
            ContainerDeployMixin._required_config_or_result_keys()

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # get the pgp private key to sign the image with
        signer_pgp_private_key = self.get_value(
            ['signer-pgp-private-key', 'container-image-signer-pgp-private-key']
        )

        # get the uri to the image to sign
        container_image_address = self._get_deploy_time_container_image_address()

        image_signatures_directory = self.create_working_dir_sub_dir(
            sub_dir_relative_path='image-signature'
        )
        try:
            # import the PGP key and get the finger print
            signer_pgp_private_key_fingerprint = import_pgp_key(
                pgp_private_key=signer_pgp_private_key
            )
            step_result.add_artifact(
                name='container-image-signature-signer-private-key-fingerprint',
                value=signer_pgp_private_key_fingerprint
            )

            # login to any provider container registries
            # NOTE 1: can not use auth file, even though we want to, because podman image sign
            #         does not accept authfile.
            #         https://github.com/containers/podman/issues/10866
            # NOTE 2: have to force login to use podman because even though logging in with
            #         any of the tools should work, in testing the podman sign only worked
            #         from within the python virtual environment if the login happened with podman.
            container_registries_login(
                registries=self.get_value('container-registries'),
                containers_config_tls_verify=strtobool(self.get_value('src-tls-verify')),
                container_command_short_name='podman'
            )

            # sign the image
            signature_file_path = PodmanSign.__sign_image(
                pgp_private_key_fingerprint=signer_pgp_private_key_fingerprint,
                image_signatures_directory=image_signatures_directory,
                container_image_address=container_image_address
            )
            step_result.add_artifact(
                name='container-image-signed-address',
                value=container_image_address,
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

             # upload the image signature
            container_image_signature_destination_url = self.get_value(
                'container-image-signature-destination-url'
            )
            if container_image_signature_destination_url:
                container_image_signature_destination_uri = \
                    f"{container_image_signature_destination_url}/{signature_name}"
                step_result.add_artifact(
                    name='container-image-signature-uri',
                    description='URI of the uploaded container image signature',
                    value=container_image_signature_destination_uri
                )

                upload_result = upload_file(
                    file_path=signature_file_path,
                    destination_uri=container_image_signature_destination_uri,
                    username=self.get_value('container-image-signature-destination-username'),
                    password=self.get_value('container-image-signature-destination-password')
                )
                step_result.add_artifact(
                    name='container-image-signature-upload-results',
                    description='Results of uploading the container image signature' \
                                ' to the given destination.',
                    value=upload_result
                )
        except (RuntimeError, StepRunnerException) as error:
            step_result.success = False
            step_result.message = str(error)

        return step_result

    @staticmethod
    def __sign_image(
        pgp_private_key_fingerprint,
        image_signatures_directory,
        container_image_address
    ):
        # sign image
        print(
            f"Sign image ({container_image_address}) "
            f"with PGP private key ({pgp_private_key_fingerprint})"
        )
        try:
            # NOTE: for some reason the output from podman sign goes to stderr so....
            #       merge the two streams
            sh.podman.image( # pylint: disable=no-member
                "sign",
                f"--sign-by={pgp_private_key_fingerprint}",
                f"--directory={image_signatures_directory}",
                f"docker://{container_image_address}",
                _out=sys.stdout,
                _err_to_out=True,
                _tee='out'
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error signing image ({container_image_address}): {error}"
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
            f"Signed image ({container_image_address}) with PGP private key "
            f"({pgp_private_key_fingerprint}): '{signature_file_path}'"
        )

        return signature_file_path
