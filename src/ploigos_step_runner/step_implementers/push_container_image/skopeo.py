"""`StepImplementer` for the `push-container-image` step using Skopeo.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key | Required? | Default  | Description
------------------|-----------|----------|-----------
`destination-url` | Yes       |          | Container image repository destination to push image \
                                           to. o not include the `docker://` prefix as it will \
                                           automatically be applied
`src-tls-verify`  | Yes       | `'true'` | Whether to very TLS for source of image
`dest-tls-verify` | Yes       | `'true'` | Whether to verify TLS for destination of image
`containers-config-auth-file` | Yes | `'~/.skopeo-auth.json'` | \
                                           Path to the container registry authentication file \
                                           to use for container registry authentication.
`container-image-version`     | Yes |    | Tag to push container image with
`image-tar-file`  | Yes       |          | Local tar file of container image to push

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                     | Description
----------------------------------------|------------
`container-image-registry-uri`          | URI to the image registry service.
`container-image-registry-organization` | Organization in the image registry to push the image to.
`container-image-repository`            | Repository in the Organization in the image registry to \
                                          push the image to.
`container-image-name`                  | Name of the image to push to the Image Repository. \
                                          This is the same value as `container-image-repository` as\
                                          these are always the same, but people refer to them \
                                          differently in different cases, so providing both.
`container-image-version`               | Version of the image to push.
`container-image-tag`                   | Tag container image was pushed with. <br/>\
                                          Takes the form of: \
                                            "`container-image-registry-uri`\
                                                /`container-image-registry-organization`\
                                                /`container-image-repository`\
                                                :`container-image-version`"
"""
import os
import sys
from distutils import util
from pathlib import Path

import sh
from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.utils.containers import container_registries_login

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
    """`StepImplementer` for the `push-container-image` step using Skopeo.
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

        image_version = self.get_value('container-image-version').lower()
        application_name = self.get_value('application-name')
        service_name = self.get_value('service-name')
        organization = self.get_value('organization')
        image_tar_file = self.get_value('image-tar-file')
        destination_url = self.get_value('destination-url')
        dest_tls_verify = self.get_value('dest-tls-verify')

        image_registry_uri = destination_url
        image_registry_organization = organization
        image_repository = f"{application_name}-{service_name}"
        image_tag = f"{image_registry_uri}/{image_registry_organization}" \
                    f"/{image_repository}:{image_version}"

        try:
            # login to any provider container registries
            # NOTE: important to specify the auth file because depending on the context this is
            #       being run in python process may not have permissions to default location
            containers_config_auth_file = self.get_value('containers-config-auth-file')
            container_registries_login(
                registries=self.get_value('container-registries'),
                containers_config_auth_file=containers_config_auth_file,
                containers_config_tls_verify=util.strtobool(dest_tls_verify)
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
            step_result.message = f'Error pushing container image ({image_tar_file}) ' \
                f' to tag ({image_tag}) using skopeo: {error}'

        step_result.add_artifact(name='container-image-registry-uri', value=image_registry_uri)
        step_result.add_artifact(
            name='container-image-registry-organization',
            value=image_registry_organization
        )
        step_result.add_artifact(name='container-image-repository', value=image_repository)
        step_result.add_artifact(name='container-image-name', value=image_repository)
        step_result.add_artifact(name='container-image-version', value=image_version)
        step_result.add_artifact(name='container-image-tag', value=image_tag)

        return step_result
