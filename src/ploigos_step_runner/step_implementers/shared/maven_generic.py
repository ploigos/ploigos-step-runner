"""Abstract parent class for StepImplementers that use Maven.

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
`maven-phases-and-goals`     | Yes       |         | List of maven phases and/or goals to execute.
`maven-profiles`             | No        | `[]`    | List of maven profiles to use.
`maven-no-transfer-progress` | No        | `True`  | \
                            `True` to suppress the transfer progress of packages maven downloads.
                            `False` to have the transfer progress printed.\
                            See https://maven.apache.org/ref/current/maven-embedder/cli.html
`maven-additional-arguments` | No        | `[]`    | List of additional arguments to use.
`maven-servers`              | No        |         | Dictionary of dictionaries of id, username, password
`maven-repositories`         | No        |         | Dictionary of dictionaries of id, url, snapshots, releases
`maven-mirrors`              | No        |         | Dictionary of dictionaries of id, url, mirror_of
"""# pylint: disable=line-too-long

import os

from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.maven import (generate_maven_settings,
                                            run_maven, write_effective_pom)
from ploigos_step_runner.utils.xml import get_xml_element_by_path

DEFAULT_CONFIG = {
    'pom-file': 'pom.xml',
    'tls-verify': True,
    'maven-profiles': [],
    'maven-additional-arguments': [],
    'maven-no-transfer-progress': True
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'pom-file',
    'maven-phases-and-goals'
]

class MavenGeneric(StepImplementer):
    """Abstract parent class for StepImplementers that use Maven.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None,
        maven_phases_and_goals=None
    ):
        self.__maven_settings_file = None
        self.__maven_phases_and_goals = maven_phases_and_goals

        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment
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
        * given 'pom-file' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # if pom-file has value verify file exists
        # If it doesn't have value and is required function will have already failed
        pom_file = self.get_value('pom-file')
        if pom_file is not None:
            assert os.path.exists(pom_file), \
                f'Given maven pom file (pom-file) does not exist: {pom_file}'

    @property
    def maven_phases_and_goals(self):
        """Property for getting the maven phases and goals to execute which can either come
        from field set on this class via constructor, intended for use by sub classes that want
        to hard code the phases and goals for convenience, or comes from config value
        `maven-phases-and-goals` set by the user.

        Returns
        -------
        str
            Maven phases and/or goals to execute.
        """
        maven_phases_and_goals = None
        if self.__maven_phases_and_goals:
            maven_phases_and_goals = self.__maven_phases_and_goals
        else:
            maven_phases_and_goals = self.get_value('maven-phases-and-goals')

        return maven_phases_and_goals

    @property
    def maven_settings_file(self):
        """Gets the maven settings file for this step.
        """

        if not self.__maven_settings_file:
            maven_servers = ConfigValue.convert_leaves_to_values(
                self.get_value('maven-servers')
            )
            maven_repositories = ConfigValue.convert_leaves_to_values(
                self.get_value('maven-repositories')
            )
            maven_mirrors = ConfigValue.convert_leaves_to_values(
                self.get_value('maven-mirrors')
            )

            self.__maven_settings_file = generate_maven_settings(
                working_dir=self.work_dir_path,
                maven_servers=maven_servers,
                maven_repositories=maven_repositories,
                maven_mirrors=maven_mirrors
            )

        return self.__maven_settings_file

    def _get_effective_pom(self):
        """Writes the effective pom to a file and returns the path.

        Returns
        -------
        str
            Path to the written effective pom generated from the 'pom-file' value.
        """
        effective_pom_path = os.path.join(self.work_dir_path, 'effective-pom.xml')

        if not os.path.exists(effective_pom_path):
            write_effective_pom(
                pom_file_path=self.get_value('pom-file'),
                output_path=effective_pom_path,
                profiles=self.get_value('maven-profiles')
            )

        return effective_pom_path

    def _get_effective_pom_element(self, element_path):
        """Get an XML element from the effective pom.

        Parameters
        ----------
        element_path : str
            XML path of element to to get from effective pom.

        Returns
        -------
        str
            Value of the element from the effective pom.
        """
        return get_xml_element_by_path(
            self._get_effective_pom(),
            element_path,
            default_namespace='mvn'
        )

    def _run_maven_step(
        self,
        mvn_output_file_path,
        step_implementer_additional_arguments=None
    ):
        """Runs maven using the configuration given to this step runner.

        Parameters
        ----------
        mvn_output_file_path : str
            Path to file containing the maven stdout and stderr output.
        step_implementer_additional_arguments : []
            Additional arguments hard coded by the step implementer.

        Raises
        ------
        StepRunnerException
            If maven returns a none 0 exit code.
        """

        phases_and_goals = self.maven_phases_and_goals
        pom_file = self.get_value('pom-file')
        tls_verify = self.get_value('tls-verify')
        profiles = self.get_value('maven-profiles')
        no_transfer_progress = self.get_value('maven-no-transfer-progress')

        additional_arguments = []
        if step_implementer_additional_arguments:
            additional_arguments = \
                step_implementer_additional_arguments + self.get_value('maven-additional-arguments')
        else:
            additional_arguments = self.get_value('maven-additional-arguments')

        run_maven(
            mvn_output_file_path=mvn_output_file_path,
            phases_and_goals=phases_and_goals,
            additional_arguments=additional_arguments,
            pom_file=pom_file,
            tls_verify=tls_verify,
            profiles=profiles,
            no_transfer_progress=no_transfer_progress,
            settings_file=self.maven_settings_file
        )

    def _run_step(self): # pylint: disable=too-many-locals
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # package the artifacts
        mvn_output_file_path = self.write_working_file('mvn_output.txt')
        try:
            # execute maven step (params come from config)
            self._run_maven_step(
                mvn_output_file_path=mvn_output_file_path
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running maven. " \
                f"More details maybe found in 'maven-output' report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value=mvn_output_file_path
            )

        return step_result
