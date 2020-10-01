"""StepImplementer for the sign-container-image step using Podman to push an image signature using


Step Configuration
------------------
Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key                           | Required? | Default  | Description
|---------------------------------------------|-----------|----------|-------------
| `container-image-signature-server-url`      | True      |          |
    Url where the signature server is located
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
                                                                 name -- including /
                                                                 organization, repo, and hash /
                                                                 eg) jkeam/hello-node@sha256=/
                                                                 2cbdb73c9177e63e85d267f738e9/
                                                                 9e368db3f806eab4c541f5c6b719/
                                                                 e69f1a2b/signature-1

Results
-------
Results output by this step.

| Result Key  | Description
|-------------|------------
TODO: figure out output

"""

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
    """StepImplementer for the push-container-signature step using
    """

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
        # extract configs
        signature_server_url = self.get_config_value('container-image-signature-server-url')
        signature_server_username = self.get_config_value(
            'container-image-signature-server-username'
        )
        signature_server_password = self.get_config_value(
            'container-image-signature-server-password'
        )

        # extract step results
        step_results = CurlPush.__get_step_result_values(
            self.get_step_results(DefaultSteps.SIGN_CONTAINER_IMAGE),
            ['container-image-signature-file-path', 'container-image-signature-name']
        )
        container_image_signature_file_path, container_image_signature_name = itemgetter(
            'container-image-signature-file-path',
            'container-image-signature-name'
        )(step_results)

        # upload
        container_image_signature_url = CurlPush.__curl_file(
            container_image_signature_file_path=container_image_signature_file_path,
            container_image_signature_name=container_image_signature_name,
            signature_server_url=signature_server_url,
            signature_server_username=signature_server_username,
            signature_server_password=signature_server_password
        )

        return {
            'container-image-signature-url': container_image_signature_url
        }

    @staticmethod
    def __get_step_result_values(step_results, keys):
        if step_results is None:
            raise RuntimeError(f"Missing step results from {DefaultSteps.SIGN_CONTAINER_IMAGE}")

        results = {}
        for key in keys:
            result = step_results.get(key)
            if result is None:
                raise RuntimeError(
                    f"Missing {key} step results from {DefaultSteps.SIGN_CONTAINER_IMAGE}"
                )
            results[key] = result
        return results

    @staticmethod
    def __curl_file(
            container_image_signature_file_path,
            container_image_signature_name,
            signature_server_url,
            signature_server_username,
            signature_server_password
    ):
        # remove any trailing / from url
        signature_server_url = re.sub(r'/$', '', signature_server_url)
        container_image_signature_url = f"{signature_server_url}/{container_image_signature_name}"
        try:
            stdout_result = StringIO()
            stdout_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stdout,
                stdout_result
            ])

            # -s: Silent
            # -S: Show error
            # -f: Don't print out failure document
            sh.curl(  # pylint: disable=no-member
                '-sSfv',
                '-X', 'PUT',
                '--user', f"{signature_server_username}:{signature_server_password}",
                '--data-binary', f"@{container_image_signature_file_path}",
                container_image_signature_url,
                _out=stdout_callback,
                _err=sys.stderr,
                _tee='err'
            )
        except sh.ErrorReturnCode as error:
            raise RuntimeError(
                f"Unexpected error curling signature file to signature server: {error}"
            ) from error

        return container_image_signature_url
