import os
import sys

from pathlib import Path
import pytest
from testfixtures import TempDirectory
import unittest
from unittest.mock import patch
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.unit_test import JUnit

from test_utils import *

def create_mvn_side_effect(pom_file, artifact_parent_dir, artifact_names, throw_mvn_exception=False):
    """simulates what mvn does by touching files.
    
    Notes
    -----
    
    Supports
    
    - mvn clean
    - mvn install
    - mvn test
    
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
        
        if 'test' in args:
            if throw_mvn_exception is True:
                raise RuntimeError

            os.makedirs(target_dir_path, exist_ok=True)
            
            for artifact_name in artifact_names:
                artifact_path = os.path.join(
                    target_dir_path,
                    artifact_name
                )
                Path(artifact_path).touch()

    return mvn_side_effect

class TestStepImplementerUnitTest(unittest.TestCase):

    @patch('sh.mvn', create=True)
    def test_unit_test_default_pom_file_missing(self, mvn_mock):
        config = {
            'tssc-config': {
                'unit-test': {
                    'implementer': 'JUnit'
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError, 
                "Given pom file does not exist: pom.xml"):
            factory.run_step('unit-test')

    @patch('sh.mvn', create=True)
    def test_unit_test_runtime_pom_file_missing(self, mvn_mock):
        config = {
            'tssc-config': {
                'unit-test': {
                    'implementer': 'JUnit'
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError, 
                "Given pom file does not exist: does-not-exist-pom.xml"):
            factory.run_step('unit-test', {'pom-file': 'does-not-exist-pom.xml'})
    
    @patch('sh.mvn', create=True)
    def test_unit_test_config_file_pom_file_missing(self, mvn_mock):
        config = {
            'tssc-config': {
                'unit-test': {
                    'implementer': 'JUnit',
                    'config': {
                        'pom-file': 'does-not-exist.pom'
                    }
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError, 
                'Given pom file does not exist: does-not-exist.pom'):
            factory.run_step('unit-test')

    @patch('sh.mvn', create=True)
    def test_unit_test_no_reports_directory_reference_in_pom(self, mvn_mock):
        reports_dir = 'target/surefire-reports'
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        version = '1.0'
        with TempDirectory() as temp_dir:
            temp_dir.write(
                'pom.xml',
                bytes('''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" 
  xmlns="http://maven.apache.org/POM/4.0.0" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
                <configuration>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>'''.format(group_id=group_id, artifact_id=artifact_id, version=version), 'utf-8')
            )
            test_results_dir = os.path.join(temp_dir.path,'tssc-results/unit-test/junit')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'unit-test': {
                        'implementer': 'JUnit',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            factory = TSSCFactory(config)
            
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                [
                    '{group_id}.{artifact_id}.ClassNameTest.txt'.format(group_id=group_id, artifact_id=artifact_id),
                    'TEST-{group_id}.{artifact_id}.ClassNameTest.xml'.format(group_id=group_id, artifact_id=artifact_id)
                ]
            )
            expected_step_results = {
                'tssc-results': {
                    'unit-test': {
                        'junit': {
                            'pom-path': str(pom_file_path),
                            'test-results': test_results_dir
                        }
                    }
                }
            }

            run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)
            mvn_mock.assert_called_once_with('clean', 'test', '-f', pom_file_path, _out=sys.stdout)

    @patch('sh.mvn', create=True)
    def test_unit_test_reports_directory_reference_exists_in_pom(self, mvn_mock):
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        version = '1.0'
        with TempDirectory() as temp_dir:
            reports_dir = os.path.join(temp_dir.path, 'target/custom-reports-dir')
            temp_dir.write(
                'pom.xml',
                bytes('''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" 
  xmlns="http://maven.apache.org/POM/4.0.0" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
                <configuration>
                    <reportsDirectory>{reports_dir}</reportsDirectory>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>'''.format(group_id=group_id, artifact_id=artifact_id, version=version, reports_dir=reports_dir), 'utf-8')
            )
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'unit-test': {
                        'implementer': 'JUnit',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            factory = TSSCFactory(config)
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                [
                    '{group_id}.{artifact_id}.ClassNameTest.txt'.format(group_id=group_id, artifact_id=artifact_id),
                    'TEST-{group_id}.{artifact_id}.ClassNameTest.xml'.format(group_id=group_id, artifact_id=artifact_id)
                ]
            )

            test_results_dir = os.path.join(temp_dir.path,'tssc-results/unit-test/junit')

            expected_step_results = {
                'tssc-results': {
                    'unit-test': {
                        'junit': {
                            'pom-path': str(pom_file_path),
                            'test-results': test_results_dir
                        }
                    }
                }
            }

            run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)
            mvn_mock.assert_called_once_with('clean', 'test', '-f', pom_file_path, _out=sys.stdout)

    def test_unit_test_missing_surefire_plugin_in_pom(self):
        reports_dir = 'target/surefire-reports'
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        version = '1.0'
        with TempDirectory() as temp_dir:
            temp_dir.write(
                'pom.xml',
                bytes('''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" 
  xmlns="http://maven.apache.org/POM/4.0.0" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <modelVersion>4.0.0</modelVersion>
        <groupId>{group_id}</groupId>
        <artifactId>{artifact_id}</artifactId>
        <version>{version}</version>
</project>'''.format(group_id=group_id, artifact_id=artifact_id, version=version), 'utf-8')
            )
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'unit-test': {
                        'implementer': 'JUnit',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            factory = TSSCFactory(config)
            with self.assertRaisesRegex(
                ValueError, 
                'Unit test dependency "maven-surefire-plugin" missing from POM.'):
                factory.run_step('unit-test')
        
    @patch('sh.mvn', create=True)
    def test_unit_test_empty_reports_dir(self, mvn_mock):
        reports_dir = 'target/surefire-reports'
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        version = '1.0'
        with TempDirectory() as temp_dir:
            temp_dir.write(
                'pom.xml',
                bytes('''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" 
  xmlns="http://maven.apache.org/POM/4.0.0" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
                <configuration>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>'''.format(group_id=group_id, artifact_id=artifact_id, version=version), 'utf-8')
            )
            test_results_dir = os.path.join(temp_dir.path,'tssc-results/unit-test/junit')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'unit-test': {
                        'implementer': 'JUnit',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            factory = TSSCFactory(config)
            
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                [
                ]
            )
            expected_step_results = {
                'tssc-results': {
                    'unit-test': {
                        'junit': {
                            'pom-path': str(pom_file_path),
                            'test-results': 'NO UNIT TEST RESULTS'
                        }
                    }
                }
            }

            run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)
            mvn_mock.assert_called_once_with('clean', 'test', '-f', pom_file_path, _out=sys.stdout)

    @patch('sh.mvn', create=True)
    def test_unit_test_run_attempt_fails(self, mvn_mock):
        reports_dir = 'target/surefire-reports'
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        version = '1.0'
        with TempDirectory() as temp_dir:
            temp_dir.write(
                'pom.xml',
                bytes('''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" 
  xmlns="http://maven.apache.org/POM/4.0.0" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <modelVersion>4.0.0</modelVersion>
        <groupId>{group_id}</groupId>
        <artifactId>{artifact_id}</artifactId>
        <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
                <configuration>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>'''.format(group_id=group_id, artifact_id=artifact_id, version=version), 'utf-8')
            )
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'unit-test': {
                        'implementer': 'JUnit',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            factory = TSSCFactory(config)

            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                [],
                True
            )

            with self.assertRaisesRegex(
                RuntimeError,''):
                factory.run_step('unit-test')
