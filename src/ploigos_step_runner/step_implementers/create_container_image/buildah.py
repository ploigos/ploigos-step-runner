"""`StepImplementer` for the `create-container-image step` using Buildah.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key  | Required? | Default | Description
-------------------|-----------|---------|-----------
`imagespecfile`    | True      | `'Containerfile'` \
                                         | File defining the container image
`context`          | True      | `'.'`   | Context to build the container image in
`tls-verify`       | True      | `True`  | Whether to verify TLS when pulling parent images
`format`           | True      | `'oci'` | format of the built image's manifest and metadata
`containers-config-auth-file` \
                   | False     |         | Path to the container registry authentication \
                                           file to use for container registry authentication. \
                                           If one is not provided one will be created in the \
                                           working directory.
`container-image-version` \
                   | True      |         | Version to use when building the container image
`organization`     | True      |         | Used in built container image tag
`application_name` | True      |         | Used in built container image tag
`service_name`     | True      |         | Used in built container image tag
`container-registries` \
                   | False     |         | Hash of container registries to authenticate with.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key            | Description
-------------------------------|------------
`container-image-registry-uri` | Registry URI poriton of the container image tag \
                                 of the built container image.
`container-image-registry-organization` \
                               | Organization portion of the container image tag \
                                 of the built container image.
`container-image-repository`   | Repository portion of the container image tag \
                                 of the built container image.
`container-image-name`         | Another way to reference the \
                                 repository portion of the container image tag \
                                 of the built container image.
`container-image-version`      | Version portion of the container image tag \
                                 of the built container image.
`container-image-tag`          | Full container image tag of the built container, \
                                 including the registry URI. <br/> \
                                 Takes the form of: \
                                    `container-image-registry-organization/container-image-repository:container-image-version`
`container-image-short-tag`    | Short container image tag of the built container image, \
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
        image_version = self.get_value('container-image-version')
        if image_version is None:
            image_version = 'latest'
            print('No image tag version found in metadata. Using latest')
        image_registry_uri = 'localhost'
        image_registry_organization = self.get_value('organization')
        image_repository = f"{self.get_value('application-name')}-{self.get_value('service-name')}"
        short_tag = f"{image_registry_organization}/{image_repository}:{image_version}"
        build_tag = f"{image_registry_uri}/{short_tag}"

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
                '-t', build_tag,
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
            return step_result

        # add artifacts
        step_result.add_artifact(
            name='container-image-registry-uri',
            value=image_registry_uri,
            description='Registry URI poriton of the container image tag' \
                ' of the built container image.'
        )
        step_result.add_artifact(
            name='container-image-registry-organization',
            value=image_registry_organization,
            description='Organization portion of the container image tag' \
                ' of the built container image.'
        )
        step_result.add_artifact(
            name='container-image-repository',
            value=image_repository,
            description='Repository portion of the container image tag' \
                ' of the built container image.'
        )
        step_result.add_artifact(
            name='container-image-name',
            value=image_repository,
            description='Another way to reference the' \
                ' repository portion of the container image tag of the built container image.'
        )
        step_result.add_artifact(
            name='container-image-version',
            value=image_version,
            description='Version portion of the container image tag of the built container image.'
        )
        step_result.add_artifact(
            name='container-image-tag',
            value=build_tag,
            description='Full container image tag of the built container,' \
                ' including the registry URI.'
        )
        step_result.add_artifact(
            name='container-image-short-tag',
            value=short_tag,
            description='Short container image tag of the built container image,' \
                ' excluding the registry URI.'
        )

        return step_result
