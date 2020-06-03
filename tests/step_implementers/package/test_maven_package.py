import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.package import Maven

from test_utils import *

def test_package_java_mvn_quickstart_single_jar():
    with TempDirectory() as temp_dir:
        #java_app_class_file = os.path.join(temp_dir.path,"src/main/java/com/mycompany/app/app.java")
        #os.makedirs(java_app_class_file)
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
                    'artifacts': {
                        'my-app-1.0-SNAPSHOT.jar': os.path.join(temp_dir.path, "target", 'my-app-1.0-SNAPSHOT.jar')
                    }
                }
            }
        }

        run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)
