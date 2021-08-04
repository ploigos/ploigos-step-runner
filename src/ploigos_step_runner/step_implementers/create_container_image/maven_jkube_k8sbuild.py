"""`StepImplementer` for the `create-container-image` step using Maven JKube Plugin.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key             | Required? | Default | Description
------------------------------|-----------|---------|-----------
`pom-file`                    | Yes       | `'pom.xml'` | pom used when executing maven.
`tls-verify`                  | No        | `True`  | Disables TLS Verification if set to False
`maven-profiles`              | No        | `[]`    | List of maven profiles to use.
`maven-no-transfer-progress`  | No        | `True`  | `True` to suppress the transfer progress of packages maven downloads.
                                                     `False` to have the transfer progress printed.\
                                                    See https://maven.apache.org/ref/current/maven-embedder/cli.html
`maven-additional-arguments`  | No        | `['-Dmaven.test.skip=true', '-Dmaven.install.skip=true']` \
                                                    | List of additional arguments to use. \
                                                      Skipping tests by default because assuming \
                                                      a previous step already ran them. \
                                                      Skipping install backs assuming this is \
                                                      running in an ephermal environment where \
                                                      that would be a waist of time, and also \
                                                      that a previous step ran `package` \
                                                      and `push-artifacts` steps.
`maven-servers`               | No        |         | Dictionary of dictionaries of id, username, password
`maven-repositories`          | No        |         | Dictionary of dictionaries of id, url, snapshots, releases
`maven-mirrors`               | No        |         | Dictionary of dictionaries of id, url, mirror_of
`container-image-version`     | Yes       |         | Version to use when building the container image
`organization`                | Yes       |         | Used in built container image tag
`application_name`            | Yes       |         | Used in built container image tag
`service_name`                | Yes       |         | Used in built container image tag
`container-registries`        | No        |         | Hash of container registries to authenticate with.

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

from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.step_implementers.shared.maven_generic import \
    MavenGeneric
from ploigos_step_runner.utils.containers import \
    determine_container_image_build_tag_info

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

        # create local build tag
        image_registry_organization = self.get_value('organization')
        build_full_tag, build_short_tag, image_registry_uri, image_repository, image_version = \
            determine_container_image_build_tag_info(
                image_version=self.get_value('container-image-version'),
                organization=image_registry_organization,
                application_name=self.get_value('application-name'),
                service_name=self.get_value('service-name')
            )

        # push the artifacts
        mvn_jkube_output_file_path = self.write_working_file('mvn_k8s_build_output.txt')
        try:
            # execute maven step (params come from config)
            print("Build container image with Maven Jkube kubernetes plugin")
            self._run_maven_step(
                mvn_output_file_path=mvn_jkube_output_file_path,
                step_implementer_additional_arguments=[
                    f"-Djkube.generator.name={build_full_tag}"
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
            value=build_full_tag,
            description='Full container image tag of the built container,' \
                ' including the registry URI.'
        )
        step_result.add_artifact(
            name='container-image-short-tag',
            value=build_short_tag,
            description='Short container image tag of the built container image,' \
                ' excluding the registry URI.'
        )

        return step_result
