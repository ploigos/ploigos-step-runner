"""`StepImplementer` for the `package` step using Maven.

Notes
-----

.. WARNING::

    This can currently only handle POMs that generate a single artifact.
    See https://github.com/ploigos/ploigos-step-runner/issues/99 for RFE
    to handle multiple artifacts.

.. Important::

    If package not specified in pom will default to jar in result.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key     | Required? | Default                 | Description
----------------------|-----------|-------------------------|-----------
`pom-file`            | True      | `'pom.xml'`             | Maven pom file to build
`artifact-extensions` | True      | `["jar", "war", "ear"]` | Extensions to look for in the \
                                                              `artifact-parent-dir` for built \
                                                               artifacts.
`artifact-parent-dir` | True      | `'target'`              | Parent directory to look for built \
                                                              artifacts in ending in \
                                                              `artifact-extensions`.
`tls-verify`          | No        | True                    | Disables TLS Verification if set to \
                                                              False

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`package-artifacts` | An array of dictionaries with information on the built artifacts.


## package-artifacts
Keys in the dictionary elements in the `package-artifacts` array in the step results.

| Key             | Description
|-----------------|------------
| `path`          | Absolute path to the built artifact.
| `artifact-id`   | Maven artifact ID.
| `group-id`      | Maven group ID.
| `package-type`  | Package type.
| `pom-path`      | Absolute path to the pom that built the artifact.

Examples
--------

**Example 1**

*Given POM*

    <project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>1.0-SNAPSHOT</version>
        <properties>
            <maven.compiler.source>1.8</maven.compiler.source>
            <maven.compiler.target>1.8</maven.compiler.target>
        </properties>
    </project>

**Example 2**

*Given POM*

    <project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>1.0-SNAPSHOT</version>
        <package>war</package>
        <properties>
            <maven.compiler.source>1.8</maven.compiler.source>
            <maven.compiler.target>1.8</maven.compiler.target>
        </properties>
    </project>

"""
import os
import sys

import sh
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.shared.maven_generic import MavenGeneric
from ploigos_step_runner.utils.io import create_sh_redirect_to_multiple_streams_fn_callback
from ploigos_step_runner.utils.xml import get_xml_element

DEFAULT_CONFIG = {
    'tls-verify': True,
    'pom-file': 'pom.xml',
    'artifact-extensions': ["jar", "war", "ear"],
    'artifact-parent-dir': 'target'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'pom-file'
]


class Maven(MavenGeneric):
    """`StepImplementer` for the `package` step using Maven.
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

    def _run_step(self): # pylint: disable=too-many-locals
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        tls_verify = self.get_value('tls-verify')
        pom_file = self.get_value('pom-file')
        artifact_extensions = self.get_value('artifact-extensions')
        artifact_parent_dir = self.get_value('artifact-parent-dir')

        if not os.path.exists(pom_file):
            step_result.success = False
            step_result.message = f'Given pom file does not exist: {pom_file}'
            return step_result

        mvn_additional_options = []
        if not tls_verify:
            mvn_additional_options += [
                '-Dmaven.wagon.http.ssl.insecure=true',
                '-Dmaven.wagon.http.ssl.allowall=true',
                '-Dmaven.wagon.http.ssl.ignore.validity.dates=true',
            ]

        settings_file = self._generate_maven_settings()
        mvn_output_file_path = self.write_working_file('mvn_test_output.txt')
        try:
            with open(mvn_output_file_path, 'w') as mvn_output_file:
                out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stdout,
                    mvn_output_file
                ])
                err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stderr,
                    mvn_output_file
                ])

                sh.mvn(  # pylint: disable=no-member
                    'clean',
                    'install',
                    '-f', pom_file,
                    '-s', settings_file,
                    *mvn_additional_options,
                    _out=out_callback,
                    _err=err_callback
                )
        except sh.ErrorReturnCode as error:
            step_result.success = False
            step_result.message = "Package failures. See 'maven-output' report artifacts " \
                f"for details: {error}"
            return step_result
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from 'mvn install'.",
                name='maven-output',
                value=mvn_output_file_path
            )

        # find the artifacts
        artifact_file_names = []
        artifact_parent_dir_full_path = \
            os.listdir(os.path.join(
                os.path.dirname(os.path.abspath(pom_file)),
                artifact_parent_dir))
        for filename in artifact_parent_dir_full_path:
            if any(filename.endswith(ext) for ext in artifact_extensions):
                artifact_file_names.append(filename)

        # error if we find more then one artifact
        # see https://projects.engineering.redhat.com/browse/NAPSSPO-546
        if len(artifact_file_names) > 1:
            step_result.success = False
            step_result.message = 'pom resulted in multiple artifacts with expected artifact ' \
                                  f'extensions ({artifact_extensions}), this is unsupported'
            return step_result

        if len(artifact_file_names) < 1:
            step_result.success = False
            step_result.message = 'pom resulted in 0 with expected artifact extensions ' \
                                  f'({artifact_extensions}), this is unsupported'
            return step_result

        artifact_id = get_xml_element(pom_file, 'artifactId').text
        group_id = get_xml_element(pom_file, 'groupId').text
        try:
            package_type = get_xml_element(pom_file, 'package').text
        except ValueError:
            package_type = 'jar'

        package_artifacts = {
            'path': os.path.join(
                    os.path.dirname(os.path.abspath(pom_file)),
                    artifact_parent_dir,
                    artifact_file_names[0]
            ),
            'artifact-id': artifact_id,
            'group-id': group_id,
            'package-type': package_type,
            'pom-path': pom_file
        }

        # Currently, package returns ONE 'artifact', eg: one war file
        # However, in the future, an ARRAY could be returned, eg: several jar files
        step_result.add_artifact(
           name='package-artifacts',
           value=[package_artifacts]
        )

        return step_result
