"""Test Maven Cucumber

Tests the Maven Cucumber UAT step.
"""
from os import path, rmdir, makedirs
from io import IOBase
from unittest.mock import patch
from pathlib import Path
from sh import ErrorReturnCode

from testfixtures import TempDirectory

from tssc import TSSCFactory
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.test_utils import run_step_test_with_result_validation, Any

SELENIUM_HUB_URL = 'http://selenium:4444'
TARGET_BASE_URL = 'http://app:8080'

def create_pom(temp_dir, build_config,
               group_id='com.mycompany.app', artifact_id='my-app', version='1.0'):
    """Creates pom file.

    Will create the pom.xml file and return the location.
    """
    data = bytes('''<project
                    xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
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
                        {build_config}
                    </project>'''.format(
                        group_id=group_id,
                        artifact_id=artifact_id,
                        version=version,
                        build_config=build_config), 'utf-8')

    temp_dir.write('pom.xml', data)
    return path.join(temp_dir.path, 'pom.xml')

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
        artifact_parent_dir
    )

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

# pylint: disable=R0201
class TestStepImplementerUatTest(BaseTSSCTestCase):
    """Test Step Implementer UAT

    Runner for the UAT Step Implementer.
    """

    @patch('sh.mvn', create=True)
    def test_uat_mandatory_selenium_hub_url_missing(self, _mvn_mock):
        """Test when mandatory selenium hub url is missing."""
        config = {
            'tssc-config': {
                'uat': {
                    'implementer': 'Maven'
                }
            }
        }
        factory = TSSCFactory(config)
        error_message = '.* is missing the required configuration keys ' \
            '\\(\\[\'selenium-hub-url\'\\]\\).*'
        with self.assertRaisesRegex(
                AssertionError,
                error_message):
            factory.run_step('uat')

    @patch('sh.mvn', create=True)
    def test_uat_mandatory_target_base_url_missing(self, _mvn_mock):
        """Test when mandatory target base url is missing."""
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
                'No target base url was specified'):
            factory.config.set_step_config_overrides(
                'uat',
                {
                    'selenium-hub-url': SELENIUM_HUB_URL,
                }
            )
            factory.run_step('uat')

    @patch('sh.mvn', create=True)
    def test_uat_default_pom_file_missing(self, _mvn_mock):
        """Test if the default pom file is missing."""
        config = {
            'tssc-config': {
                'uat': {
                    'implementer': 'Maven',
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError,
                'Given pom file does not exist: pom.xml'):
            factory.config.set_step_config_overrides(
                'uat',
                {
                    'selenium-hub-url': SELENIUM_HUB_URL,
                    'target-base-url': TARGET_BASE_URL
                }
            )
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
            factory.config.set_step_config_overrides(
                'uat',
                {
                    'pom-file': 'does-not-exist-pom.xml',
                    'selenium-hub-url': SELENIUM_HUB_URL,
                    'target-base-url': TARGET_BASE_URL
                }
            )
            factory.run_step('uat')

    @patch('sh.mvn', create=True)
    def test_uat_config_file_pom_file_missing(self, _mvn_mock):
        """Test when config has invalid pom file."""
        config = {
            'tssc-config': {
                'uat': {
                    'implementer': 'Maven',
                    'config': {
                        'pom-file': 'does-not-exist.pom',
                        'selenium-hub-url': SELENIUM_HUB_URL,
                        'target-base-url': TARGET_BASE_URL
                    }
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError,
                'Given pom file does not exist: does-not-exist.pom'):
            factory.run_step('uat')

    @patch(
        'sh.mvn',
        create=True,
        side_effect=ErrorReturnCode('mvn clean -Pintegration-test test', b'mock out', b'mock error')
    )
    def test_uat_mvn_error_return_code(self, _mvn_mock):
        """Test when maven returns an error code."""
        with TempDirectory() as temp_dir:
            temp_dir.write(
                'src/main/java/com/mycompany/app/App.java',
                b'''package com.mycompany.app;
                    public class App {
                        public static void main( String[] args ) {
                            System.out.println( "Hello World!" );
                        }
                    }
                '''
            )
            build_config = '''<build>
                                  <plugins>
                                      <plugin>
                                          <artifactId>maven-surefire-plugin</artifactId>
                                          <version>${{surefire-plugin.version}}</version>
                                          <configuration></configuration>
                                      </plugin>
                                  </plugins>
                              </build>'''
            pom_file_path = create_pom(temp_dir, build_config)
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL,
                            'target-base-url': TARGET_BASE_URL
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
        with TempDirectory() as temp_dir:
            build_config = '''<build>
                                  <plugins>
                                      <plugin>
                                          <artifactId>maven-surefire-plugin</artifactId>
                                          <version>${{surefire-plugin.version}}</version>
                                          <configuration></configuration>
                                      </plugin>
                                  </plugins>
                              </build>'''
            pom_file_path = create_pom(
                temp_dir,
                build_config,
                group_id=group_id,
                artifact_id=artifact_id
            )
            test_results_dir = path.join(temp_dir.path, 'target/cucumber')
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL,
                            'target-base-url': TARGET_BASE_URL
                        }
                    }
                }
            }
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                [
                    '{group_id}.{artifact_id}.ClassNameTest.txt' \
                        .format(group_id=group_id, artifact_id=artifact_id),
                    'TEST-{group_id}.{artifact_id}.ClassNameTest.xml' \
                        .format(group_id=group_id, artifact_id=artifact_id)
                ]
            )
            expected_step_results = {
                'tssc-results': {
                    'uat': {
                        'result': {
                            'success': True,
                            'message': 'Uat step run successfully and reports were generated'
                        },
                        'options': {
                            'pom-path': str(pom_file_path)
                        },
                        'report-artifacts': [
                            {
                                'name': 'Uat results generated',
                                'path': f'file://{str(test_results_dir)}'
                            }
                        ]
                    }
                }
            }

            settings_file_path = f'{temp_dir.path}/tssc-working/uat/settings.xml'
            run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                '-Pintegration-test',
                f'-Dselenium.hub.url={SELENIUM_HUB_URL}',
                f'-Dtarget.base.url={TARGET_BASE_URL}',
                '-Dcucumber.plugin=html:target/cucumber/cucumber.html,' \
                    'json:target/cucumber/cucumber.json',
                'test',
                '-f', pom_file_path,
                '-s', settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.mvn', create=True)
    def test_uat_reports_directory_reference_exists_in_pom(self, mvn_mock):
        """Test when the reports directory exists in the pom."""
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        with TempDirectory() as temp_dir:
            reports_dir = path.join(temp_dir.path, 'target/custom-reports-dir')
            build_config = '''<build>
                                  <plugins>
                                      <plugin>
                                          <artifactId>maven-surefire-plugin</artifactId>
                                          <version>${{surefire-plugin.version}}</version>
                                          <configuration>
                                              <reportsDirectory>{reports_dir}</reportsDirectory>
                                          </configuration>
                                      </plugin>
                                  </plugins>
                              </build>'''.format(reports_dir=reports_dir)
            pom_file_path = create_pom(
                temp_dir,
                build_config,
                group_id=group_id,
                artifact_id=artifact_id
            )
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL,
                            'target-base-url': TARGET_BASE_URL
                        }
                    }
                }
            }
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                [
                    '{group_id}.{artifact_id}.ClassNameTest.txt' \
                        .format(group_id=group_id, artifact_id=artifact_id),
                    'TEST-{group_id}.{artifact_id}.ClassNameTest.xml' \
                        .format(group_id=group_id, artifact_id=artifact_id)
                ]
            )

            expected_step_results = {
                'tssc-results': {
                    'uat': {
                        'result': {
                            'success': True,
                            'message': 'Uat step run successfully and reports were generated'
                        },
                        'options': {
                            'pom-path': str(pom_file_path)
                        },
                        'report-artifacts': [
                            {
                                'name': 'Uat results generated',
                                'path': f'file://{path.join(temp_dir.path, "target/cucumber")}'
                            }
                        ]
                    }
                }
            }

            settings_file_path = f'{temp_dir.path}/tssc-working/uat/settings.xml'
            run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                '-Pintegration-test',
                f'-Dselenium.hub.url={SELENIUM_HUB_URL}',
                f'-Dtarget.base.url={TARGET_BASE_URL}',
                '-Dcucumber.plugin=html:target/cucumber/cucumber.html,' \
                    'json:target/cucumber/cucumber.json',
                'test',
                '-f', pom_file_path,
                '-s', settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    def test_uat_test_missing_surefire_plugin_in_pom(self):
        """Test when missing surefire plugin in pom."""
        with TempDirectory() as temp_dir:
            build_config = ''
            pom_file_path = create_pom(temp_dir, build_config)
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL,
                            'target-base-url': TARGET_BASE_URL
                        }
                    }
                }
            }
            factory = TSSCFactory(config, temp_dir)
            with self.assertRaisesRegex(
                    ValueError,
                    'Uat dependency "maven-surefire-plugin" missing from POM.'):
                factory.run_step('uat')

    @patch('sh.mvn', create=True)
    def test_uat_empty_reports_dir(self, mvn_mock):
        """Test when report dir is empty."""
        reports_dir = 'target/surefire-reports'
        with TempDirectory() as temp_dir:
            build_config = '''<build>
                                  <plugins>
                                      <plugin>
                                          <artifactId>maven-surefire-plugin</artifactId>
                                          <version>${{surefire-plugin.version}}</version>
                                          <configuration></configuration>
                                      </plugin>
                                  </plugins>
                              </build>'''
            pom_file_path = create_pom(temp_dir, build_config)
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL,
                            'target-base-url': TARGET_BASE_URL
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
        with TempDirectory() as temp_dir:
            build_config = '''<build>
                                  <plugins>
                                      <plugin>
                                          <artifactId>maven-surefire-plugin</artifactId>
                                          <version>${{surefire-plugin.version}}</version>
                                          <configuration></configuration>
                                      </plugin>
                                  </plugins>
                              </build>'''
            pom_file_path = create_pom(temp_dir, build_config)
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL,
                            'target-base-url': TARGET_BASE_URL
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
        """Test when failure on no tests with flag to ignore it set to false."""
        reports_dir = 'target/surefire-reports'
        with TempDirectory() as temp_dir:
            build_config = '''<build>
                                  <plugins>
                                      <plugin>
                                          <artifactId>maven-surefire-plugin</artifactId>
                                          <version>${{surefire-plugin.version}}</version>
                                          <configuration></configuration>
                                      </plugin>
                                  </plugins>
                              </build>'''
            pom_file_path = create_pom(temp_dir, build_config)
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'fail-on-no-tests': False,
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL,
                            'target-base-url': TARGET_BASE_URL
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

            settings_file_path = f'{temp_dir.path}/tssc-working/uat/settings.xml'
            run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                '-Pintegration-test',
                f'-Dselenium.hub.url={SELENIUM_HUB_URL}',
                f'-Dtarget.base.url={TARGET_BASE_URL}',
                '-Dcucumber.plugin=html:target/cucumber/cucumber.html,' \
                    'json:target/cucumber/cucumber.json',
                'test',
                '-f', pom_file_path,
                '-s', settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.mvn', create=True)
    def test_uat_run_attempt_fails_fail_on_no_tests_flag_true(self, mvn_mock):
        """Test when failure on no tests with flag to ignore it set to true."""
        reports_dir = 'target/surefire-reports'
        with TempDirectory() as temp_dir:
            build_config = '''<build>
                                  <plugins>
                                      <plugin>
                                          <artifactId>maven-surefire-plugin</artifactId>
                                          <version>${{surefire-plugin.version}}</version>
                                          <configuration></configuration>
                                      </plugin>
                                  </plugins>
                              </build>'''
            pom_file_path = create_pom(temp_dir, build_config)
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'fail-on-no-tests': True,
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL,
                            'target-base-url': TARGET_BASE_URL
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
    def test_uat_with_custom_report_dir(self, mvn_mock):
        """Test with custom report directory."""
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        reports_dir = 'target/surefire-reports'
        with TempDirectory() as temp_dir:
            build_config = '''<build>
                                  <plugins>
                                      <plugin>
                                          <artifactId>maven-surefire-plugin</artifactId>
                                          <version>${{surefire-plugin.version}}</version>
                                      </plugin>
                                  </plugins>
                              </build>'''
            pom_file_path = create_pom(
                temp_dir,
                build_config,
                group_id=group_id,
                artifact_id=artifact_id
            )
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL,
                            'target-base-url': TARGET_BASE_URL,
                            'report-dir': 'custom-cucumber'
                        }
                    }
                }
            }
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                [
                    '{group_id}.{artifact_id}.ClassNameTest.txt' \
                        .format(group_id=group_id, artifact_id=artifact_id),
                    'TEST-{group_id}.{artifact_id}.ClassNameTest.xml' \
                        .format(group_id=group_id, artifact_id=artifact_id)
                ]
            )

            test_results_dir = path.join(temp_dir.path, 'target/custom-cucumber')
            expected_step_results = {
                'tssc-results': {
                    'uat': {
                        'result': {
                            'success': True,
                            'message': 'Uat step run successfully and reports were generated'
                        },
                        'options': {
                            'pom-path': str(pom_file_path)
                        },
                        'report-artifacts': [
                            {
                                'name': 'Uat results generated',
                                'path': f'file://{str(test_results_dir)}'
                            }
                        ]
                    }
                }
            }

            settings_file_path = f'{temp_dir.path}/tssc-working/uat/settings.xml'
            run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                '-Pintegration-test',
                f'-Dselenium.hub.url={SELENIUM_HUB_URL}',
                f'-Dtarget.base.url={TARGET_BASE_URL}',
                '-Dcucumber.plugin=html:target/custom-cucumber/cucumber.html,' \
                    'json:target/custom-cucumber/cucumber.json',
                'test',
                '-f', pom_file_path,
                '-s', settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.mvn', create=True)
    def test_uat_with_deploy_dir(self, mvn_mock):
        """Test with report directory from the deploy."""
        group_id = 'com.mycompany.app'
        artifact_id = 'my-app'
        reports_dir = 'target/surefire-reports'
        endpoint_url = 'http://new-unique-app:8080'
        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')
            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(f'''tssc-results:
                            deploy:
                              result:
                                deploy-endpoint-url: {endpoint_url}''', 'utf-8')
            )

            build_config = '''<build>
                                  <plugins>
                                      <plugin>
                                          <artifactId>maven-surefire-plugin</artifactId>
                                          <version>${{surefire-plugin.version}}</version>
                                      </plugin>
                                  </plugins>
                              </build>'''
            pom_file_path = create_pom(
                temp_dir,
                build_config,
                group_id=group_id,
                artifact_id=artifact_id
            )
            config = {
                'tssc-config': {
                    'uat': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path),
                            'selenium-hub-url': SELENIUM_HUB_URL
                        }
                    }
                }
            }
            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                reports_dir,
                [
                    '{group_id}.{artifact_id}.ClassNameTest.txt' \
                        .format(group_id=group_id, artifact_id=artifact_id),
                    'TEST-{group_id}.{artifact_id}.ClassNameTest.xml' \
                        .format(group_id=group_id, artifact_id=artifact_id)
                ]
            )

            test_results_dir = path.join(temp_dir.path, 'target/cucumber')
            expected_step_results = {
                'tssc-results': {
                    'deploy': {
                        'result': {
                            'deploy-endpoint-url': f'{endpoint_url}'
                        }
                    },
                    'uat': {
                        'result': {
                            'success': True,
                            'message': 'Uat step run successfully and reports were generated'
                        },
                        'options': {
                            'pom-path': str(pom_file_path)
                        },
                        'report-artifacts': [
                            {
                                'name': 'Uat results generated',
                                'path': f'file://{str(test_results_dir)}'
                            }
                        ]
                    }
                }
            }

            settings_file_path = f'{temp_dir.path}/tssc-working/uat/settings.xml'
            run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)
            mvn_mock.assert_called_once_with(
                'clean',
                '-Pintegration-test',
                f'-Dselenium.hub.url={SELENIUM_HUB_URL}',
                f'-Dtarget.base.url={endpoint_url}',
                '-Dcucumber.plugin=html:target/cucumber/cucumber.html,' \
                    'json:target/cucumber/cucumber.json',
                'test',
                '-f', pom_file_path,
                '-s', settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )
