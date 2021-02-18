"""`StepImplementer` for the `package` step using Maven.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key              | Required | Default | Description
-------------------------------|----------|---------|------------------------------------------
`maven-push-artifact-repo-url` | yes      |         | id for the maven servers and mirrors
`maven-push-artifact-repo-id`  | Yes      |         | url for the maven servers and mirrors
`version`                      | Yes      |         | version to push
`package-artifacts`            | Yes      |         | Artifacts is dictionary \
                                                      Each element of an `artifact` will be used \
                                                      as a parameter to deploy to repository: <br/>\
                                                        * artifact.group-id <br/>\
                                                        * artifact.artifact-id <br/>\
                                                        * artifact.path <br/>\
                                                        * artifact.package-type
`tls-verify`                   | No       | True    | Disables TLS Verification if set to False

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`push-artifacts`    | An array of dictionaries with information on the built artifacts.

## push-artifacts
Keys in the dictionary elements in the `push-artifacts` array in the step results.

| Key             | Description
|-----------------|------------
| `path`          | Absolute path to the artifact pushed to the artifact repository
| `artifact-id`   | Maven artifact ID pushed to the artifact repository
| `group-id`      | Maven group ID pushed to the artifact repository
| `version`       | Version pushed to the artifact repository
| `packaging`     | Type of package (eg: jar, war)

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
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.shared.maven_generic import MavenGeneric
from ploigos_step_runner.utils.io import create_sh_redirect_to_multiple_streams_fn_callback

DEFAULT_CONFIG = {
    'tls-verify': True
}
REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'maven-push-artifact-repo-url',
    'maven-push-artifact-repo-id',
    'version',
    'package-artifacts'
]

class Maven(MavenGeneric):
    """`StepImplementer` for the `package` step using Maven.
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
        package_artifacts = self.get_value('package-artifacts')
        tls_verify = self.get_value('tls-verify')

        # disable tls verification
        mvn_additional_options = []
        if not tls_verify:
            mvn_additional_options += [
                '-Dmaven.wagon.http.ssl.insecure=true',
                '-Dmaven.wagon.http.ssl.allowall=true',
                '-Dmaven.wagon.http.ssl.ignore.validity.dates=true',
            ]

        # Create settings.xml
        settings_file = self._generate_maven_settings()

        # push the artifacts
        push_artifacts = []
        mvn_output_file_path = self.write_working_file('mvn_test_output.txt')
        try:
            for package in package_artifacts:
                artifact_path = package['path']
                group_id = package['group-id']
                artifact_id = package['artifact-id']
                package_type = package['package-type']

                # push the artifact
                with open(mvn_output_file_path, 'a') as mvn_output_file:
                    out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                        sys.stdout,
                        mvn_output_file
                    ])
                    err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                        sys.stderr,
                        mvn_output_file
                    ])
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
                        *mvn_additional_options,
                        _out=out_callback,
                        _err=err_callback
                    )

                # record the pushed artifact
                push_artifacts.append({
                    'artifact-id': artifact_id,
                    'group-id': group_id,
                    'version': version,
                    'path': artifact_path,
                    'packaging': package_type,
                })
        except sh.ErrorReturnCode as error:
            step_result.success = False
            step_result.message = "Push artifacts failures. See 'maven-output' report artifacts " \
                f"for details: {error}"

        step_result.add_artifact(
            description="Standard out and standard error from 'mvn install'.",
            name='maven-output',
            value=mvn_output_file_path
        )
        step_result.add_artifact(
            name='push-artifacts',
            value=push_artifacts
        )
        return step_result
