"""Step Implementer for the package step for Maven.

Notes
-----

.. WARNING::

    This can currently only handle POMs that generate a single artifact.
    See https://projects.engineering.redhat.com/browse/NAPSSPO-546 for RFE
    to handle multiple artifacts.

.. Important::

    If package not specified in pom will default to jar in result.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key     | Required? | Default                 | Description
|-----------------------|-----------|-------------------------|-----------
| `pom-file`            | True      | `'pom.xml'`             | Maven pom file to build
| `artifact-extensions` | True      | `["jar", "war", "ear"]` | Extensions to look for in the
                                                                `artifact-parent-dir` for built
                                                                artifacts.
| `artifact-parent-dir` | True      | `'target'`              | Parent directory to look for built
                                                                artifacts in ending in
                                                                `artifact-extensions`.

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

None.

Results
-------

Results output by this step.

| Result Key  | Description
|-------------|------------
| `artifacts` | An array of dictionaries with information on the built artifacts.


**artifacts**
Keys in the dictionary elements in the `artifacts` array in the step results.

| `artifacts` Key | Description
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

*Step Results after this Step Implementer*

    {'tssc-results': {
        'package': [
            {
                'path': '{FULL_PATH_TO_GENERATED_ARTIFACT}',
                'artifact-id': 'my-app',
                'group-id': 'com.mycompany.app'
                'package-type': 'jar',
                'pom-path': '{FULL_PATH_TO_POM}'
            }
        ]
    }}

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

*Step Results after this Step Implementer*

    {'tssc-results': {
        'package': [
            {
                'path': '{FULL_PATH_TO_GENERATED_ARTIFACT}',
                'artifact-id': 'my-app',
                'group-id': 'com.mycompany.app'
                'package-type': 'war',
                'pom-path': '{FULL_PATH_TO_POM}'
            }
        ]
    }}
"""
import sys
import os
import sh

from tssc import StepImplementer
from tssc.utils.xml import get_xml_element

from tssc.utils.maven import generate_maven_settings
from tssc.config import ConfigValue

DEFAULT_CONFIG = {
    'pom-file': 'pom.xml',
    'artifact-extensions': ["jar", "war", "ear"],
    'artifact-parent-dir': 'target'
}

REQUIRED_CONFIG_KEYS = [
    'pom-file'
]


class Maven(StepImplementer):
    """
    StepImplementer for the package step for Maven. It is assumed thought that there will
    only be a single jar, ear, or war output for running mvn clean install against the given
    pom.xml file.
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
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.

        See Also
        --------
        _validate_runtime_step_config

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.
        """
        return REQUIRED_CONFIG_KEYS

    def _generate_maven_settings(self):
        # ----- build settings.xml
        maven_servers = ConfigValue.convert_leaves_to_values(
            self.get_config_value('maven-servers')
        )
        maven_repositories = ConfigValue.convert_leaves_to_values(
            self.get_config_value('maven-repositories')
        )
        maven_mirrors = ConfigValue.convert_leaves_to_values(
            self.get_config_value('maven-mirrors')
        )
        return generate_maven_settings(self.get_working_dir(),
                                       maven_servers,
                                       maven_repositories,
                                       maven_mirrors)

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        dict
            Results of running this step.
        """
        pom_file = self.get_config_value('pom-file')
        artifact_extensions = self.get_config_value('artifact-extensions')
        artifact_parent_dir = self.get_config_value('artifact-parent-dir')

        if not os.path.exists(pom_file):
            raise ValueError('Given pom file does not exist: ' + pom_file)

        settings_file = self._generate_maven_settings()

        try:
            sh.mvn(  # pylint: disable=no-member,
                'clean',
                'install',
                '-f', pom_file,
                '-s', settings_file,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise RuntimeError(f'Error invoking mvn: {error}') from error

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
            raise ValueError(
                'pom resulted in multiple artifacts with expected artifact extensions ' +
                '({artifact_extensions}), this is unsupported'.format(
                    artifact_extensions=artifact_extensions))

        if len(artifact_file_names) < 1:
            raise ValueError(
                'pom resulted in 0 with expected artifact extensions ' +
                '({artifact_extensions}), this is unsupported'.format(
                    artifact_extensions=artifact_extensions))

        artifact_id = get_xml_element(pom_file, 'artifactId').text
        group_id = get_xml_element(pom_file, 'groupId').text
        try:
            package_type = get_xml_element(pom_file, 'package').text
        except ValueError:
            package_type = 'jar'

        results = {
            'artifacts': [{
                'path': os.path.join(
                    os.path.dirname(os.path.abspath(pom_file)),
                    artifact_parent_dir, artifact_file_names[0]
                ),
                'artifact-id': artifact_id,
                'group-id': group_id,
                'package-type': package_type,
                'pom-path': pom_file
            }]
        }
        return results
