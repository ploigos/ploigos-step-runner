"""`StepImplementer` for the `create-container-image step` using Buildah.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key             | Required? | Default           | Description
------------------------------|-----------|-------------------|-----------
`imagespecfile`               | Yes       | `'Containerfile'` | File defining the container image
`context`                     | Yes       | `'.'`             | Context to build the container image in
`tls-verify`                  | Yes       | `True`            | Whether to verify TLS when pulling parent images
`format`                      | Yes       | `'oci'`           | format of the built image's manifest and metadata
`containers-config-auth-file` | No        |                   | Path to the container registry authentication \
                                                                file to use for container registry authentication. \
                                                                If one is not provided one will be created in the \
                                                                working directory.
`[container-image-tag, \
  container-image-version]`   | Yes       |                   | Container image tag to use when building the container image.
`organization`                | Yes       |                   | Used in built container image tag
`application_name`            | Yes       |                   | Used in built container image tag
`service_name`                | No        |                   | Used in built container image tag
`container-registries`        | No        |                   | Hash of container registries to authenticate with.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                   | Description
--------------------------------------|------------
`container-image-registry`            | Container image registry of the built container image address.
`container-image-repository`          | Container image repository of the built container image address.
`container-image-tag`                 | Container image tag of the built container image address.
`container-image-build-digest`        | Container image digest of the built container image address.
`container-image-build-address`       | Container image address of the built container image.
`container-image-build-short-address` | Container image short address (no registry) of the built container image.
""" # pylint: disable=line-too-long

import os
import sys
from distutils import util

import sh
from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.utils.containers import (
    add_container_build_step_result_artifacts, container_registries_login,
    determine_container_image_address_info, get_container_image_digest)

DEFAULT_CONFIG = {
    # Image specification file name
    'imagespecfile': 'Containerfile',

    # Parent path to the image specification file
    'context': '.',

    # Verify TLS Certs?
    'tls-verify': True,

    # Format of the produced image
    'format': 'oci'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'imagespecfile',
    'context',
    'tls-verify',
    'format',
    'organization',
    'service-name',
    'application-name'
]

class Buildah(StepImplementer):
    """`StepImplementer` for the `create-container-image step` using Buildah.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

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

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * given 'imagespecfile' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # if pom-file has value verify file exists
        # If it doesn't have value and is required function will have already failed
        image_spec_file = self.get_value('imagespecfile')
        context = self.get_value('context')
        image_spec_file_full_path = os.path.join(context, image_spec_file)
        assert os.path.exists(image_spec_file_full_path), \
            f'Given imagespecfile ({image_spec_file}) does not exist in given context ({context}).'

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # get config
        image_spec_file = self.get_value('imagespecfile')
        tls_verify = self.get_value('tls-verify')
        if isinstance(tls_verify, str):
            tls_verify = bool(util.strtobool(tls_verify))

        # create local build tag
        container_image_build_address, container_image_build_short_address, \
        contaimer_image_registry, container_image_repository, container_image_tag = \
            determine_container_image_address_info(
                contaimer_image_registry='localhost',
                container_image_tag=self.get_value([
                    'container-image-tag',
                    'container-image-version'
                ]),
                organization=self.get_value('organization'),
                application_name=self.get_value('application-name'),
                service_name=self.get_value('service-name')
            )

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
                containers_config_tls_verify=tls_verify
            )

            # perform build
            sh.buildah.bud(  # pylint: disable=no-member
                '--format=' + self.get_value('format'),
                '--tls-verify=' + str(tls_verify).lower(),
                '--layers', '-f', image_spec_file,
                '-t', container_image_build_address,
                '--authfile', containers_config_auth_file,
                self.get_value('context'),
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )

        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            step_result.success = False
            step_result.message = 'Issue invoking buildah bud with given image ' \
                f'specification file ({image_spec_file}): {error}'

        # get image digest
        container_image_digest = None
        if step_result.success:
            try:
                print("Get container image digest")
                container_image_digest = get_container_image_digest(
                    container_image_address=container_image_build_address
                )
            except RuntimeError as error:
                step_result.success = False
                step_result.message = f"Error getting built container image digest: {error}"

        # add artifacts
        add_container_build_step_result_artifacts(
            step_result=step_result,
            contaimer_image_registry=contaimer_image_registry,
            container_image_repository=container_image_repository,
            container_image_tag=container_image_tag,
            container_image_digest=container_image_digest,
            container_image_build_address=container_image_build_address,
            container_image_build_short_address=container_image_build_short_address
        )

        return step_result
