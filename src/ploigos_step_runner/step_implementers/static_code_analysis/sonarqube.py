"""`StepImplementer` for the `static-code-analysis` step using SonarQube.

Reference:  https://docs.sonarqube.org/latest/analysis/analysis-parameters

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Key               | Required | Default                     | Description
------------------|----------|-----------------------------|------------
`properties`      | Yes      | `./sonar-project.proerties` | Existing properties file for SonarQube
`url`             | Yes      |                             | SonarQube host url (sonar.host.url)
`username`        | No       |                             | SonarQube username id (sonar.login)
`password`        | No       |                             | SonarQube password
`version`         | Yes      |                             | Version to use for the SonarQube \
                                                             project version (sonar.projectVersion)
`java-truststore` | No       | `/etc/pki/java/cacerts`     | Location of Java TrustStore. Defaults \
                                                             to System.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key    | Description
-----------------------|------------
`sonarqube-result-set` | Path to the sonarqube results

Examples
--------

Example: Step Configuration (minimal)

    static-code-analysis:
    - implementer: SonarQube
      config:
        url: https://sonarqube.yourcompany.com/

Example: Generated Sonar Scanner Call (uses both step configuration and previous results)

    sonar-scanner
        -Dproject.settings=properties
        -Dsonar.host.url=url
        -Dsonar.projectVersion=generate-metadata.version
        -Dsonar.projectKey=application-name.service-name

Example: Existing Sonar Properties File (minimal)

    #----- Default SonarQube server
    # Config requires the url; this will NOT be used
    #   sonar.host.url=https://sonarqube-sonarqube.apps.ploigos_step_runner.rht-set.com/
    # Will override:
    #   sonar.projectKey
    #   sonar.projectVersion
    #   sonar.working.directory
    # Recommendation:
    #   Set qualitygate wait to true to stop the pipeline
    #   when the threshold of errors is reached.
    #   Regardless, see the SonarQube dashboard for details.
    sonar.qualitygate.wait=true

    # --- optional ---
    # Optional defaults to project key,
    sonar.projectName=Quarkus Reference App

    # --- optional ---
    # Encoding of the source code. Default is default system encoding
    sonar.sourceEncoding=UTF-8

    # --- java basic properties ---
    sonar.sources=src/main/java/
    sonar.java.libraries=target/*.jar
    sonar.java.binaries=target/classes/org/acme/rest/json
    sonar.java.test.binaries=target/test-classes/org/acme/rest/json

    # --- java reporting properties ---
    #sonar.coverage.jacoco.xmlReportPaths=target/site/jacoco
    #sonar.core.codeCoveragePlugin=jacoco

"""

import os
import sys

import sh
from ploigos_step_runner import StepImplementer
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_result import StepResult

DEFAULT_CONFIG = {
    'properties': './sonar-project.properties',
    'java-truststore': '/etc/pki/java/cacerts'
}

AUTHENTICATION_CONFIG = {
    'username': None,
    'password': None
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'url',
    'application-name',
    'service-name',
    'version'
]


class SonarQube(StepImplementer):
    """
    StepImplementer for the tag-source step for SonarQube.
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
        * either both username and password are set or neither.

        Raises
        ------
        StepRunnerException
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # ensure either both git-username and git-password are set or neither
        runtime_auth_config = {}
        for auth_config_key in AUTHENTICATION_CONFIG:
            runtime_auth_config_value = self.get_value(auth_config_key)

            if runtime_auth_config_value is not None:
                runtime_auth_config[auth_config_key] = runtime_auth_config_value

        if (any(element in runtime_auth_config for element in AUTHENTICATION_CONFIG)) and \
                (not all(element in runtime_auth_config for element in AUTHENTICATION_CONFIG)):
            raise StepRunnerException(
                "Either 'username' or 'password 'is not set. Neither or both must be set."
            )

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # Optional: username and password
        username = None
        password = None
        if self.has_config_value(AUTHENTICATION_CONFIG):
            if (self.get_value('username')
                    and self.get_value('password')):
                username = self.get_value('username')
                password = self.get_value('password')

        application_name = self.get_value('application-name')
        service_name = self.get_value('service-name')
        project_key = f'{application_name}:{service_name}'
        url = self.get_value('url')
        version = self.get_value('version')
        properties_file = self.get_value('properties')
        java_truststore = self.get_value('java-truststore')

        if not os.path.exists(properties_file):
            step_result.success = False
            step_result.message = f'Properties file not found: {properties_file}'
            return step_result

        try:
            # Hint:  Call sonar-scanner with sh.sonar_scanner
            #    https://amoffat.github.io/sh/sections/faq.html
            working_directory = self.work_dir_path
            if username:
                sh.sonar_scanner(  # pylint: disable=no-member
                    f'-Dproject.settings={properties_file}',
                    f'-Dsonar.host.url={url}',
                    f'-Dsonar.projectVersion={version}',
                    f'-Dsonar.projectKey={project_key}',
                    f'-Dsonar.login={username}',
                    f'-Dsonar.password={password}',
                    f'-Dsonar.working.directory={working_directory}',
                    _env={"SONAR_SCANNER_OPTS": f'-Djavax.net.ssl.trustStore={java_truststore}'},
                    _out=sys.stdout,
                    _err=sys.stderr
                )
            else:
                sh.sonar_scanner(  # pylint: disable=no-member
                    f'-Dproject.settings={properties_file}',
                    f'-Dsonar.host.url={url}',
                    f'-Dsonar.projectVersion={version}',
                    f'-Dsonar.projectKey={project_key}',
                    f'-Dsonar.working.directory={working_directory}',
                    _env={"SONAR_SCANNER_OPTS": f'-Djavax.net.ssl.trustStore={java_truststore}'},
                    _out=sys.stdout,
                    _err=sys.stderr
                )
        except sh.ErrorReturnCode_1 as error: # pylint: disable=no-member
            # Error Code 1: INTERNAL_ERROR
            # See error codes: https://github.com/SonarSource/sonar-scanner-cli/blob/master/src/main/java/org/sonarsource/scanner/cli/Exit.java # pylint: disable=line-too-long
            step_result.success = False
            step_result.message = "Error running static code analysis" \
                f" using sonar-scanner: {error}"
        except sh.ErrorReturnCode_2 as error: # pylint: disable=no-member
            # Error Code 2: USER_ERROR
            # See error codes: https://github.com/SonarSource/sonar-scanner-cli/blob/master/src/main/java/org/sonarsource/scanner/cli/Exit.java # pylint: disable=line-too-long
            step_result.success = False
            step_result.message = "Static code analysis failed." \
                " See 'sonarqube-result-set' result artifact for details."
        except sh.ErrorReturnCode as error: # pylint: disable=no-member
            # Error Code Other: unexpected
            # See error codes: https://github.com/SonarSource/sonar-scanner-cli/blob/master/src/main/java/org/sonarsource/scanner/cli/Exit.java # pylint: disable=line-too-long
            step_result.success = False
            step_result.message = "Unexpected error running static code analysis" \
                f" using sonar-scanner: {error}"

        step_result.add_artifact(
            name='sonarqube-result-set',
            value=f'{working_directory}/report-task.txt'
        )
        return step_result
