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

| Step Name           |  Key               | Description
|---------------------|--------------------|------------
| `generate-metadata` | `version`          | The version to be used to deploy to the repository.
| `package`           | `artifacts`        | Artifacts is an array of `artifact`.
|                     |                    | Each element of an `artifact` will be used
|                     |                    | as a parameter to deploy to repository:
|                     |                    | * artifact.group-id
|                     |                    | * artifact.artifact-id
|                     |                    | * artifact.path
|                     |                    | * artifact.package-type

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
      -Dversion=generate-metadata.version
      -DgroupId=package.artifact.group-id
      -DartifactId=package.artifact.artifact-id
      -Dfile=package.artifact.path
      -Dpackaging=package.artifact.package-type
      -DrepositoryId=maven-push-artifact-repo-id
      -s settings.xml

Example: Results

    'tssc-results': {
        'result: {
            'success': True
            'message': 'push artifacts step completed - see report-artifacts',
        }
        'report-artifacts': [
             {
             'path':''
             'artifact-id': ''
             'group-id': ''
             'package-type': ''
             'version': ''
             }
        ]
    }

"""
import sys

import sh
from tssc import StepImplementer
from tssc.config import ConfigValue
from tssc.utils.maven import generate_maven_settings

DEFAULT_CONFIG = {}
REQUIRED_CONFIG_KEYS = [
    'maven-push-artifact-repo-url',
    'maven-push-artifact-repo-id'
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

    def _get_version(self):
        # Required: Get the generate-metadata.version
        if (self.get_step_results('generate-metadata') and
                self.get_step_results('generate-metadata').get('version')):
            return self.get_step_results('generate-metadata')['version']
        raise ValueError('generate-metadata results missing version')

    def _get_artifacts(self):
        # Required: Get the package.artifacts
        if (self.get_step_results('package') and
                self.get_step_results('package').get('artifacts')):
            return self.get_step_results('package')['artifacts']
        raise ValueError('package results missing artifacts')

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
        return generate_maven_settings(self.get_working_dir(),
                                       maven_servers,
                                       maven_repositories,
                                       maven_mirrors)

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        dict
            Results of running this step.
        """

        # ----- get generate-metadata items
        version = self._get_version()

        # ----- get package items
        artifacts = self._get_artifacts()

        maven_push_artifact_repo_id = self.get_config_value('maven-push-artifact-repo-id')
        maven_push_artifact_repo_url = self.get_config_value('maven-push-artifact-repo-url')
        settings_file = self._generate_maven_settings()

        report_artifacts = []

        for artifact in artifacts:
            artifact_path = artifact['path']
            group_id = artifact['group-id']
            artifact_id = artifact['artifact-id']
            package_type = artifact['package-type']

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

            report_artifacts.append({
                'artifact-id': artifact_id,
                'group-id': group_id,
                'version': version,
                'path': artifact_path,
            })
        results = {
            'result': {
                'success': True,
                'message': 'push artifacts step completed - see report-artifacts',
            },
            'report-artifacts': report_artifacts
        }
        return results
