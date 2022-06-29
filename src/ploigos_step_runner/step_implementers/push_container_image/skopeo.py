"""`StepImplementer` for the `push-container-image` step using Skopeo.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key                      | Required? | Default               | Description
---------------------------------------|-----------|-----------------------|-----------
`[container-image-pull-registry-type, \
  container-image-registry-type]`      | Yes       | 'containers-storage:' | Container repository type for the pull image source. \
                                                                             See https://github.com/containers/skopeo for valid options.
`[container-image-pull-address, \
  container-image-build-address],      | Yes       |                       | Address of image to push to the push destination.
`[source-tls,verify, src-tls-verify]`  | Yes       | `True`                | Whether to verify TLS when pulling source image.
`[container-image-push-registry-type, \
  container-image-registry-type]`      | Yes       | 'docker://'           | Container repository type for the push image source. \
                                                                             See https://github.com/containers/skopeo for valid options.
`[container-image-push-registry, \
  destination-url]`                    | Yes       |                       | Container image repository destination to push image to. <br/> \
                                                                             Should not include the repository type.
`[container-image-push-repository, \
  container-image-repository]`         | Yes       |                       | Container image repository to push the container image to.
`[container-image-push-tag, \
  container-image-tag, \
  container-image-version]`            | Yes       |                       | Container image tag to push the container image with.
`dest-tls-verify`                      | Yes       | `True`                | Whether to verify TLS when pushing destination image.
`containers-config-auth-file`          | No        |                       | Path to the container registry authentication file \
                                                                             to use for container registry authentication. \
                                                                             If one is not provided one will be created in the \
                                                                             working directory using `container-registries`.
`container-registries`                 | False     |         |             | Hash of container registries to authenticate with.


Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                       | Description
------------------------------------------|------------
`container-image-push-registry`           | Container image registry image was pushed to.
`container-image-push-repository`         | Container image repository image was pushed to.
`container-image-push-tag`                | Container image tag image was pushed to.
`container-image-push-digest`             | Container image digest of pushed container image.
`container-image-address-by-tag`          | Pushed container image address by tag.
`container-image-short-address-by-tag`    | Pushed container image short address (no registry) by tag.
`container-image-address-by-digest`       | Pushed container image address by digest.
`container-image-short-address-by-digest` | Pushed container image short address (no registry) by digest.
""" # pylint: disable=line-too-long

import os
import sys
from distutils import util

import sh
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.utils.containers import (container_registries_login,
                                                  get_container_image_digest)

DEFAULT_CONFIG = {
    'src-tls-verify': True,
    'dest-tls-verify': True,
    'container-image-pull-registry-type': 'containers-storage:',
    'container-image-push-registry-type': 'docker://',
    'container-image-push-tag': 'latest'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    ['container-image-pull-registry-type', 'container-image-registry-type'],
    ['container-image-pull-address', 'container-image-build-address'],
    ['source-tls,verify', 'src-tls-verify'],

    ['container-image-push-registry-type', 'container-image-registry-type'],
    ['container-image-push-registry', 'destination-url'],
    ['container-image-push-repository', 'container-image-repository'],
    ['container-image-push-tag', 'container-image-tag', 'container-image-version'],
    'dest-tls-verify'
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

    def _run_step(self): # pylint: disable=too-many-locals
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # get src image config
        pull_registry_type = self.get_value([
            'container-image-pull-registry-type',
            'container-image-registry-type'
        ])
        container_image_pull_address = self.get_value([
            'container-image-pull-address',
            'container-image-build-address'
        ])
        source_tls_verify = self.get_value(['source-tls-verify', 'src-tls-verify'])
        if isinstance(source_tls_verify, str):
            source_tls_verify = bool(util.strtobool(source_tls_verify))

        # create destination config
        push_registry_type = self.get_value([
            'container-image-push-registry-type',
            'container-image-registry-type'
        ])
        container_image_push_registry = self.get_value([
            'container-image-push-registry',
            'destination-url'
        ])
        container_image_push_repository = self.get_value([
            'container-image-push-repository',
            'container-image-repository'
        ])
        container_image_push_tag = self.get_value([
            'container-image-push-tag',
            'container-image-tag',
            'container-image-version'
        ])
        dest_tls_verify = self.get_value('dest-tls-verify')
        if isinstance(dest_tls_verify, str):
            dest_tls_verify = bool(util.strtobool(dest_tls_verify))
        container_image_push_short_address = \
            f"{container_image_push_repository}:{container_image_push_tag}"
        container_image_push_address_by_tag = f"{container_image_push_registry}" \
           f"/{container_image_push_short_address}"

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
                f'{pull_registry_type}{container_image_pull_address}',
                f'{push_registry_type}{container_image_push_address_by_tag}',
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )
        except sh.ErrorReturnCode as error:
            step_result.success = False
            step_result.message = f'Error pushing container image ({container_image_pull_address}) ' \
                f' to tag ({container_image_push_address_by_tag}) using skopeo: {error}'

        # add address part artifacts
        step_result.add_artifact(
            name='container-image-push-registry',
            value=container_image_push_registry,
            description='Container image registry container image was pushed to.'
        )
        step_result.add_artifact(
            name='container-image-push-repository',
            value=container_image_push_repository,
            description='Container image repository container image was pushed to.'
        )
        step_result.add_artifact(
            name='container-image-push-tag',
            value=container_image_push_tag,
            description='Container image tag container image was pushed to.'
        )

        # add address by tag artifacts
        step_result.add_artifact(
            name='container-image-address-by-tag',
            value=container_image_push_address_by_tag,
            description='Pushed container image address by tag.'
        )
        step_result.add_artifact(
            name='container-image-short-address-by-tag',
            value=container_image_push_short_address,
            description='Pushed container image short address (no registry) by tag.'
        )

        # add address by digest artifacts
        if step_result.success:
            try:
                print("Get pushed container image digest")
                container_image_digest = get_container_image_digest(
                    tls_verify=self.get_value('dest-tls-verify'),
                    container_image_address=container_image_push_address_by_tag,
                    containers_config_auth_file=containers_config_auth_file
                )

                container_image_short_address_by_digest = \
                    f"{container_image_push_repository}@{container_image_digest}"
                container_image_address_by_digest = \
                    f"{container_image_push_registry}/{container_image_short_address_by_digest}"

                step_result.add_artifact(
                    name='container-image-push-digest',
                    value=container_image_digest,
                    description='Container image digest container image was pushed to.'
                )
                step_result.add_artifact(
                    name='container-image-address-by-digest',
                    value=container_image_address_by_digest,
                    description='Pushed container image address by digest.'
                )
                step_result.add_artifact(
                    name='container-image-short-address-by-digest',
                    value=container_image_short_address_by_digest,
                    description='Pushed container image short address (no registry) by digest.'
                )
            except RuntimeError as error:
                step_result.success = False
                step_result.message = f"Error getting pushed container image digest: {error}"

        return step_result
