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

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared import MavenGeneric
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils import xml

DEFAULT_CONFIG = {
    'csproj-file': 'dotnet-app.csproj',
    'auto-increment-version-segment': None,
    'auto-increment-all-module-versions': True,
    'tls-verify': True
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
        return {**MavenGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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

        auto_increment_version_segment = self.get_value('auto-increment-version-segment')
        if auto_increment_version_segment:
            assert (auto_increment_version_segment in ('major', 'minor', 'patch')), \
                f'Given auto increment version segment (auto-increment-version-segment)' \
                f' must be one of [major, minor, patch]: {auto_increment_version_segment}'

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        try:
            step_result = StepResult.from_step_implementer(self)

            # auto increment the version
            auto_increment_version_segment = self.get_value('auto-increment-version-segment')
            if auto_increment_version_segment:
                print("Update dotnet package version")
                self.__auto_increment_version(auto_increment_version_segment, step_result)


            # get the version
            project_version = self.__get_project_version(step_result)
            if project_version:
                step_result.add_artifact(
                    name='app-version',
                    value=project_version
                )
            else:
                step_result.success = False
                step_result.message += 'Could not get project version from given pom file' \
                    f' ({self.get_value("pom-file")})'
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = str(error)

        return step_result

    def __get_project_version(self, step_result):
        """Get the project version

        Parameters
        ---------
        step_result : StepResult
            Step result to add step results to.
        """
        project_version = None
        dotnet_evaluate_project_version_file_path = self.write_working_file(
            'dotnet_evaluate_project_version.txt'
        )
        try:
            project_version = xml.get_xml_element(self.get_value('csproj-file'), 'Version')

        except StepRunnerException as error:
            step_result.success = False
            step_result.message = f"Error retrieving project version from csproj file: {error}"

        return project_version

    def __auto_increment_version(self, auto_increment_version_segment, step_result):
        """Automatically increments a given version segment.

        Parameters
        ---------
        auto_increment_version_segment : str
            The version segment to auto increment.
            One of: major, minor, or patch
        step_result : StepResult
            Step result to add step results to.
        """
        dotnet_auto_increment_version_output_file_path = self.write_working_file(
            'dotnet_versions_set_output.txt'
        )
        try:
            # SEE: https://www.mojohaus.org/build-helper-maven-plugin/parse-version-mojo.html
            new_version = None
            if auto_increment_version_segment == 'major':
                new_version = r'${parsedVersion.nextMajorVersion}.0.0'
            elif auto_increment_version_segment == 'minor':
                new_version = r'${parsedVersion.majorVersion}.${parsedVersion.nextMinorVersion}.0'
            elif auto_increment_version_segment == 'patch':
                new_version = r'${parsedVersion.majorVersion}' \
                    r'.${parsedVersion.minorVersion}' \
                    r'.${parsedVersion.nextIncrementalVersion}'

            additional_arguments = [
                f'-DnewVersion={new_version}'
            ]

            # determine if should auto increment all modules
            auto_increment_all_module_versions = self.get_value(
                'auto-increment-all-module-versions'
            )
            if auto_increment_all_module_versions:
                additional_arguments.append('-DprocessAllModules')

            #Add code to update csproj file
            #
            #

        except StepRunnerException as error:
            raise StepRunnerException(f"Error running maven to auto increment version segment"
                f" ({auto_increment_version_segment})."
                f" More details maybe found in 'maven-auto-increment-version-output'"
                f" report artifact: {error}") from error
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from running maven" \
                    " to auto increment version.",
                name='maven-auto-increment-version-output',
                value=dotnet_auto_increment_version_output_file_path
            )
