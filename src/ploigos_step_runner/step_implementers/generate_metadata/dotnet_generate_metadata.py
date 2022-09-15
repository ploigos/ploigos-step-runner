"""`StepImplementer` for the `generate-metadata` step using Maven.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key                    | Required? | Default      | Description
-------------------------------------|-----------|--------------|-----------
`csproj-file`                        | Yes       |              | csproj file to read the app version out of
`csproj-version-tag`                 | No        | 'Version'    | XML tag to get version from csproj file

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                     | Description
----------------------------------------|------------
`app-version`                           | Value to use for `version` portion of semantic version \
                                          (https://semver.org/). Uses the version read out of the given pom file.
"""# pylint: disable=line-too-long

import os.path
import xml.etree.ElementTree as ET
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer

DEFAULT_CONFIG = {
    'csproj-version-tag': 'Version'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'csproj-file'
]


class DotnetGenerateMetadata(StepImplementer):
    """`StepImplementer` for the `generate-metadata` step using Dotnet.
    """

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

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """

        step_result = StepResult.from_step_implementer(self)

        # get the version
        csproj_file = self.get_value('csproj-file')
        csproj_version_tag = self.get_value('csproj-version-tag')

        if not os.path.exists(csproj_file):
            step_result.message += f'Given csproj file (csproj-file) does not exist: {csproj_file}'
            step_result.success = False
            return step_result

        project_version = self.__get_project_version(csproj_file, csproj_version_tag)

        if project_version is not None:
            step_result.add_artifact(
                name='app-version',
                value=project_version
            )
            step_result.success = True
        else:
            step_result.success = False
            step_result.message += 'Could not get project version from given csproj file:' \
                f' ({self.get_value("csproj-file")})'

        return step_result

    def __get_project_version(self, xml_file, xml_tag):
        """Get the project version from a csproj xml file
        """
        project_version = None

        csproj_file = self.get_value('csproj-file')
        assert os.path.exists(csproj_file), f'Given csproj file (csproj-file) does not exist: {csproj_file}'

        # Parse csproj file for a Version tag
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for child in root.iter():
            if child.tag == xml_tag:
                project_version = child.text
                break

        return project_version
