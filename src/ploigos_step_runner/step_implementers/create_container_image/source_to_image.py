"""`StepImplementer` for the `create-container-image step` using Source-to-Image (s2i)
to create a Containerfile that can be built by another `StepImplementer`, such as Buildah.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key             | Required? | Default | Description
------------------------------|-----------|---------|-----------
`s2i-builder-image`           | True      |         | Container image tag to use as the s2i builder image.
`s2i-image-scripts-url`       | False     |         | Location of the s2i scripts in the given `s2i-builder-image`. \
                                                      If not given s2i will assume they are in `image:///usr/libexec/s2i`. \
                                                      <br/> \
                                                      EX:<br/> \
                                                      s2i-builder-image: registry.redhat.io/redhat-openjdk-18/openjdk18-openshift <br/> \
                                                      s2i-image-scripts-url: `image:///usr/local/s2i`
`s2i-loglevel`                | False     | 1       | s2i log level to specify. See s2i docs.
`s2i-additional-arguments`    | False     | `[]`    | List of additional arguments to append to s2i call.
`context`                     | True      | `'.'`   | Context to build the container image in
`tls-verify`                  | True      | `True`  | Whether to verify TLS when pulling parent images
`containers-config-auth-file` | False     |         | Path to the container registry authentication \
                                                      file to use for container registry authentication. \
                                                      If one is not provided one will be created in the \
                                                      working directory.
`container-registries`        | False     |         | Hash of container registries to authenticate with.


Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                     | Description
----------------------------------------|------------
`container-image-registry-uri`          | Registry URI poriton of the container image tag of the built container image.
`container-image-registry-organization` | Organization portion of the container image tag of the built container image.
`container-image-repository`            | Repository portion of the container image tag of the built container image.
`container-image-name`                  | Another way to reference the repository portion of the container image tag \
                                          of the built container image.
`container-image-version`               | Version portion of the container image tag of the built container image.
`container-image-tag`                   | Full container image tag of the built container, including the registry URI. <br/> \
                                          Takes the form of: \
                                          `container-image-registry-organization/container-image-repository:container-image-version`
`container-image-short-tag`             | Short container image tag of the built container image,  excluding the registry URI. <br/> \
                                          Takes the form of: \
                                          `container-image-registry-uri/container-image-registry-organization/container-image-repository:container-image-version`

"""# pylint: disable=line-too-long

import os
import sys
from distutils import util

import sh
from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.utils.containers import (container_registries_login,
                                                  inspect_container_image)

DEFAULT_CONFIG = {
    'context': '.',
    'tls-verify': True,
    's2i-additional-arguments': [],
    's2i-loglevel': 1
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'context',
    'tls-verify',
    's2i-builder-image',
    'organization',
    'service-name',
    'application-name'
]

class SourceToImage(StepImplementer):
    """`StepImplementer` for the `create-container-image step` using Source-to-Image (s2i)
    to create a Containerfile that can be built by another `StepImplementer`, such as Buildah.
    """

    CONTAINER_LABEL_SCRIPTS_URL = 'io.openshift.s2i.scripts-url'

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

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # get values
        builder_image = self.get_value('s2i-builder-image')

        # determine tls flag
        tls_verify = self.get_value('tls-verify')
        if isinstance(tls_verify, str):
            tls_verify = bool(util.strtobool(tls_verify))
        if tls_verify:
            s2i_tls_flags = ['--tlsverify']
        else:
            s2i_tls_flags = []

        # determine the generated imagespec file
        s2i_working_dir = self.create_working_dir_sub_dir('s2i-context')
        imagespecfile = self.write_working_file(
            os.path.join(s2i_working_dir, 'Containerfile.s2i-gen')
        )

        # determine image scripts url flags
        # use user provided url if given,
        # else try and inspect from builder image
        s2i_image_scripts_url = self.get_value('s2i-image-scripts-url')
        if not s2i_image_scripts_url:
            print('Attempt to inspect builder image for label for image scripts url')

            # attempt to auth with container image registries
            # login to any provider container registries
            # NOTE: important to specify the auth file because depending on the context this is
            #       being run in python process may not have permissions to default location
            containers_config_auth_file = self.get_value('containers-config-auth-file')
            if not containers_config_auth_file:
                containers_config_auth_file = os.path.join(
                    self.work_dir_path,
                    'container-auth.json'
                )
            try:
                container_registries_login(
                    registries=self.get_value('container-registries'),
                    containers_config_auth_file=containers_config_auth_file,
                    containers_config_tls_verify=tls_verify
                )
            except RuntimeError as error:
                step_result.message += "WARNING: error authenticating with" \
                    " container image registries to be able to pull s2i builder image" \
                    f" to inspect for image scripts url: {error}\n"

            # if not given, attempt to get from builder image labels
            try:
                container_image_details = inspect_container_image(
                    container_image_address=builder_image,
                    containers_config_auth_file=containers_config_auth_file
                )

                s2i_image_scripts_url = container_image_details['OCIv1']['config']['Labels']\
                    [SourceToImage.CONTAINER_LABEL_SCRIPTS_URL]
            except RuntimeError as error:
                step_result.message += "WARNING: failed to inspect s2i builder image" \
                    f" ({builder_image}) to dynamically determine image scripts url." \
                    f" S2I default will be used: {error}\n"
            except KeyError as error:
                step_result.message += "WARNING: failed to find s2i scripts url label" \
                    f" ({SourceToImage.CONTAINER_LABEL_SCRIPTS_URL}) on s2i builder image" \
                    f" ({builder_image}) to dynamically determine image scripts url." \
                    f" S2I default will be used: Could not find key ({error}).\n"

        # if determined image scripts url set the flag
        # else s2i will use its default (image:///usr/libexec/s2i)
        if s2i_image_scripts_url:
            s2i_image_scripts_url_flags = ['--image-scripts-url', s2i_image_scripts_url]
        else:
            s2i_image_scripts_url_flags = []

        try:
            # perform build
            print('Use s2i to generate imagespecfile and accompanying resources')
            sh.s2i.build(  # pylint: disable=no-member
                self.get_value('context'),
                builder_image,
                '--loglevel', self.get_value('s2i-loglevel'),
                *s2i_tls_flags,
                '--as-dockerfile', imagespecfile,
                *s2i_image_scripts_url_flags,
                *self.get_value('s2i-additional-arguments'),
                _out=sys.stdout,
                _err=sys.stderr,
                _tee='err'
            )
        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            step_result.success = False
            step_result.message += f'Issue invoking s2i build: {error}'

        # add artifacts
        step_result.add_artifact(
            name='imagespecfile',
            value=imagespecfile,
            description='File defining the container image to build generated by s2i'
        )
        step_result.add_artifact(
            name='context',
            value=s2i_working_dir,
            description='Context to use when building the imagespecfile generated by S2I.'
        )

        return step_result
