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
`csproj-file`                        | Yes       | `'dotnet-app.csproj'` | csproj file to read the app version out of
`auto-increment-version-segment`     | No        |              | Segment of the app version to auto increment. \
                                                                  One of major, minor, or patch. \
                                                                  If None / empty string will not auto increment version.
`auto-increment-all-module-versions` | No        | True         | If auto incrementing version, auto increment version in all sub modules if True.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                     | Description
----------------------------------------|------------
`app-version`                           | Value to use for `version` portion of semantic version \
                                          (https://semver.org/). Uses the version read out of the given pom file.

`dotnet-auto-increment-version-output` | Standard out and standard error from running maven to auto increment version.
"""# pylint: disable=line-too-long

import os.path
import xml.etree.ElementTree as ET
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer




DEFAULT_CONFIG = {
    'csproj-file': 'dotnet-app.csproj'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'csproj-file'
]


class Dotnet(StepImplementer):
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

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * given 'csproj-file' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        csproj_file = self.get_value('csproj-file')
        assert os.path.exists(csproj_file), f'Given csproj file (csproj-file) does not exist: {csproj_file}'

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """

        step_result = StepResult.from_step_implementer(self)

        # get the version
        project_version = self.__get_project_version()

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

    def __get_project_version(self):
        """Get the project version from a csproj xml file
        """
        project_version = None

        csproj_file = self.get_value('csproj-file')

        # Parse csproj file for a Version tag
        tree = ET.parse(csproj_file)
        root = tree.getroot()
        for child in root.iter():
            if child.tag == 'Version':
                project_version = child.text
                break

        return project_version
