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

| `artifacts`Key | Description
|----------------|------------
| `path`         | Absolute path to the built artifact.
| `artifact-id`  | Maven artifact ID.
| `group-id`     | Maven group ID.
| `package-type` | Package type.
| `pom-path`     | Absolute path to the pom that built the artifact.

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
import os
import sh

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

from tssc.step_implementers.utils.xml import get_xml_element

DEFAULT_ARGS = {
    'pom-file': 'pom.xml',
    'artifact-extensions': ["jar", "war", "ear"],
    'artifact-parent-dir': 'target'
}

class Maven(StepImplementer):
    """
    StepImplementer for the package step for Maven. It is assumed thought that there will
    only be a single jar, ear, or war output for running mvn clean install against the given
    pom.xml file.

    Raises
    ------
    ValueError
        If given pom file does not exist
        If given pom file does not contain required elements
    """

    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.PACKAGE

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """
        if 'pom-file' not in step_config or not step_config['pom-file']:
            raise ValueError('Key (pom-file) must have none empty value in the step configuration')
            #raise ValueError('Key (pom-file) must have none empty value in the step configuration')

    def _run_step(self, runtime_step_config):
        pom_file = runtime_step_config['pom-file']
        artifact_extensions = runtime_step_config['artifact-extensions']
        artifact_parent_dir = runtime_step_config['artifact-parent-dir']

        if not os.path.exists(pom_file):
            raise ValueError('Given pom file does not exist: ' + pom_file)

        try:
            sh.mvn('clean', 'install', '-f', pom_file) # pylint: disable=no-member
        except sh.ErrorReturnCode as error:
            raise RuntimeError("Error invoking mvn: {0}".format(str(error)))

        # find the artifacts
        artfiact_file_names = []
        artifact_parent_dir_full_path = \
            os.listdir(os.path.join(
                os.path.dirname(os.path.abspath(pom_file)),
                artifact_parent_dir))
        for filename in artifact_parent_dir_full_path:
            if any(filename.endswith(ext) for ext in artifact_extensions):
                artfiact_file_names.append(filename)

        # error if we find more then one artifact
        # see https://projects.engineering.redhat.com/browse/NAPSSPO-546
        if len(artfiact_file_names) > 1:
            raise ValueError(
                'pom resulted in multiple artifacts with expected artifact extensions ' +
                '({artifact_extensions}), this is unsupported'.format(
                    artifact_extensions=artifact_extensions))

        if len(artfiact_file_names) < 1:
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
            'artifacts' : [{
                'path': os.path.join(
                    os.path.dirname(os.path.abspath(pom_file)),
                    artifact_parent_dir, artfiact_file_names[0]
                ),
                'artifact-id': artifact_id,
                'group-id': group_id,
                'package-type': package_type,
                'pom-path': pom_file
            }]
        }
        return results

# register step implementer
TSSCFactory.register_step_implementer(Maven)
