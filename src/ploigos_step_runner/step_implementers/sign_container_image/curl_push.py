"""`StepImplementer` for the `sign-container-image` step using Curl to push an image signature
to a destination.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key                           | Required? | Default | Description
--------------------------------------------|-----------|---------|-------------
`container-image-signature-server-url`      | Yes       |         | Url of the signature server
`container-image-signature-server-username` | Yes       |         | Username to log onto the \
                                                                   signature server
`container-image-signature-server-password` | Yes       |         | Password to log onto the \
                                                                   signature server
`container-image-signature-file-path`       | Yes       |         | Local file path to container \
                                                                    image signature to push.
`container-image-signature-name`            | Yes       |         | Fully qualified name of the \
                                                                    name of the image signature, \
                                                                    including: organization, repo, \
                                                                    and hash. <br/>\
                                                                    ex: user/hello-node@sha256=\
                                                                    2cbdb73c9177e63e85d267f738e9\
                                                                    9e368db3f806eab4c541f5c6b719\
                                                                    e69f1a2b/signature-1
`with-fips`                                 | No        | True    | If set to false, allows use\
                                                                    of MD5 and SHA1 in container\
                                                                    signature verification.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                   | Description
--------------------------------------|------------
`container-image-signature-url`       | URL signature was uploaded to
`container-image-signature-file-md5`  | MD5 hash of signature file
`container-image-signature-file-sha1` | SHA1 Hash of signature file
"""

import hashlib
import re
import sys
from io import StringIO

import sh
from ploigos_step_runner import StepImplementer
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_result import StepResult
from ploigos_step_runner.utils.io import create_sh_redirect_to_multiple_streams_fn_callback

DEFAULT_CONFIG = {
    'with-fips': True
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'container-image-signature-server-url',
    'container-image-signature-server-username',
    'container-image-signature-server-password',
    'container-image-signature-file-path',
    'container-image-signature-name'
]

class CurlPush(StepImplementer):
    """`StepImplementer` for the `sign-container-image` step using Curl to push an image signature
    to a destination.
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

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # extract configs
        signature_server_url = self.get_value(
            'container-image-signature-server-url'
        )
        signature_server_username = self.get_value(
            'container-image-signature-server-username'
        )
        signature_server_password = self.get_value(
            'container-image-signature-server-password'
        )

        # extract step results
        container_image_signature_file_path = self.get_value('container-image-signature-file-path')
        container_image_signature_name = self.get_value('container-image-signature-name')
        with_fips = self.get_value('with-fips')

        try:
            container_image_signature_url, signature_file_md5, signature_file_sha1 = \
                CurlPush.__curl_file(
                    container_image_signature_file_path=container_image_signature_file_path,
                    container_image_signature_name=container_image_signature_name,
                    signature_server_url=signature_server_url,
                    signature_server_username=signature_server_username,
                    signature_server_password=signature_server_password,
                    with_fips=with_fips
                )

            step_result.add_artifact(
                name='container-image-signature-url', value=container_image_signature_url,
            )
            if not with_fips:
                step_result.add_artifact(
                    name='container-image-signature-file-md5', value=signature_file_md5,
                )
                step_result.add_artifact(
                    name='container-image-signature-file-sha1', value=signature_file_sha1
                )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = str(error)

        return step_result

    @staticmethod
    def __curl_file(  # pylint: disable=too-many-arguments
            container_image_signature_file_path,
            container_image_signature_name,
            signature_server_url,
            signature_server_username,
            signature_server_password,
            with_fips
    ):
        """Sends the signature file

        Raises
        ------
        StepRunnerException
            If error pushing image signature.
        """
        # remove any trailing / from url
        signature_server_url = re.sub(r'/$', '', signature_server_url)
        container_image_signature_url = f"{signature_server_url}/{container_image_signature_name}"

        curl_additional_options = []
        signature_file_md5 = None
        signature_file_sha1 = None

        # calculate hashes
        if not with_fips:
            with open(container_image_signature_file_path, 'rb') as container_image_signature_file:
                container_image_signature_file_contents = container_image_signature_file.read()
                signature_file_md5 = hashlib.md5(container_image_signature_file_contents)\
                    .hexdigest()
                signature_file_sha1 = hashlib.sha1(container_image_signature_file_contents)\
                    .hexdigest()

            curl_additional_options += [
                '--header', f'X-Checksum-Sha1:{signature_file_sha1}',
                '--header', f'X-Checksum-MD5:{signature_file_md5}',
            ]

        try:
            stdout_result = StringIO()
            stdout_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stdout,
                stdout_result
            ])

            # -s: Silent
            # -S: Show error
            # -f: Don't print out failure document
            # -v: Verbose
            sh.curl(  # pylint: disable=no-member
                '-sSfv',
                '-X', 'PUT',
                '--user', f"{signature_server_username}:{signature_server_password}",
                '--upload-file', container_image_signature_file_path,
                *curl_additional_options,
                container_image_signature_url,
                _out=stdout_callback,
                _err_to_out=True,
                _tee='out'
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error pushing signature file to signature server using curl: {error}"
            ) from error

        return container_image_signature_url, signature_file_md5, signature_file_sha1
