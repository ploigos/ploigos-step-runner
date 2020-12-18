"""Abstract parent class for StepImplementers that use Maven.
"""

import os

from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.maven import generate_maven_settings, write_effective_pom
from ploigos_step_runner.utils.xml import get_xml_element_by_path


class MavenGeneric(StepImplementer):
    """Abstract parent class for StepImplementers that use Maven.
    """

    SUREFIRE_PLUGIN_XML_ELEMENT_PATH = \
        'mvn:build/mvn:plugins/mvn:plugin/[mvn:artifactId="maven-surefire-plugin"]'
    SUREFIRE_PLUGIN_REPORTS_DIR_XML_ELEMENT_PATH = \
        f'{SUREFIRE_PLUGIN_XML_ELEMENT_PATH}/mvn:configuration/mvn:reportsDirectory'
    DEFAULT_SUREFIRE_PLUGIN_REPORTS_DIR = 'target/surefire-reports'

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

    def _generate_maven_settings(self):
        maven_servers = ConfigValue.convert_leaves_to_values(
            self.get_value('maven-servers')
        )
        maven_repositories = ConfigValue.convert_leaves_to_values(
            self.get_value('maven-repositories')
        )
        maven_mirrors = ConfigValue.convert_leaves_to_values(
            self.get_value('maven-mirrors')
        )

        return generate_maven_settings(
            working_dir=self.work_dir_path,
            maven_servers=maven_servers,
            maven_repositories=maven_repositories,
            maven_mirrors=maven_mirrors
        )

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
                output_path=effective_pom_path
            )

        return effective_pom_path

    def _get_effective_pom_element(self, element_path):
        return get_xml_element_by_path(
            self._get_effective_pom(),
            element_path,
            default_namespace='mvn'
        )
