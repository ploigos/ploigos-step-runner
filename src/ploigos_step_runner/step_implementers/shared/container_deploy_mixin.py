"""A mixin class designed to add shared functionality to
StepImplementers involved in the container deployment process.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key                      | Required? | Default  | Description
---------------------------------------|-----------|----------|-----------
`[container-image-pull-registry, \
  container-image-push-registry, \
  container-image-registry]`            | Maybe    |          | If `use-container-image-short-addres` is `True`, \
                                                                container image registry to pull container image from when deploying.

`[container-image-pull-repository, \
  container-image-push-repository, \
  container-image-repository]`          | Yes      |          | Container image repository within the given container image registry \
                                                                to pull container image from when deploying.
`[container-image-pull-digest,
  container-image-push-digest,
  container-image-digest]               | Maybe    |          | If `use-container-image-digest` is `True`,
                                                                container image digest to pull container image with when deploying.
`[container-image-pull-tag,
  container-image-push-tag,
  container-image-tag]                  | Maybe    |          | If `use-container-image-digest` is `False`,
                                                                container image tag to pull container image with when deploying.
`use-container-image-short-addres`      | No       | `False`  | If `True` then use container image short address (no registry).\
                                                                If `False` then use container image full address (including registry).
`use-container-image-digest`            | No       | `True`   | If `True` then use container image digest in container image address when \
                                                                pulling container image for deployment.<br/>\
                                                                If `False` then use container image tag in container image address when \
                                                                pulling container image for deployment.
"""# pylint: disable=line-too-long

from ploigos_step_runner.exceptions import StepRunnerException

DEFAULT_CONFIG = {
    'use-container-image-short-addres': False,
    'use-container-image-digest': True
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'use-container-image-short-addres',
    'use-container-image-digest',
    [
        'container-image-pull-repository',
        'container-image-push-repository',
        'container-image-repository'
    ]
]
class ContainerDeployMixin:
    """A mixin class designed to add shared functionality to
    StepImplementers involved in the container deployment process.
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

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * either both git-username and git-password are set or neither.

        Raises
        ------
        StepRunnerException
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # ensure container image registry is given if to be used in container image deploy address
        if not self.get_value('use-container-image-short-addres'):
            container_image_registry = self.get_value([
                'container-image-pull-registry',
                'container-image-registry',
                'container-image-push-registry',
            ])
            if container_image_registry is None:
                raise StepRunnerException(
                    "If using container image address with container image registry"
                    " (use-container-image-short-addres is False)"
                    " then container image registry ('container-image-pull-registry',"
                    " 'container-image-push-registry', 'container-image-registry') must be given."
                )

        # ensure container image tag or digest provided as needed
        if self.get_value('use-container-image-digest'):
            container_image_digest = self.get_value([
                'container-image-pull-digest',
                'container-image-push-digest',
                'container-image-digest',
            ])
            if container_image_digest is None:
                raise StepRunnerException(
                    "If deploying container image with container image digest"
                    " (use-container-image-digest is True)"
                    " in the container image address" \
                    " then container image digest ('container-image-pull-digest'," \
                    " 'container-image-push-digest', 'container-image-digest') must be given."
                )
        else:
            container_image_tag = self.get_value([
                'container-image-pull-tag',
                'container-image-push-tag',
                'container-image-tag',
            ])
            if container_image_tag is None:
                raise StepRunnerException(
                    "If deploying container image with container image tag"
                    " (use-container-image-digest is False)"
                    " in the container image address" \
                    " then container image digest ('container-image-pull-tag'," \
                    " 'container-image-push-tag', 'container-image-tag') must be given."
                )

    def _get_deploy_time_container_image_address(self):
        """Gets the container image address to use at deploy time.

        Returns
        -------
        str
            Container image address to use at deploy time
        """
        container_image_address = ""

        # include registry in address if not using short address
        use_container_image_short_address = self.get_value('use-container-image-short-address')
        if not use_container_image_short_address:
            container_image_registry = self.get_value([
            'container-image-pull-registry',
            'container-image-push-registry',
            'container-image-registry'
        ])
            container_image_address += f"{container_image_registry}/"

        # add repository to address
        container_image_repository = self.get_value([
            'container-image-pull-repository',
            'container-image-push-repository',
            'container-image-repository',
        ])
        container_image_address += container_image_repository

        # use either digest or tag
        use_container_image_digest = self.get_value('use-container-image-digest')
        if use_container_image_digest:
            container_image_digest = self.get_value([
                'container-image-pull-digest',
                'container-image-push-digest',
                'container-image-digest',
            ])
            container_image_address += f"@{container_image_digest}"
        else:
            container_image_tag = self.get_value([
                'container-image-pull-tag',
                'container-image-push-tag',
                'container-image-tag'
            ])
            container_image_address += f":{container_image_tag}"

        # return result
        return container_image_address
