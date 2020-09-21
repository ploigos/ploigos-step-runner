import os
import sh
from io import IOBase
from pathlib import Path
from unittest.mock import patch

from testfixtures import TempDirectory

from tssc import TSSCFactory

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.test_utils import run_step_test_with_result_validation, Any

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


class TestStepImplementerPackageMaven(BaseTSSCTestCase):
    @patch('sh.mvn', create=True)
    def test_mvn_quickstart_single_jar_no_pom(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.write('src/main/java/com/mycompany/app/App.java',b'''package com.mycompany.app;
    public class App {
        public static void main( String[] args ) {
            System.out.println( "Hello World!" );
        }
    }''')
            config = {
                'tssc-config': {
                    'package': {
                        'implementer': 'Maven',
                    }
                }
            }
            factory = TSSCFactory(config)
            with self.assertRaisesRegex(
                    ValueError,
                    'Given pom file does not exist: .*'):
                factory.run_step('package')

    @patch('sh.mvn', create=True)
    def test_mvn_quickstart_single_jar(self, mvn_mock):
        artifact_id = 'my-app'
        version = '1.0'
        package = 'jar'
        with TempDirectory() as temp_dir:
            temp_dir.write('src/main/java/com/mycompany/app/App.java',b'''package com.mycompany.app;
    public class App {
        public static void main( String[] args ) {
            System.out.println( "Hello World!" );
        }
    }''')
            temp_dir.write(
                'pom.xml',
                bytes('''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>{artifact_id}</artifactId>
        <version>{version}</version>
        <properties>
            <maven.compiler.source>1.8</maven.compiler.source>
            <maven.compiler.target>1.8</maven.compiler.target>
        </properties>
    </project>'''.format(artifact_id=artifact_id, version=version), 'utf-8')
            )
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'package': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            artifact_file_name = '{artifact_id}-{version}.{package}'.format(
                artifact_id=artifact_id,
                version=version,
                package=package
            )
            expected_step_results = {
                'tssc-results': {
                    'package': {
                        'artifacts': [{
                            'path': os.path.join(
                                temp_dir.path,
                                'target',
                                artifact_file_name
                            ),
                            'artifact-id': artifact_id,
                            'group-id': 'com.mycompany.app',
                            'package-type': package,
                            'pom-path': str(pom_file_path)
                        }]
                    }
                }
            }

            mvn_mock.side_effect = create_mvn_side_effect(pom_file_path,
                                                          'target',
                                                          [artifact_file_name])
            run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)
            settings_file_path = temp_dir.path + "/tssc-working/package/settings.xml"
            mvn_mock.assert_called_once_with(
                'clean',
                'install',
                '-f',
                pom_file_path,
                '-s',
                settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.mvn', create=True)
    def test_mvn_quickstart_no_jar(self, mvn_mock):
        artifact_id = 'my-app'
        version = '1.0'
        package = 'jar'
        with TempDirectory() as temp_dir:
            temp_dir.write('src/main/java/com/mycompany/app/App.java',b'''package com.mycompany.app;
    public class App {
        public static void main( String[] args ) {
            System.out.println( "Hello World!" );
        }
    }''')
            temp_dir.write(
                'pom.xml',
                bytes('''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>{artifact_id}</artifactId>
        <version>{version}</version>
    </project>'''.format(artifact_id=artifact_id, version=version), 'utf-8')
            )
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'package': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            artifact_file_name = '{artifact_id}-{version}.{package}'.format(
                artifact_id=artifact_id,
                version=version,
                package=package
            )
            expected_step_results = {
                'tssc-results': {
                    'package': {
                        'artifacts': [{
                            'path': os.path.join(
                                temp_dir.path,
                                'target',
                                artifact_file_name
                            ),
                            'artifact-id': 'my-app',
                            'group-id': 'com.mycompany.app'
                        }]
                    }
                }
            }

            # NOTE:
            # sort of hacking this test by passing in no artifacts to cause the no artifacts error message
            # because can't figure out how to create a pom that doesn't generate any artifacts
            mvn_mock.side_effect = create_mvn_side_effect(pom_file_path, 'target', [])

            with self.assertRaisesRegex(
                    ValueError,
                    'pom resulted in 0 with expected artifact extensions (.*), this is unsupported'):
                run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)

    @patch('sh.mvn', create=True)
    def test_mvn_multiple_jars(self, mvn_mock):
        artifact_id = 'my-app'
        version = '1.0'
        package = 'jar'
        with TempDirectory() as temp_dir:
            temp_dir.write('src/main/java/com/mycompanya/app/App.java',b'''package com.mycompanya.app;
    public class App {
        public static void main( String[] args ) {
            System.out.println( "Hello World!" );
        }
    }''')
            temp_dir.write('src/main/java/com/mycompanyb/app/App.java',b'''package com.mycompanyb.app;
    public class App {
        public static void main( String[] args ) {
            System.out.println( "Hello World!" );
        }
    }''')
            temp_dir.write(
                'pom.xml',
                bytes('''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>{artifact_id}</artifactId>
        <version>{version}</version>
        <properties>
            <maven.compiler.source>1.8</maven.compiler.source>
            <maven.compiler.target>1.8</maven.compiler.target>
        </properties>
        <build>
            <plugins>
                <plugin>
                    <artifactId>maven-assembly-plugin</artifactId>
                    <executions>
                        <execution>
                            <id>jar1</id>
                            <phase>package</phase>
                            <goals>
                                <goal>single</goal>
                            </goals>
                            <configuration>
                                <archive>
                                    <manifest>
                                        <mainClass>com.mycompanya.app.App</mainClass>
                                    </manifest>
                                </archive>
                                <descriptorRefs>
                                    <descriptorRef>jar-with-dependencies</descriptorRef>
                                </descriptorRefs>
                                <finalName>companya</finalName>
                            </configuration>
                        </execution>
                        <execution>
                            <id>jar2</id>
                            <phase>package</phase>
                            <goals>
                                <goal>single</goal>
                            </goals>
                            <configuration>
                                <archive>
                                    <manifest>
                                        <mainClass>com.mycompanyb.app.App</mainClass>
                                    </manifest>
                                </archive>
                                <descriptorRefs>
                                    <descriptorRef>jar-with-dependencies</descriptorRef>
                                </descriptorRefs>
                                <finalName>companyb</finalName>
                            </configuration>
                        </execution>
                    </executions>
                </plugin>
            </plugins>
        </build>
    </project>'''.format(artifact_id=artifact_id, version=version), 'utf-8')
            )
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'package': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            factory = TSSCFactory(config)
            artifact_file_name = '{artifact_id}-{version}.{package}'.format(
                artifact_id=artifact_id,
                version=version,
                package=package
            )

            mvn_mock.side_effect = create_mvn_side_effect(
                pom_file_path,
                'target',
                [
                    'companya-{version}-jar-with-dependencies.jar'.format(version=version),
                    'companyb-{version}-jar-with-dependencies.jar'.format(version=version),
                    artifact_file_name
                ]
            )

            with self.assertRaisesRegex(
                    ValueError,
                    'pom resulted in multiple artifacts with expected artifact extensions (.*), this is unsupported'):
                factory.run_step('package')

    @patch('sh.mvn', create=True)
    def test_pom_file_valid_old_empty_jar(self, mvn_mock):
        artifact_id = 'my-app'
        version = '42.1'
        package = 'jar'
        with TempDirectory() as temp_dir:
            temp_dir.write(
                'pom.xml',
                bytes('''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>{artifact_id}</artifactId>
        <version>{version}</version>
    </project>'''.format(artifact_id=artifact_id, version=version), 'utf-8')
            )
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'package': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            artifact_file_name = '{artifact_id}-{version}.{package}'.format(
                artifact_id=artifact_id,
                version=version,
                package=package
            )
            expected_step_results = {
                'tssc-results': {
                    'package': {
                        'artifacts': [{
                            'path': os.path.join(temp_dir.path, 'target', artifact_file_name),
                            'artifact-id': artifact_id,
                            'group-id': 'com.mycompany.app',
                            'package-type': package,
                            'pom-path': str(pom_file_path)
                        }]
                    }
                }
            }

            mvn_mock.side_effect = create_mvn_side_effect(pom_file_path, 'target', [artifact_file_name])
            run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)
            settings_file_path = temp_dir.path + "/tssc-working/package/settings.xml"
            mvn_mock.assert_called_once_with(
                'clean',
                'install',
                '-f',
                pom_file_path,
                '-s',
                settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.mvn', create=True)
    def test_pom_file_valid_with_namespace_empty_jar(self, mvn_mock):
        artifact_id = 'my-app'
        version = '42.1'
        package = 'jar'
        with TempDirectory() as temp_dir:
            temp_dir.write(
                'pom.xml',
                bytes('''<?xml version="1.0"?>
    <project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
      xmlns="http://maven.apache.org/POM/4.0.0"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>{artifact_id}</artifactId>
        <version>{version}</version>
    </project>'''.format(artifact_id=artifact_id, version=version), 'utf-8')
            )
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            config = {
                'tssc-config': {
                    'package': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            artifact_file_name = '{artifact_id}-{version}.{package}'.format(
                artifact_id=artifact_id,
                version=version,
                package=package
            )
            expected_step_results = {
                'tssc-results': {
                    'package': {
                        'artifacts': [{
                            'path': os.path.join(temp_dir.path, 'target', artifact_file_name),
                            'artifact-id': artifact_id,
                            'group-id': 'com.mycompany.app',
                            'package-type': package,
                            'pom-path': str(pom_file_path)
                        }]
                    }
                }
            }
            mvn_mock.side_effect = create_mvn_side_effect(pom_file_path, 'target', [artifact_file_name])
            run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)
            settings_file_path = temp_dir.path + "/tssc-working/package/settings.xml"
            mvn_mock.assert_called_once_with(
                'clean',
                'install',
                '-f',
                pom_file_path,
                '-s',
                settings_file_path,
                _out=Any(IOBase),
                _err=Any(IOBase)
            )

    @patch('sh.mvn', create=True, side_effect = sh.ErrorReturnCode('mvn clean install', b'mock out', b'Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.1:compile (default-compile) on project my-app: Compilation failure: Compilation failure'))
    def test_mvn_quickstart_single_jar_java_error(self, mvn_mock):
        with TempDirectory() as temp_dir:
            temp_dir.write('src/main/java/com/mycompany/app/App.java',b'''package com.mycompany.app;
    public class Fail {
        public static void main( String[] args ) {
            System.out.println( "Hello World!" );
        }
    }''')
            temp_dir.write('pom.xml',b'''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>1.0</version>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'package': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            factory = TSSCFactory(config)
            with self.assertRaisesRegex(
                    RuntimeError,
                    'Error invoking mvn:.*'):
                factory.run_step('package')

    @patch('sh.mvn', create=True)
    def test_default_pom_file_missing(self, mvn_mock):
        config = {
            'tssc-config': {
                'package': {
                    'implementer': 'Maven'
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError,
                "Given pom file does not exist: pom.xml"):
            factory.run_step('package')

    @patch('sh.mvn', create=True)
    def test_runtime_pom_file_missing(self, mvn_mock):
        config = {
            'tssc-config': {
                'package': {
                    'implementer': 'Maven'
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError,
                "Given pom file does not exist: does-not-exist-pom.xml"):

            factory.config.set_step_config_overrides(
                'package',
                {'pom-file': 'does-not-exist-pom.xml'})
            factory.run_step('package')

    @patch('sh.mvn', create=True)
    def test_config_file_pom_file_missing(self, mvn_mock):
        config = {
            'tssc-config': {
                'package': {
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
            factory.run_step('package')

    @patch('sh.mvn', create=True)
    def test_config_file_pom_file_none_value(self, mvn_mock):
        config = {
            'tssc-config': {
                'package': {
                    'implementer': 'Maven',
                    'config': {
                        'pom-file': None
                    }
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                AssertionError,
                r"The runtime step configuration \(\{'pom-file': None, 'artifact-extensions': \['jar', 'war', 'ear'\], 'artifact-parent-dir': 'target'\}\) is missing the required configuration keys \(\['pom-file'\]\)"):
            factory.run_step('package')

    @patch('sh.mvn', create=True, side_effect = sh.ErrorReturnCode('mvn clean install', b'mock out', b'mock error'))
    def test_mvn_error_return_code(self, mvn_mock):
        artifact_id = 'my-app'
        version = '1.0'
        package = 'jar'
        with TempDirectory() as temp_dir:
            temp_dir.write('src/main/java/com/mycompany/app/App.java',b'''package com.mycompany.app;
    public class App {
        public static void main( String[] args ) {
            System.out.println( "Hello World!" );
        }
    }''')
            temp_dir.write(
                'pom.xml',
                bytes('''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>{artifact_id}</artifactId>
        <version>{version}</version>
        <properties>
            <maven.compiler.source>1.8</maven.compiler.source>
            <maven.compiler.target>1.8</maven.compiler.target>
        </properties>
    </project>'''.format(artifact_id=artifact_id, version=version), 'utf-8')
            )
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            config = {
                'tssc-config': {
                    'package': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            artifact_file_name = '{artifact_id}-{version}.{package}'.format(
                artifact_id=artifact_id,
                version=version,
                package=package
            )
            expected_step_results = {
                'tssc-results': {
                    'package': {
                        'artifacts': [{
                            'path': os.path.join(
                                temp_dir.path,
                                'target',
                                artifact_file_name
                            ),
                            'artifact-id': artifact_id,
                            'group-id': 'com.mycompany.app',
                            'pom-path': str(pom_file_path),
                            'package-type': 'jar'
                        }]
                    }
                }
            }

            with self.assertRaisesRegex(
                    RuntimeError,
                    'Error invoking mvn:.*'):
                run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)
