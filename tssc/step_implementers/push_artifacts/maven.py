"""Step Implementer for the push-artifacts step for Maven.
Step Configuration
------------------
Step configuration key(s) for this step:
| Key                 | Required | Default | Description
|---------------------|----------|---------|------------
| `maven-push-        | True     | N/A     | id for the maven servers and mirrors
| `artifact-repo-id`  |          |         |
| `maven-push-        | True     | N/A     | url for the maven servers and mirrors
| `artifact-repo-url` |          |         |
Expected Previous Step Results
------------------------------
Results expected from previous steps:
|  Key                | Description
|---------------------|------------
| `package-artifact`  | Artifacts is dictionary
|                     | Each element of an `artifact` will be used
|                     | as a parameter to deploy to repository:
|                     | * artifact.group-id
|                     | * artifact.artifact-id
|                     | * artifact.path
|                     | * artifact.package-type
Results
-------
Results output by this step:
| Key                | Description
|--------------------|------------
| `result`           | Dictionary of results
| `report-artifacts` | An array of dictionaries describing the push results
Elements in the `result` dictionary:
| `success`          | True or False
| `message`          | Overall status
Elements in the `report-artifacts` dictionary:
| Elements           | Description
|--------------------|------------
| `path`             | Absolute path to the artifact pushed to the artifact repository
| `artifact-id`      | Maven artifact ID pushed to the artifact repository
| `group-id`         | Maven group ID pushed to the artifact repository
| `package-type`     | Package type of the artifact
| `version`          | Version pushed to the artifact repository
Examples
--------
Example: Step Configuration (minimal)
    push-artifacts:
    - implementer: Maven
      config:
        maven-push-artifact-repo-id: internal-id-name
        maven-push-artifact-repo-url: url-to server
Example: Generated Maven Deploy (uses both step configuration and previous results)
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
REQUIRED_CONFIG_KEYS = [
    'maven-push-artifact-repo-url',
    'maven-push-artifact-repo-id'
]
REQUIRED_PREVIOUS_STEP_CONFIG_KEYS = [
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
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.
        See Also
        --------
        _validate_runtime_step_config
        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.
        """
        return REQUIRED_CONFIG_KEYS

    def _generate_maven_settings(self):
        # ----- build settings.xml
        maven_servers = ConfigValue.convert_leaves_to_values(
            self.get_config_value('maven-servers')
        )
        maven_repositories = ConfigValue.convert_leaves_to_values(
            self.get_config_value('maven-repositories')
        )
        maven_mirrors = ConfigValue.convert_leaves_to_values(
            self.get_config_value('maven-mirrors')
        )
        return generate_maven_settings(self.work_dir_path,
                                       maven_servers,
                                       maven_repositories,
                                       maven_mirrors)

    def _validate_previous_step_results(self):
        for key in REQUIRED_PREVIOUS_STEP_CONFIG_KEYS:
            value = self.get_result_value(key)
            if value is None:
                return f'previous step results missing {key}'
        return None

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        step_result
            Object with results of running this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # Validate previous step results values exist
        message = self._validate_previous_step_results()
        if message:
            step_result.success = False
            step_result.message = message
            return step_result

        # Get config items
        maven_push_artifact_repo_id = self.get_config_value('maven-push-artifact-repo-id')
        maven_push_artifact_repo_url = self.get_config_value('maven-push-artifact-repo-url')

        # Create settings.xml
        settings_file = self._generate_maven_settings()

        # Get previous step values
        push_artifacts = []
        version = self.get_result_value('version')
        package_artifacts = self.get_result_value('package-artifacts')
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
            })

        step_result.add_artifact(name='push-artifacts', value=push_artifacts)
        return step_result
