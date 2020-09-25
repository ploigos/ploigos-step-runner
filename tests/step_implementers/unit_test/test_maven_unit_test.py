import os
from io import IOBase
import sh
from pathlib import Path

from testfixtures import TempDirectory
import unittest
from unittest.mock import patch
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.unit_test import Maven
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

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
                raise RuntimeError('Error: No unit tests defined')

            os.makedirs(target_dir_path, exist_ok=True)

            for artifact_name in artifact_names:
                artifact_path = os.path.join(
                    target_dir_path,
                    artifact_name
                )
                Path(artifact_path).touch()

    return mvn_side_effect

class TestStepImplementerUnitTest(BaseTSSCTestCase):

    @patch('sh.mvn', create=True)
    def test_unit_test_default_pom_file_missing(self, mvn_mock):
        config = {
            'tssc-config': {
                'unit-test': {
                    'implementer': 'Maven'
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
                    'implementer': 'Maven'
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError,
                "Given pom file does not exist: does-not-exist-pom.xml"):
            factory.config.set_step_config_overrides(
                'unit-test',
                {'pom-file': 'does-not-exist-pom.xml'})
            factory.run_step('unit-test')

    @patch('sh.mvn', create=True)
    def test_unit_test_config_file_pom_file_missing(self, mvn_mock):
        config = {
            'tssc-config': {
                'unit-test': {
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
            factory.run_step('unit-test')

    @patch('sh.mvn', create=True, side_effect = sh.ErrorReturnCode('mvn clean test', b'mock out', b'mock error'))
    def test_mvn_error_return_code(self, mvn_mock):
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
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'unit-test': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            expected_step_results = {
                'tssc-results': {
                    'unit-test': {
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
                    RuntimeError,
                    'Error invoking mvn:.*'):
                run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)

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
            test_results_dir = os.path.join(temp_dir.path, reports_dir)
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'unit-test': {
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
                    'unit-test': {
                        'result': {
                            'success': True,
                            'message': 'unit test step run successfully and junit reports were generated'
                        },
                        'options': {
                            'pom-path': str(pom_file_path)
                        },
                        'report-artifacts': [
                            {
                                'name': 'maven unit test results generated using junit',
                                'path': f'file://{str(test_results_dir)}'
                            }
                        ]
                    }
                }
            }

            settings_file_path = f'{temp_dir.path}/tssc-working/unit-test/settings.xml'
            run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                'test',
                '-f',
                pom_file_path,
                '-s',
                settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

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
                    'unit-test': {
                        'result': {
                            'success': True,
                            'message': 'unit test step run successfully and junit reports were generated'
                        },
                        'options': {
                            'pom-path': str(pom_file_path)
                        },
                        'report-artifacts': [
                            {
                                'name': 'maven unit test results generated using junit',
                                'path': f'file://{str(reports_dir)}'
                            }
                        ]
                    }
                }
            }

            settings_file_path = f'{temp_dir.path}/tssc-working/unit-test/settings.xml'
            run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                'test',
                '-f',
                pom_file_path,
                '-s',
                settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    def test_unit_test_missing_surefire_plugin_in_pom(self):
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
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'unit-test': {
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
                ]
            )
            expected_step_results = {
                'tssc-results': {
                    'unit-test': {
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
                    RuntimeError, 'Error: No unit tests defined'):
                run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)

    @patch('sh.mvn', create=True)
    def test_unit_test_run_attempt_fails_default_fail_on_no_tests_flag(self, mvn_mock):
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
                    'unit-test': {
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
                    RuntimeError, 'Error: No unit tests defined'):
                run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)

    @patch('sh.mvn', create=True)
    def test_unit_test_run_attempt_fails_fail_on_no_tests_flag_false(self, mvn_mock):
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
                    'unit-test': {
                        'result': {
                            'success': True,
                            'message': 'unit test step run successfully, but no tests were found'
                        },
                        'report-artifacts': [],
                        'options': {
                            'pom-path': str(pom_file_path),
                            'fail-on-no-tests': False
                        }
                    }
                }
            }

            settings_file_path = f'{temp_dir.path}/tssc-working/unit-test/settings.xml'
            run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                'test',
                '-f',
                pom_file_path,
                '-s',
                settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
