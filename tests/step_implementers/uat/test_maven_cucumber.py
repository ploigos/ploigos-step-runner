"""Test Maven Cucumber

Tests the Maven Cucumber UAT step.
"""
from os import path, rmdir, makedirs
from sys import stdout
from unittest.mock import patch
from pathlib import Path
from sh import ErrorReturnCode

from testfixtures import TempDirectory

from tssc import TSSCFactory
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.test_utils import run_step_test_with_result_validation

def create_resources(target_dir_path, artifact_names):
    """Create resources.

    Given a list of artifact_names, will create them all at a given path, target_dir_path.
    It is ok if path already exists, no error will be thrown.
    """
    makedirs(target_dir_path, exist_ok=True)
    for artifact_name in artifact_names:
        artifact_path = path.join(
            target_dir_path,
            artifact_name
        )
        Path(artifact_path).touch()

def create_mvn_side_effect(pom_file, artifact_parent_dir, artifact_names, throw_mvn_error=False):
    """Simulates what mvn does by touching files.

    Notes
    -----

    Supports

    - mvn clean
    - mvn install
    - mvn test

    """

    target_dir_path = path.join(
        path.dirname(path.abspath(pom_file)),
        artifact_parent_dir)

    def mvn_side_effect(*args, **_kwargs):
        if 'clean' in args and path.exists(target_dir_path):
            rmdir(target_dir_path)

        if 'install' in args:
            create_resources(target_dir_path, artifact_names)

        if 'test' in args:
            if throw_mvn_error is True:
                raise RuntimeError('Error: No uat defined')
            create_resources(target_dir_path, artifact_names)

    return mvn_side_effect

# pylint: disable=R0201,C0301
class TestStepImplementerUatTest(BaseTSSCTestCase):
    """Test Step Implementer UAT

    Runner for the UAT Step Implementer
    """

    @patch('sh.mvn', create=True)
    def test_uat_default_pom_file_missing(self, _mvn_mock):
        """ Test if the default pom file is missing
        """
        config = {
            'tssc-config': {
                'uat': {
                    'implementer': 'Maven',
                    'config': {}
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError,
                'Given pom file does not exist: pom.xml'):
            factory.run_step('uat')

    @patch('sh.mvn', create=True)
    def test_uat_runtime_pom_file_missing(self, _mvn_mock):
        """Test when pom file is invalid."""
        config = {
            'tssc-config': {
                'uat': {
                    'implementer': 'Maven'
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError,
                'Given pom file does not exist: does-not-exist-pom.xml'):
            factory.run_step('uat', {'pom-file': 'does-not-exist-pom.xml'})

    @patch('sh.mvn', create=True)
    def test_uat_config_file_pom_file_missing(self, _mvn_mock):
        """Test when config has invalid pom file."""
        config = {
            'tssc-config': {
                'uat': {
                    'implementer': 'Maven',
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
            factory.run_step('uat')

    @patch('sh.mvn', create=True, side_effect=ErrorReturnCode('mvn clean -Pintegration-test test', b'mock out', b'mock error'))
    def test_uat_mvn_error_return_code(self, _mvn_mock):
        """Test when maven returns an error code"""
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        version = '1.0'
        with TempDirectory() as temp_dir:
            temp_dir.write('src/main/java/com/mycompany/app/App.java', b'''package com.mycompany.app;
    public class App {
        public static void main( String[] args ) {
            System.out.println( "Hello World!" );
        }
    }''')
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
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            expected_step_results = {
                'tssc-results': {
                    'uat': {
                        'result': {
                            'success': False,
                            'message': 'Failure message'
                        },
                        'report-artifacts': [],
                        'options': {
                            'pom-path': str(pom_file_path)
                        }
                    }
                }
            }

            with self.assertRaisesRegex(
                    RuntimeError,
                    'Error invoking mvn:.*'):
                run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)

    @patch('sh.mvn', create=True)
    def test_uat_no_reports_directory_reference_in_pom(self, mvn_mock):
        """Test when no reports directory in defined in the pom."""
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
            test_results_dir = path.join(temp_dir.path, reports_dir)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
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
                    'uat': {
                        'result': {
                            'success': True,
                            'message': 'uat step run successfully and junit reports were generated'
                        },
                        'options': {
                            'pom-path': str(pom_file_path)
                        },
                        'report-artifacts': [
                            {
                                'name': 'uat results generated using junit',
                                'path': f'file://{str(test_results_dir)}'
                            }
                        ]
                    }
                }
            }

            run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                '-Pintegration-test',
                '-Dselenium.hub.url=http://192.168.1.11:4444',
                '-Dtarget.base.url=http://192.168.1.11:8080',
                '-Dcucumber.plugin=html:target/cucumber.html,json:target/cucumber.json',
                'test',
                '-f', pom_file_path,
                _out=stdout
            )

    @patch('sh.mvn', create=True)
    def test_uat_reports_directory_reference_exists_in_pom(self, mvn_mock):
        """Test when the reports directory exists in the pom."""
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        version = '1.0'
        with TempDirectory() as temp_dir:
            reports_dir = path.join(temp_dir.path, 'target/custom-reports-dir')
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
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
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
                    'uat': {
                        'result': {
                            'success': True,
                            'message': 'uat step run successfully and junit reports were generated'
                        },
                        'options': {
                            'pom-path': str(pom_file_path)
                        },
                        'report-artifacts': [
                            {
                                'name': 'uat results generated using junit',
                                'path': f'file://{str(reports_dir)}'
                            }
                        ]
                    }
                }
            }

            run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                '-Pintegration-test',
                '-Dselenium.hub.url=http://192.168.1.11:4444',
                '-Dtarget.base.url=http://192.168.1.11:8080',
                '-Dcucumber.plugin=html:target/cucumber.html,json:target/cucumber.json',
                'test',
                '-f', pom_file_path,
                _out=stdout
            )

    def test_uat_test_missing_surefire_plugin_in_pom(self):
        """Test when missing surefire plugin in pom."""
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
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            factory = TSSCFactory(config)
            with self.assertRaisesRegex(
                    ValueError,
                    'Uat dependency "maven-surefire-plugin" missing from POM.'):
                factory.run_step('uat')

    @patch('sh.mvn', create=True)
    def test_uat_empty_reports_dir(self, mvn_mock):
        """Test when report dir is empty."""
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
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                []
            )
            expected_step_results = {
                'tssc-results': {
                    'uat': {
                        'result': {
                            'success': False,
                            'message': "Failure message"
                        },
                        'report-artifacts': [],
                        'options': {
                            'pom-path': str(pom_file_path)
                        }
                    }
                }
            }

            with self.assertRaisesRegex(
                    RuntimeError, 'Error: No uat defined'):
                run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)

    @patch('sh.mvn', create=True)
    def test_uat_run_attempt_fails_default_fail_on_no_tests_flag(self, mvn_mock):
        """Test when failure on no tests."""
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
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                [],
                True
            )
            expected_step_results = {
                'tssc-results': {
                    'uat': {
                        'result': {
                            'success': False,
                            'message': "Failure message"
                        },
                        'report-artifacts': [],
                        'options': {
                            'pom-path': str(pom_file_path)
                        }
                    }
                }
            }

            with self.assertRaisesRegex(
                    RuntimeError, 'Error: No uat defined'):
                run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)


    @patch('sh.mvn', create=True)
    def test_uat_run_attempt_fails_fail_on_no_tests_flag_false(self, mvn_mock):
        """Test when failure on no tests with flag to ignore it set."""
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
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'fail-on-no-tests': False,
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                []
            )
            expected_step_results = {
                'tssc-results': {
                    'uat': {
                        'result': {
                            'success': True,
                            'message': 'Uat step run successfully, but no tests were found'
                        },
                        'report-artifacts': [],
                        'options': {
                            'pom-path': str(pom_file_path),
                            'fail-on-no-tests': False
                        }
                    }
                }
            }

            run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                '-Pintegration-test',
                '-Dselenium.hub.url=http://192.168.1.11:4444',
                '-Dtarget.base.url=http://192.168.1.11:8080',
                '-Dcucumber.plugin=html:target/cucumber.html,json:target/cucumber.json',
                'test',
                '-f', pom_file_path,
                _out=stdout
            )
