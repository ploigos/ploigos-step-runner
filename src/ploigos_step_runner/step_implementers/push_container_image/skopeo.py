"""`StepImplementer` for the `push-container-image` step using Skopeo.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key  | Required? | Default | Description
-------------------|-----------|---------|-----------
`container-image-version` \
                   | Yes       |         | Version to use when pushing the container image
`organization`     | Yes       |         | Used in creating the container image push tag
`application_name` | Yes       |         | Used in creating the container image push tag
`service_name`     | Yes       |         | Used in creating the container image push tag
`destination-url`  | Yes       |         | Container image repository destination to push image \
                                           to. <br/> \
                                           Should not include the repository type.
`[source-tls,verify, src-tls-verify]` \
                   | Yes       | `True`  | Whether to verify TLS when pulling source image.
`dest-tls-verify`  | Yes       | `True`  | Whether to verify TLS when pushing destination image.
`[container-image-pull-tag, container-image-tag]` \
                   | Yes       |         | Container image tag of image to push to \
                                           `destination-url`.
`[container-image-pull-repository-type, container-image-repository-type]` \
                   | Yes       | 'containers-storage:' \
                                         | Container repository type for the pull image source. \
                                           See https://github.com/containers/skopeo for valid \
                                           options.
`[container-image-push-repository-type, container-image-repository-type]` \
                   | Yes       | 'docker://' \
                                         | Container repository type for the push image source. \
                                           See https://github.com/containers/skopeo for valid \
                                           options.
`containers-config-auth-file` \
                   | No        |         | Path to the container registry authentication file \
                                           to use for container registry authentication. \
                                           If one is not provided one will be created in the \
                                           working directory.
`container-registries` \
                   | False     |         | Hash of container registries to authenticate with.


Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key            | Description
-------------------------------|------------
`container-image-registry-uri` | Registry URI poriton of the container image tag \
                                 of the pushed container image.
`container-image-registry-organization` \
                               | Organization portion of the container image tag \
                                 of the pushed container image.
`container-image-repository`   | Repository portion of the container image tag \
                                 of the pushed container image.
`container-image-name`         | Another way to reference the \
                                 repository portion of the container image tag \
                                 of the pushed container image.
`container-image-version`      | Version portion of the container image tag \
                                 of the pushed container image.
`container-image-tag`          | Full container image tag of the pushed container, \
                                 including the registry URI. <br/> \
                                 Takes the form of: \
                                    `container-image-registry-organization/container-image-repository:container-image-version`
`container-image-short-tag`    | Short container image tag of the pushed container image, \
                                 excluding the registry URI. <br/> \
                                 Takes the form of: \
                                    `container-image-registry-uri/container-image-registry-organization/container-image-repository:container-image-version`

""" # pylint: disable=line-too-long

import os
import sys
from distutils import util

import sh
from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.utils.containers import container_registries_login

DEFAULT_CONFIG = {
    'src-tls-verify': True,
    'dest-tls-verify': True,
    'container-image-pull-repository-type': 'containers-storage:',
    'container-image-push-repository-type': 'docker://'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'destination-url',
    ['source-tls,verify', 'src-tls-verify'],
    'dest-tls-verify',
    'service-name',
    'application-name',
    'organization',

    # being flexible for different use cases of proceeding steps
    ['container-image-pull-tag', 'container-image-tag'],
    ['container-image-pull-repository-type', 'container-image-repository-type'],
    ['container-image-push-repository-type', 'container-image-repository-type']
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

        # get config
        image_pull_tag = self.get_value(['container-image-pull-tag', 'container-image-tag'])
        pull_repository_type = self.get_value([
            'container-image-pull-repository-type',
            'container-image-repository-type'
        ])
        push_repository_type = self.get_value([
            'container-image-push-repository-type',
            'container-image-repository-type'
        ])
        dest_tls_verify = self.get_value('dest-tls-verify')
        if isinstance(dest_tls_verify, str):
            dest_tls_verify = bool(util.strtobool(dest_tls_verify))
        source_tls_verify = self.get_value(['source-tls-verify', 'src-tls-verify'])
        if isinstance(source_tls_verify, str):
            source_tls_verify = bool(util.strtobool(source_tls_verify))

        # create push tag
        image_version = self.get_value('container-image-version')
        if image_version is None:
            image_version = 'latest'
            print('No image tag version found in metadata. Using latest')
        image_version = image_version.lower()
        image_registry_uri = self.get_value('destination-url')
        image_registry_organization = self.get_value('organization')
        image_repository = f"{self.get_value('application-name')}-{self.get_value('service-name')}"
        image_push_short_tag = f"{image_registry_organization}/{image_repository}:{image_version}"
        image_push_tag = f"{image_registry_uri}/{image_push_short_tag}"

        try:
            # login to any provider container registries
            # NOTE: important to specify the auth file because depending on the context this is
            #       being run in python process may not have permissions to default location
            containers_config_auth_file = self.get_value('containers-config-auth-file')
            if not containers_config_auth_file:
                containers_config_auth_file = os.path.join(
                    self.work_dir_path,
                    'container-auth.json'
                )
            container_registries_login(
                registries=self.get_value('container-registries'),
                containers_config_auth_file=containers_config_auth_file,
                containers_config_tls_verify=dest_tls_verify
            )

            # push image
            sh.skopeo.copy( # pylint: disable=no-member
                f"--src-tls-verify={str(source_tls_verify).lower()}",
                f"--dest-tls-verify={str(dest_tls_verify).lower()}",
                f"--authfile={containers_config_auth_file}",
                f'{pull_repository_type}{image_pull_tag}',
                f'{push_repository_type}{image_push_tag}',
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )
        except sh.ErrorReturnCode as error:
            step_result.success = False
            step_result.message = f'Error pushing container image ({image_pull_tag}) ' \
                f' to tag ({image_push_tag}) using skopeo: {error}'

        # add artifacts
        step_result.add_artifact(
            name='container-image-registry-uri',
            value=image_registry_uri,
            description='Registry URI poriton of the container image tag' \
                ' of the pushed container image.'
        )
        step_result.add_artifact(
            name='container-image-registry-organization',
            value=image_registry_organization,
            description='Organization portion of the container image tag' \
                ' of the pushed container image.'
        )
        step_result.add_artifact(
            name='container-image-repository',
            value=image_repository,
            description='Repository portion of the container image tag' \
                ' of the pushed container image.'
        )
        step_result.add_artifact(
            name='container-image-name',
            value=image_repository,
            description='Another way to reference the' \
                ' repository portion of the container image tag of the pushed container image.'
        )
        step_result.add_artifact(
            name='container-image-version',
            value=image_version,
            description='Version portion of the container image tag of the pushed container image.'
        )
        step_result.add_artifact(
            name='container-image-tag',
            value=image_push_tag,
            description='Full container image tag of the pushed container,' \
                ' including the registry URI.'
        )
        step_result.add_artifact(
            name='container-image-short-tag',
            value=image_push_short_tag,
            description='Short container image tag of the pushed container image,' \
                ' excluding the registry URI.'
        )

        return step_result
