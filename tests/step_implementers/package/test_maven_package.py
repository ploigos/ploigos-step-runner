import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.package import Maven

from test_utils import *

def test_mvn_quickstart_single_jar_no_pom():
    with TempDirectory() as temp_dir:
        temp_dir.write('src/main/java/com/mycompany/app/App.java',b'''package com.mycompany.app;
public class App {
    public static void main( String[] args ) {
        System.out.println( "Hello World!" );
    }
}''')
        pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
        config = {
            'tssc-config': {
                'package': {
                    'implementer': 'Maven',
                }
            }
        }
        expected_step_results = {
            'tssc-results': {
                'package': {
                    'artifact': os.path.join(temp_dir.path, 'target', 'my-app-1.0-SNAPSHOT.jar')
                }
            }
        }
        factory = TSSCFactory(config)
        with pytest.raises(ValueError):
            factory.run_step('package')

def test_mvn_quickstart_single_jar():
    with TempDirectory() as temp_dir:
        temp_dir.write('src/main/java/com/mycompany/app/App.java',b'''package com.mycompany.app;
public class App {
    public static void main( String[] args ) {
        System.out.println( "Hello World!" );
    }
}''')
        temp_dir.write('pom.xml',b'''<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0-SNAPSHOT</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
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
        expected_step_results = {
            'tssc-results': {
                'package': {
                    'artifact': os.path.join(temp_dir.path, 'target', 'my-app-1.0-SNAPSHOT.jar')
                }
            }
        }
        run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)

def test_mvn_multiple_jars():
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
        temp_dir.write('pom.xml',b'''<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0-SNAPSHOT</version>
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
        with pytest.raises(ValueError):
            factory.run_step('package')

def test_pom_file_valid_old_empty_jar ():
    with TempDirectory() as temp_dir:
        temp_dir.write('pom.xml',b'''<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
    <version>42.1</version>
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
        expected_step_results = {
            'tssc-results': {
                'package': {
                    'artifact': os.path.join(temp_dir.path, 'target', 'my-app-42.1.jar')
                }
            }
        }

        run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)

def test_pom_file_valid_with_namespace_empty_jar ():
    with TempDirectory() as temp_dir:
        temp_dir.write('pom.xml',b'''<?xml version="1.0"?>
<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
  xmlns="http://maven.apache.org/POM/4.0.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
    <version>42.1</version>
</project>''')
        pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
        results_dir_path = os.path.join(temp_dir.path, 'tssc-resutls')

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
        expected_step_results = {
            'tssc-results': {
                'package': {
                    'artifact': os.path.join(temp_dir.path, 'target', 'my-app-42.1.jar')
                }
            }
        }
        run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)

def test_mvn_quickstart_single_jar_java_error():
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
    <version>1.0-SNAPSHOT</version>
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
        with pytest.raises(ValueError):
            factory.run_step('package')

def test_pom_file_missing_version ():
    with TempDirectory() as temp_dir:
        temp_dir.write('pom.xml',b'''<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
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
        with pytest.raises(ValueError):
            factory.run_step('package')

def test_default_pom_file_missing ():
    config = {
        'tssc-config': {
            'package': {
                'implementer': 'Maven'
            }
        }
    }
    factory = TSSCFactory(config)
    with pytest.raises(ValueError):
        factory.run_step('package', {'pom-file': 'does-not-exist-pom.xml'})

def test_runtime_pom_file_missing ():
    config = {
        'tssc-config': {
            'package': {
                'implementer': 'Maven'
            }
        }
    }
    factory = TSSCFactory(config)
    with pytest.raises(ValueError):
        factory.run_step('package', {'pom-file': 'does-not-exist-pom.xml'})

def test_config_file_pom_file_missing ():
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
    with pytest.raises(ValueError):
        factory.run_step('package')

def test_config_file_pom_file_none_value ():
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
    with pytest.raises(ValueError):
        factory.run_step('package')
