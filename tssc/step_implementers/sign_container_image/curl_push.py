"""StepImplementer for the sign-container-image step using Podman to push an image signature using


Step Configuration
------------------
Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key                           | Required? | Default  | Description
|---------------------------------------------|-----------|----------|-------------
| `container-image-signature-server-url`      | True      |          |
    Url of the signature server
| `container-image-signature-server-username` | True      |          |
    Username to log onto the signature server
| `container-image-signature-server-password` | True      |          |
    Password to log onto the signature server


Expected Previous Step Results
------------------------------
Results expected from previous steps that this step requires.

| Step Name             | Result Key                           | Description
|-----------------------|--------------------------------------|-------------------------------
| `sign-container-image`| `container-image-signature-file-path`| File path where signature /
                                                                 is located /
                                                                 eg) /tmp/jkeam/hello-node@/
                                                                     sha256=2cbdb73c9177e63/
                                                                     e85d267f738e99e368db3f/
                                                                     806eab4c541f5c6b719e69/
                                                                     f1a2b/signature-1
| `sign-container-image`| `container-image-signature-name`     | Fully qualified name of the /
                                                                 name of the image signature, /
                                                                 including: /
                                                                 organization, repo, and hash /
                                                                 eg) jkeam/hello-node@sha256=/
                                                                 2cbdb73c9177e63e85d267f738e9/
                                                                 9e368db3f806eab4c541f5c6b719/
                                                                 e69f1a2b/signature-1


Results
-------
Results output by this step.

| Result Key                            | Description
|---------------------------------------|------------
| `container-image-signature-url`       | URL signature was uploaded to
| `container-image-signature-file-md5`  | MD5 hash of signature file
| `container-image-signature-file-sha1` | SHA1 Hash of signature file
"""

import hashlib
import re
import sys
from io import StringIO
from operator import itemgetter

import sh
from tssc import StepImplementer
from tssc.step_implementer import DefaultSteps
from tssc.utils.io import create_sh_redirect_to_multiple_streams_fn_callback

DEFAULT_CONFIG = {
}

REQUIRED_CONFIG_KEYS = [
    'container-image-signature-server-url',
    'container-image-signature-server-username',
    'container-image-signature-server-password'
]

class CurlPush(StepImplementer):
    """StepImplementer for the push-container-signature step using"""

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
        """Run step and perform the curl"""
        # extract configs
        signature_server_url = self.get_config_value('container-image-signature-server-url')
        signature_server_username = self.get_config_value(
            'container-image-signature-server-username'
        )
        signature_server_password = self.get_config_value(
            'container-image-signature-server-password'
        )

        # extract step results
        previous_sign_container_image_step_results = self.get_step_results(
            DefaultSteps.SIGN_CONTAINER_IMAGE
        )
        CurlPush.__verify_previous_sign_container_image_step_results(
            previous_sign_container_image_step_results,
            ['container-image-signature-file-path', 'container-image-signature-name']
        )
        container_image_signature_file_path, container_image_signature_name = itemgetter(
            'container-image-signature-file-path',
            'container-image-signature-name'
        )(previous_sign_container_image_step_results)

        # upload
        container_image_signature_url, signature_file_md5, signature_file_sha1 = \
            CurlPush.__curl_file(
                container_image_signature_file_path=container_image_signature_file_path,
                container_image_signature_name=container_image_signature_name,
                signature_server_url=signature_server_url,
                signature_server_username=signature_server_username,
                signature_server_password=signature_server_password
            )

        return {
            'container-image-signature-url': container_image_signature_url,
            'container-image-signature-file-md5': signature_file_md5,
            'container-image-signature-file-sha1': signature_file_sha1
        }

    @staticmethod
    def __verify_previous_sign_container_image_step_results(step_results, keys):
        """Verifies that the given step results has the expected keys"""
        if step_results is None:
            raise RuntimeError(f"Missing step results from {DefaultSteps.SIGN_CONTAINER_IMAGE}")

        for key in keys:
            result = step_results.get(key)
            if result is None:
                raise RuntimeError(
                    f"Missing {key} step results from {DefaultSteps.SIGN_CONTAINER_IMAGE}"
                )

    @staticmethod
    def __curl_file(
            container_image_signature_file_path,
            container_image_signature_name,
            signature_server_url,
            signature_server_username,
            signature_server_password
    ):
        """Sends the signature file"""
        # remove any trailing / from url
        signature_server_url = re.sub(r'/$', '', signature_server_url)
        container_image_signature_url = f"{signature_server_url}/{container_image_signature_name}"

        # calculate hashes
        with open(container_image_signature_file_path, 'rb') as container_image_signature_file:
            container_image_signature_file_contents = container_image_signature_file.read()
            signature_file_md5 = hashlib.md5(container_image_signature_file_contents).hexdigest()
            signature_file_sha1 = hashlib.sha1(container_image_signature_file_contents).hexdigest()

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
                '--header', f'X-Checksum-Sha1:{signature_file_sha1}',
                '--header', f'X-Checksum-MD5:{signature_file_md5}',
                '--user', f"{signature_server_username}:{signature_server_password}",
                '--upload-file', container_image_signature_file_path,
                container_image_signature_url,
                _out=stdout_callback,
                _err_to_out=True,
                _tee='out'
            )
        except sh.ErrorReturnCode as error:
            raise RuntimeError(
                f"Unexpected error curling signature file to signature server: {error}"
            ) from error

        return container_image_signature_url, signature_file_md5, signature_file_sha1
