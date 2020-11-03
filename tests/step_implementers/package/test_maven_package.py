import os
import re
from io import IOBase, StringIO
from unittest.mock import MagicMock, patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tssc.config.config import Config
from tssc.step_implementers.package import Maven
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult
from tests.helpers.test_utils import Any
from pathlib import Path


class TestStepImplementerMavenPackageBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Maven,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

# TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = Maven.step_implementer_config_defaults()
        expected_defaults = {
            'pom-file': 'pom.xml',
            'artifact-extensions': ["jar", "war", "ear"],
            'artifact-parent-dir': 'target'
        }
        self.assertEqual(defaults, expected_defaults)

    def test_required_runtime_step_config_keys(self):
        required_keys = Maven.required_runtime_step_config_keys()
        expected_required_keys = [
            'pom-file'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def create_mvn_side_effect(pom_file, artifact_parent_dir, artifact_names):
        """simulates what mvn does by touching files.
        Notes
        -----
        Supports
        - mvn clean
        - mvn install
        """
        target_dir_path = os.path.join(
            os.path.dirname(os.path.abspath(pom_file)),
            artifact_parent_dir)


        def mvn_side_effect(*args, **kwargs):
            if 'clean' in args:
                if os.path.exists(target_dir_path):
                    os.rmdir(target_dir_path)

            if 'install' in args:
                os.mkdir(target_dir_path)

                for artifact_name in artifact_names:
                    artifact_path = os.path.join(
                        target_dir_path,
                        artifact_name
                    )
                    Path(artifact_path).touch()

        return mvn_side_effect

    @patch('sh.mvn', create=True)
    def test_run_step_pass(self, mvn_mock):
        with TempDirectory() as temp_dir:
            artifact_id = 'my-app'
            version = '1.0'
            package = 'jar'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('pom.xml',b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>1.0</version>
                <package>war</package>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {'pom-file': pom_file_path}
            
            artifact_file_name = f'{artifact_id}-{version}.{package}'

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='package',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            mvn_mock.side_effect = TestStepImplementerMavenPackageBase.create_mvn_side_effect(
                pom_file_path, 
                'target', 
                [artifact_file_name])
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='package', sub_step_name='Maven', sub_step_implementer_name='Maven')
            expected_step_result.add_artifact(name='path', value=temp_dir.path + '/target/my-app-1.0.jar', value_type='path')
            expected_step_result.add_artifact(name='artifact-id', value='my-app')
            expected_step_result.add_artifact(name='group-id', value='com.mycompany.app')
            expected_step_result.add_artifact(name='package-type', value='war')
            expected_step_result.add_artifact(name='pom-path', value=pom_file_path, value_type='path')

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch('sh.mvn', create=True)
    def test_run_step_pass_no_package_in_pom(self, mvn_mock):
        with TempDirectory() as temp_dir:
            artifact_id = 'my-app'
            version = '1.0'
            package = 'jar'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('pom.xml',b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>1.0</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {'pom-file': pom_file_path}
            
            artifact_file_name = f'{artifact_id}-{version}.{package}'

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='package',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            mvn_mock.side_effect = TestStepImplementerMavenPackageBase.create_mvn_side_effect(
                pom_file_path, 
                'target', 
                [artifact_file_name])
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='package', sub_step_name='Maven', sub_step_implementer_name='Maven')
            expected_step_result.add_artifact(name='path', value=temp_dir.path + '/target/my-app-1.0.jar', value_type='path')
            expected_step_result.add_artifact(name='artifact-id', value='my-app')
            expected_step_result.add_artifact(name='group-id', value='com.mycompany.app')
            expected_step_result.add_artifact(name='package-type', value='jar')
            expected_step_result.add_artifact(name='pom-path', value=pom_file_path, value_type='path')

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())
    
    @patch('sh.mvn', create=True)
    def test_run_step_fail_no_pom(self, mvn_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}
            
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='package',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='package', sub_step_name='Maven', sub_step_implementer_name='Maven')
            expected_step_result.success = False
            expected_step_result.message = 'Given pom file does not exist: pom.xml'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch('sh.mvn', create=True)
    def test_run_step_fail_mvn_error(self, mvn_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('pom.xml',b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>1.0</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {'pom-file': pom_file_path}
            
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='package',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            mvn_mock.side_effect = sh.ErrorReturnCode('maven', b'mock out', b'mock error')

            with self.assertRaisesRegex(
                RuntimeError,
                "Error invoking mvn:"
            ):
                step_implementer._run_step()

    @patch('sh.mvn', create=True)
    def test_run_step_fail_multiple_artifacts(self, mvn_mock):
        with TempDirectory() as temp_dir:
            artifact_id = 'my-app'
            version = '1.0'
            package = 'jar'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('pom.xml',b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>1.0</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {'pom-file': pom_file_path}
            
            artifact_file_name = f'{artifact_id}-{version}.{package}'

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='package',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            mvn_mock.side_effect = TestStepImplementerMavenPackageBase.create_mvn_side_effect(
                pom_file_path, 
                'target', 
                [
                    f'{artifact_id}-{version}.war',
                    artifact_file_name
                ]
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='package', sub_step_name='Maven', sub_step_implementer_name='Maven')
            expected_step_result.success = False
            expected_step_result.message = "pom resulted in multiple artifacts with expected artifact extensions (['jar', 'war', 'ear']), this is unsupported"
            print(result.get_step_result())
            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch('sh.mvn', create=True)
    def test_run_step_fail_no_artifacts(self, mvn_mock):
        with TempDirectory() as temp_dir:
            artifact_id = ''
            version = ''
            package = ''
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('pom.xml',b'''<project>
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.mycompany.app</groupId>
                <artifactId>my-app</artifactId>
                <version>1.0</version>
            </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            step_config = {'pom-file': pom_file_path}
            
            artifact_file_name = f'{artifact_id}-{version}.{package}'

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='package',
                implementer='Maven',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            mvn_mock.side_effect = TestStepImplementerMavenPackageBase.create_mvn_side_effect(
                pom_file_path, 
                'target', 
                [artifact_file_name]
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='package', sub_step_name='Maven', sub_step_implementer_name='Maven')
            expected_step_result.success = False
            expected_step_result.message = "pom resulted in 0 with expected artifact extensions (['jar', 'war', 'ear']), this is unsupported"
            print(result.get_step_result())
            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())