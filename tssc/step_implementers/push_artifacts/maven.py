"""Step Implementer for the push-artifacts step for Maven.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key   | Required | Default | Description
|---------------------|----------|---------|------------------------------------------
| `maven-push-`       | True     | N/A     | id for the maven servers and mirrors
| `artifact-repo-id`  |          |         |
| `maven-push-`       | True     | N/A     | url for the maven servers and mirrors
| `artifact-repo-url` |          |         |

Expected Previous Step Results
------------------------------
Results expected from previous steps that this step requires.

| Step Name           | Result Key          | Description
|---------------------|---------------------|-------------------------------------------
| package             | `package-artifact`  | Artifacts is dictionary
|                     |                     | Each element of an `artifact` will be used
|                     |                     | as a parameter to deploy to repository:
|                     |                     |  * artifact.group-id
|                     |                     |  * artifact.artifact-id
|                     |                     |  * artifact.path
|                     |                     |  * artifact.package-type

Results
-------
Results output by this step:

| Result Key          | Description
|---------------------|------------
| `push-artifacts`    | An array of dictionaries with information on the built artifacts.

| Results Key        | Description
|--------------------|------------
| `path`             | Absolute path to the artifact pushed to the artifact repository
| `artifact-id`      | Maven artifact ID pushed to the artifact repository
| `group-id`         | Maven group ID pushed to the artifact repository
| `version`          | Version pushed to the artifact repository
| `packaging`        | Type of package (eg: jar, war)

Examples
--------

**Example: Step Configuration (minimal)**

    push-artifacts:
    - implementer: Maven
      config:
        maven-push-artifact-repo-id: internal-id-name
        maven-push-artifact-repo-url: url-to server

**Example: Generated Maven Deploy (uses both step configuration and previous results)**

    mvn
      deploy:deploy-file'
      -Durl=maven-push-artifact-repo-url
      -Dversion=package.artifact.version
      -DgroupId=package.artifact.group-id
      -DartifactId=package.artifact.artifact-id
      -Dfile=package.artifact.path
      -Dpackaging=package.artifact.package-type
      -DrepositoryId=maven-push-artifact-repo-id
      -s settings.xml
"""
import sys

import sh
from tssc import StepImplementer
from tssc.config import ConfigValue
from tssc.step_result import StepResult
from tssc.utils.maven import generate_maven_settings

DEFAULT_CONFIG = {}
REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'maven-push-artifact-repo-url',
    'maven-push-artifact-repo-id',
    'version',
    'package-artifacts'
]

class Maven(StepImplementer):
    """
    StepImplementer for the push-artifacts step for Maven.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

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

    def _generate_maven_settings(self):
        # ----- build settings.xml
        maven_servers = ConfigValue.convert_leaves_to_values(
            self.get_value('maven-servers')
        )
        maven_repositories = ConfigValue.convert_leaves_to_values(
            self.get_value('maven-repositories')
        )
        maven_mirrors = ConfigValue.convert_leaves_to_values(
            self.get_value('maven-mirrors')
        )
        return generate_maven_settings(self.work_dir_path,
                                       maven_servers,
                                       maven_repositories,
                                       maven_mirrors)

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        step_result
            Object with results of running this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # Get config items
        maven_push_artifact_repo_id = self.get_value('maven-push-artifact-repo-id')
        maven_push_artifact_repo_url = self.get_value('maven-push-artifact-repo-url')

        # Create settings.xml
        settings_file = self._generate_maven_settings()

        # Get previous step values
        push_artifacts = []
        version = self.get_value('version')
        package_artifacts = self.get_value('package-artifacts')
        for package in package_artifacts:
            artifact_path = package['path']
            group_id = package['group-id']
            artifact_id = package['artifact-id']
            package_type = package['package-type']

            try:
                sh.mvn(  # pylint: disable=no-member
                    'deploy:deploy-file',
                    '-Dversion=' + version,
                    '-Dfile=' + artifact_path,
                    '-DgroupId=' + group_id,
                    '-DartifactId=' + artifact_id,
                    '-Dpackaging=' + package_type,
                    '-Durl=' + maven_push_artifact_repo_url,
                    '-DrepositoryId=' + maven_push_artifact_repo_id,
                    '-s' + settings_file,
                    _out=sys.stdout,
                    _err=sys.stderr,
                    _tee='err'
                )
            except sh.ErrorReturnCode as error:
                raise RuntimeError(f'Error invoking mvn: {error}') from error

            push_artifacts.append({
                'artifact-id': artifact_id,
                'group-id': group_id,
                'version': version,
                'path': artifact_path,
                'packaging': package_type,
            })

        step_result.add_artifact(name='push-artifacts', value=push_artifacts)
        return step_result
