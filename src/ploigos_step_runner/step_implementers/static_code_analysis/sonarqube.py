"""`StepImplementer` for the `static-code-analysis` step using SonarQube.

Reference:  https://docs.sonarqube.org/latest/analysis/analysis-parameters

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Key                      | Required | Default                     | Description
-------------------------|----------|-----------------------------|------------
`properties`             | Yes      | `./sonar-project.proerties` | Existing properties file for SonarQube
`url`                    | Yes      |                             | SonarQube host url (sonar.host.url)
`username`               | No       |                             | SonarQube username id (sonar.login)
`password`               | No       |                             | SonarQube password
`token`                  | No       |                             | SonarQube token
`version`                | Yes      |                             | Version to use for the SonarQube \
                                                                    project version (sonar.projectVersion)
`java-truststore`        | No       | `/etc/pki/java/cacerts`     | Location of Java TrustStore. Defaults \
                                                             to System.
`project-key`            | No       |                             | SonarQube project key
`sonar-analyze-branches` | No       | `False`                     | `True` to pass the `sonar.branch.name` property to SonarQube, \
                                                                    which can only be done if using SonarQube Developer Edition or above as per \
                                                                    https://redirect.sonarsource.com/doc/branches.html. \
                                                                    `False to not pass the `sonar.branch.name` property to SonarQube. \
                                                                    Note, even if `False`, SonarQube will still be called even if on a branch, \
                                                                    that branch name just wont be passed to SonarQube so all of the results will \
                                                                    show up on the same `master` branch in the SonarQube UI.
`branch`                 | Maybe    |                             | Value to use for `sonar.branch.name` property if `sonar-analyze-branches` is `True`. \
                                                                    See https://sonarqube.corp.redhat.com/documentation/branches/overview/.
`release-branch-regexes` | No       | `['^main$', '^master$']`    | SonarQube does not want the `sonar.branch.name` flag passed for the \
                                                                    "main", "master", "release" branch. Therefor the StepImplementer needs to know \
                                                                    which branch(s) are considered the "main" branch so we don't pass the flag \
                                                                    for that branch. \
                                                                    See https://community.sonarsource.com/t/how-to-change-the-main-branch-in-sonarqube/13669/8

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
        -Dsonar.branch.name=feature/foo42

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

"""# pylint: disable=line-too-long

import os
import re
import sys

import sh
from ploigos_step_runner import StepImplementer, StepResult
from ploigos_step_runner.exceptions import StepRunnerException

DEFAULT_CONFIG = {
    'properties': './sonar-project.properties',
    'java-truststore': '/etc/pki/java/cacerts',
    'sonar-analyze-branches': False,
    'release-branch-regexes': ['^main$', '^master$']
}

AUTHENTICATION_CONFIG = {
    'username': None,
    'password': None,
    'token': None
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
        * either username and password are set but not token, token is set but not username
        and password, or none are set.
        Raises
        ------
        StepRunnerException
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # if token ensure no username and password
        if self.get_value('token'):
            if (self.get_value('username')
                    or self.get_value('password')):
                raise StepRunnerException(
                    "Either 'username' or 'password 'is set. Neither can be set with a token."
                )
        # if no token present, ensure either both git-username and git-password are set or neither
        else:
            if (self.get_value('username') and self.get_value('password') is None
                        or self.get_value('username') is None and self.get_value('password')):
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

        username = None
        password = None
        token = None

        if self.has_config_value(AUTHENTICATION_CONFIG, True):
            # Optional: token
            if self.get_value('token'):
                token = self.get_value('token')
            # Optional: username and password
            else:
                if (self.get_value('username')
                        and self.get_value('password')):
                    username = self.get_value('username')
                    password = self.get_value('password')

        application_name = self.get_value('application-name')
        service_name = self.get_value('service-name')
        properties_file = self.get_value('properties')

        # Optional: project-key
        if self.get_value('project-key'):
            project_key = self.get_value('project-key')
        # Default
        else:
            project_key = f'{application_name}:{service_name}'

        if not os.path.exists(properties_file):
            step_result.success = False
            step_result.message = f'Properties file not found: {properties_file}'
            return step_result

        sonarqube_success = False
        try:
            # Hint:  Call sonar-scanner with sh.sonar_scanner
            #    https://amoffat.github.io/sh/sections/faq.html
            working_directory = self.work_dir_path

            sonar_optional_flags = []
            # determine auth flags
            if token:
                sonar_optional_flags += [
                    f'-Dsonar.login={token}'
                ]
            elif username:
                sonar_optional_flags += [
                    f'-Dsonar.login={username}',
                    f'-Dsonar.password={password}',
                ]

            # determine branch flag
            # only provide sonar.branch.name flag if not the "main"/"master"/"release branch" and
            # sonar-analyze-branches is true (since can only due with certain versions of SonarQube)
            # see: https://community.sonarsource.com/t/how-to-change-the-main-branch-in-sonarqube/13669/8
            if self.get_value('sonar-analyze-branches') and not self.__is_release_branch():
                sonar_optional_flags += [
                    f"-Dsonar.branch.name={self.get_value('branch')}",
                ]

            # run scan
            sh.sonar_scanner(  # pylint: disable=no-member
                f'-Dproject.settings={properties_file}',
                f"-Dsonar.host.url={self.get_value('url')}",
                f"-Dsonar.projectVersion={self.get_value('version')}",
                f'-Dsonar.projectKey={project_key}',
                f'-Dsonar.working.directory={working_directory}',
                *sonar_optional_flags,
                _env={
                    "SONAR_SCANNER_OPTS": \
                        f"-Djavax.net.ssl.trustStore={self.get_value('java-truststore')}"
                },
                _out=sys.stdout,
                _err=sys.stderr
            )
            sonarqube_success = True
        except sh.ErrorReturnCode_1 as error: # pylint: disable=no-member
            # Error Code 1: INTERNAL_ERROR
            # See error codes: https://github.com/SonarSource/sonar-scanner-cli/blob/master/src/main/java/org/sonarsource/scanner/cli/Exit.java # pylint: disable=line-too-long
            step_result.success = False
            step_result.message = "Error running static code analysis" \
                f" using sonar-scanner: {error}"
        except sh.ErrorReturnCode_2: # pylint: disable=no-member
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

        step_result.add_evidence(
            name='sonarqube-quality-gate-pass',
            value=sonarqube_success
        )

        return step_result

    def __is_release_branch(self):
        """Determins if current branch is a release branch or not.

        Returns
        -------
        bool
            True if current branch is a release branch.
            False if not.
        """
        branch = self.get_value('branch')
        release_branch_regexes = self.get_value('release-branch-regexes')

        is_release_branch = False
        if release_branch_regexes:
            is_release_branch = False
            if not isinstance(release_branch_regexes, list):
                release_branch_regexes = [release_branch_regexes]
            for release_branch_regex in release_branch_regexes:
                if re.match(release_branch_regex, branch):
                    is_release_branch = True
                    break

        return is_release_branch
