"""Step Implementer for the create-container-image step for Skopeo.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default  | Description
|-------------------|-----------|----------|-----------
| `destination-url` | True      |          | Container image repository destination to push image
|                   |           |          | to. o not include the `docker://` prefix as it will
|                   |           |          | automatically be applied
| `src-tls-verify`  | True      | `'true'` | Whether to very TLS for source of image
| `dest-tls-verify` | True      | `'true'` | Whether to verify TLS for destination of image
| `containers-config-auth-file` | True | `'~/.skopeo-auth.json'` | \
|   Path to the container registry authentication file \
|   to use for container registry authentication.

Expected Previous Step Results
------------------------------
Results expected from previous steps that this step requires.

| Step Name                | Result Key       | Description
|--------------------------|------------------|------------
| `generate-metadata`      | `container-image-version`      | Tag to push image with
| `create-container-image` | `image-tar-file` | Local tar file of image to push

Results
-------

Results output by this step.

| Result Key                | Description
|---------------------------|------------
| `container-image-version` |
| `container-image-uri`     |
| `container-image-tag`     |
"""
import os
from pathlib import Path
import sys
import sh
from tssc import StepImplementer, DefaultSteps
from tssc.utils.containers import container_registries_login
from tssc.step_result import StepResult

DEFAULT_CONFIG = {
    'src-tls-verify': 'true',
    'dest-tls-verify': 'true',
    'containers-config-auth-file': os.path.join(Path.home(), '.skopeo-auth.json')
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'containers-config-auth-file',
    'destination-url',
    'src-tls-verify',
    'dest-tls-verify',
    'service-name',
    'application-name',
    'organization',
    'container-image-version',
    'image-tar-file'
]

class Skopeo(StepImplementer):
    """
    StepImplementer for the push-container-image step for Skopeo.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

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
        """Runs the TSSC step implemented by this StepImplementer.
        Returns
        -------
        dict
            Results of running this step.
        """
        step_result = StepResult.from_step_implementer(self)

        image_version = self.get_value('container-image-version').lower()
        application_name = self.get_value('application-name')
        service_name = self.get_value('service-name')
        organization = self.get_value('organization')
        image_tar_file = self.get_value('image-tar-file')
        destination_url = self.get_value('destination-url')
        image_repository_uri = f"{destination_url}/{organization}/{application_name}-{service_name}"
        image_tag = f"{image_repository_uri}:{image_version}"

        try:
            # login to any provider container registries
            # NOTE: important to specify the auth file because depending on the context this is
            #       being run in python process may not have permissions to default location
            containers_config_auth_file = self.get_value('containers-config-auth-file')
            container_registries_login(
                registries=self.get_value('container-registries'),
                containers_config_auth_file=containers_config_auth_file
            )

            # push image
            sh.skopeo.copy( # pylint: disable=no-member
                f"--src-tls-verify={str(self.get_value('src-tls-verify'))}",
                f"--dest-tls-verify={str(self.get_value('dest-tls-verify'))}",
                f"--authfile={containers_config_auth_file}",
                f'docker-archive:{image_tar_file}',
                f'docker://{image_tag}',
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )
        except sh.ErrorReturnCode as error:
            step_result.success = False
            step_result.message = f'Error pushing container image ({image_tar_file}) ' + \
                f' to tag ({image_tag}) using skopeo: {error}'

        step_result.add_artifact(name='container-image-version', value=image_version)
        step_result.add_artifact(name='container-image-uri', value=image_repository_uri)
        step_result.add_artifact(name='container-image-tag', value=image_tag)

        return step_result
