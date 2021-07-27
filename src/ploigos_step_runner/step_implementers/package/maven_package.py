"""`StepImplementer` for the `package` step using Maven.

Notes
-----

.. Important::

    If package not specified in pom will default to jar in result.

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
`maven-profiles`             | No        | `[]`    | List of maven profiles to use.
`maven-no-transfer-progress` | No        | `True`  | \
                            `True` to suppress the transfer progress of packages maven downloads.
                            `False` to have the transfer progress printed.\
                            See https://maven.apache.org/ref/current/maven-embedder/cli.html
`maven-additional-arguments` | No        | `['-Dmaven.test.skip=true']` \
                                                   | List of additional arguments to use. \
                                                     Skipping tests by default because assuming \
                                                     a previous step already ran them.
`maven-servers`              | No        |         | Dictionary of dictionaries of \
                                                     id, username, password
`maven-repositories`         | No        |         | Dictionary of dictionaries of \
                                                     id, url, snapshots, releases
`maven-mirrors`              | No        |         | Dictionary of dictionaries of \
                                                     id, url, mirror_of
`artifact-extensions`        | Yes       | `["jar", "war", "ear"]` \
                                            | Extensions to look for in the `artifact-parent-dir` \
                                              for built artifacts.
`artifact-parent-dir`        | Yes       | `'target'` \
                                            | Parent directory to look for built artifacts in \
                                              ending in `artifact-extensions`.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`maven-output`      | Path to Stdout and Stderr from invoking Maven.
`packages`          | An array of dictionaries with information on the built artifacts.


## package-artifacts
Keys in the dictionary elements in the `package-artifacts` array in the step results.

| Key             | Description
|-----------------|------------
| `path`          | Absolute path to the built artifact.

"""
import os

from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.step_implementers.shared.maven_generic import \
    MavenGeneric

DEFAULT_CONFIG = {
    'maven-additional-arguments': [
        '-Dmaven.test.skip=true'
    ],
    'artifact-extensions': ["jar", "war", "ear"],
    'artifact-parent-dir': 'target'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'pom-file'
]

class MavenPackage(MavenGeneric):
    """`StepImplementer` for the `package` step using Maven.
    """
    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None
    ):
        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment,
            maven_phases_and_goals=['package']
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

    def _run_step(self): # pylint: disable=too-many-locals
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        pom_file = self.get_value('pom-file')
        artifact_extensions = self.get_value('artifact-extensions')
        artifact_parent_dir = self.get_value('artifact-parent-dir')

        # package the artifacts
        mvn_output_file_path = self.write_working_file('mvn_output.txt')
        try:
            # execute maven step (params come from config)
            self._run_maven_step(
                mvn_output_file_path=mvn_output_file_path
            )

             # find the artifacts
            packages = []
            pom_file_dir_name = os.path.dirname(os.path.abspath(pom_file))
            artifact_parent_dir_full_path = \
                os.listdir(os.path.join(
                    pom_file_dir_name,
                    artifact_parent_dir))
            for filename in artifact_parent_dir_full_path:
                if any(filename.endswith(ext) for ext in artifact_extensions):
                    packages += [{
                        'path': os.path.join(
                            pom_file_dir_name,
                            artifact_parent_dir,
                            filename
                        )
                    }]

            step_result.add_artifact(
                name='packages',
                value=packages
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running 'maven package' to package artifacts. " \
                f"More details maybe found in 'maven-output' report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value=mvn_output_file_path
            )

        return step_result
