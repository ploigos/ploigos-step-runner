"""`StepImplementer` for the `package` step using Maven.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key            | Required? | Default | Description
-----------------------------|-----------|---------|-----------
`pom-file`                   | Yes       | `'pom.xml'` | pom used when executing maven.
`tls-verify`                 | No        | `True`  | Disables TLS Verification if set to False
`maven-profiles`             | No        | `[]`    | List of maven profiles to use.
`maven-no-transfer-progress` | No        | `True`  | \
                            `True` to suppress the transfer progress of packages maven downloads.
                            `False` to have the transfer progress printed.\
                            See https://maven.apache.org/ref/current/maven-embedder/cli.html
`maven-additional-arguments` | No        | `['-Dmaven.test.skip=true', \
                                             '-Dmaven.install.skip=true']` \
                                                   | List of additional arguments to use. \
                                                     Skipping tests by default because assuming \
                                                     a previous step already ran them. \
                                                     Skipping install backs assuming this is \
                                                     running in an ephermal environment where \
                                                     that would be a waist of time, and also \
                                                     that a previous step ran `package` \
                                                     and `push-artifacts` steps.
`maven-servers`              | No        |         | Dictionary of dictionaries of \
                                                     id, username, password
`maven-repositories`         | No        |         | Dictionary of dictionaries of \
                                                     id, url, snapshots, releases
`maven-mirrors`              | No        |         | Dictionary of dictionaries of \
                                                     id, url, mirror_of
`version`                      | Yes     |         | version to push
`maven-push-artifact-repo-url` | yes     |         | id for the maven servers and mirrors
`maven-push-artifact-repo-id`  | Yes     |         | url for the maven servers and mirrors

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`push-artifacts`    | An array of dictionaries with information on the pushed artifacts
"""

from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.step_implementers.shared.maven_generic import \
    MavenGeneric
from ploigos_step_runner.utils.maven import run_maven

DEFAULT_CONFIG = {
    'maven-additional-arguments': [
        '-Dmaven.install.skip=true',
        '-Dmaven.test.skip=true'
    ]
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'pom-file',
    'maven-push-artifact-repo-url',
    'maven-push-artifact-repo-id',
    'version'
]

class MavenDeploy(MavenGeneric):
    """`StepImplementer` for the `push-artifacts` step using Maven.
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
            maven_phases_and_goals=['deploy']
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

        # Get config items
        maven_push_artifact_repo_id = self.get_value('maven-push-artifact-repo-id')
        maven_push_artifact_repo_url = self.get_value('maven-push-artifact-repo-url')
        version = self.get_value('version')

        # push the artifacts
        mvn_update_version_output_file_path = self.write_working_file('mvn_versions_set_output.txt')
        mvn_push_artifacts_output_file_path = self.write_working_file('mvn_deploy_output.txt')
        try:
            # update the version before pushing
            # NOTE 1: we know this is weird. But the version in the pom isn't necessarily
            #         the version that was calculated as part of the release and so we need
            #         to update that before doing the maven deploy so the maven deploy will
            #         use the new version.
            #
            # NOTE 2: we tried doing this in the same command as the deploy,
            #         but the pom was already loaded so even though the xml was updated
            #         the deploy still used the old version, hence having to run this
            #         first and independently.
            print("Update maven package version")
            run_maven(
                mvn_output_file_path=mvn_update_version_output_file_path,
                settings_file=self.maven_settings_file,
                pom_file=self.get_value('pom-file'),
                phases_and_goals=['versions:set'],
                additional_arguments=[
                    f'-DnewVersion={version}'
                ]
            )

            # execute maven step (params come from config)
            print("Push packaged maven artifacts")
            self._run_maven_step(
                mvn_output_file_path=mvn_push_artifacts_output_file_path,
                step_implementer_additional_arguments=[
                    '-DaltDeploymentRepository=' \
                    f'{maven_push_artifact_repo_id}::default::{maven_push_artifact_repo_url}'
                ]
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running 'maven deploy' to push artifacts. " \
                f"More details maybe found in 'maven-output' report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from running maven to update version.",
                name='maven-update-version-output',
                value=mvn_update_version_output_file_path
            )
            step_result.add_artifact(
                description="Standard out and standard error from running maven to " \
                    "push artifacts to repository.",
                name='maven-push-artifacts-output',
                value=mvn_push_artifacts_output_file_path
            )

        return step_result
