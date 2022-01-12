"""`StepImplementer` for the `create-container-image` step using Maven JKube Plugin.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key            | Required? | Default     | Description
-----------------------------|-----------|-------------|-----------
`pom-file`                   | Yes       | `'pom.xml'` | pom used when executing maven.
`tls-verify`                 | No        | `True`      | Disables TLS Verification if set to False
`maven-profiles`             | No        | `[]`        | List of maven profiles to use.
`maven-no-transfer-progress` | No        | `True`      | `True` to suppress the transfer progress of packages maven downloads.
                                                         `False` to have the transfer progress printed.\
                                                         See https://maven.apache.org/ref/current/maven-embedder/cli.html
`maven-additional-arguments` | No        | `['-Dmaven.test.skip=true', '-Dmaven.install.skip=true']` \
                                                       | List of additional arguments to use. \
                                                         Skipping tests by default because assuming \
                                                         a previous step already ran them. \
                                                         Skipping install backs assuming this is \
                                                         running in an ephermal environment where \
                                                         that would be a waist of time, and also \
                                                         that a previous step ran `package` \
                                                         and `push-artifacts` steps.
`maven-servers`              | No        |             | Dictionary of dictionaries of id, username, password
`maven-repositories`         | No        |             | Dictionary of dictionaries of id, url, snapshots, releases
`maven-mirrors`              | No        |             | Dictionary of dictionaries of id, url, mirror_of
`[container-image-tag, \
  container-image-version]`  | Yes       |             | Container image tag to use when building the container image
`organization`               | Yes       |             | Used in built container image tag
`application_name`           | Yes       |             | Used in built container image tag
`service_name`               | No        |             | Used in built container image tag

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
"""# pylint: disable=line-too-long

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared.maven_generic import \
    MavenGeneric
from ploigos_step_runner.utils.containers import (
    add_container_build_step_result_artifacts,
    determine_container_image_address_info, get_container_image_digest)

DEFAULT_CONFIG = {
    'maven-additional-arguments': [
        '-Dmaven.install.skip=true',
        '-Dmaven.test.skip=true'
    ]
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'pom-file'
]

class MavenJKubeK8sBuild(MavenGeneric):
    """`StepImplementer` for the `create-container-image` step using Maven JKube Plugin.
    """
    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None
    ):
        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment,
            maven_phases_and_goals=['k8s:build']
        )

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
        return {**MavenGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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

        # create local build container image address
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

        # build the container image
        mvn_jkube_output_file_path = self.write_working_file('mvn_k8s_build_output.txt')
        try:
            # execute maven step (params come from config)
            print("Build container image with Maven Jkube kubernetes plugin")
            self._run_maven_step(
                mvn_output_file_path=mvn_jkube_output_file_path,
                step_implementer_additional_arguments=[
                    f"-Djkube.generator.name={container_image_build_address}"
                ]
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running 'maven k8s:build' to create container image. " \
                f"More details maybe found in 'maven-jkube-output' report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from running maven to " \
                    "create container image.",
                name='maven-jkube-output',
                value=mvn_jkube_output_file_path
            )

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
