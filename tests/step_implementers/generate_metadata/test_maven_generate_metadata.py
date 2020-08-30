import os

import unittest
from testfixtures import TempDirectory

from tssc import TSSCFactory
from tssc.step_implementers.generate_metadata import Maven
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

from tests.helpers.test_utils import *

class TestStepImplementerGenerateMetadataMaven(BaseTSSCTestCase):
    def test_pom_file_valid_runtime_config_pom_file(self):
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
                    'generate-metadata': {
                        'implementer': 'Maven'
                    }
                }
            }
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': '42.1'}}}
            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'pom-file': str(pom_file_path)})

    def test_pom_file_valid_old(self):
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
                    'generate-metadata': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': '42.1'}}}

            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results)

    def test_pom_file_valid_with_namespace(self):
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

            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': str(pom_file_path)
                        }
                    }
                }
            }
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': '42.1'}}}

            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results)

    def test_pom_file_missing_version(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('pom.xml',b'''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            config = {
                'tssc-config': {
                    'generate-metadata': {
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
                r"Given pom file does not exist:"):
            factory.run_step('generate-metadata')

    def test_default_pom_file_missing(self):
        config = {
            'tssc-config': {
                'generate-metadata': {
                    'implementer': 'Maven'
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError,
                r"Given pom file does not exist: does-not-exist-pom.xml"):

            factory.config.set_step_config_overrides(
                'generate-metadata',
                {'pom-file': 'does-not-exist-pom.xml'})
            factory.run_step('generate-metadata')

    def test_runtime_pom_file_missing(self):
        config = {
            'tssc-config': {
                'generate-metadata': {
                    'implementer': 'Maven'
                }
            }
        }
        factory = TSSCFactory(config)
        with self.assertRaisesRegex(
                ValueError,
                r"Given pom file does not exist: does-not-exist-pom.xml"):

            factory.config.set_step_config_overrides(
                'generate-metadata',
                {'pom-file': 'does-not-exist-pom.xml'})
            factory.run_step('generate-metadata')

    def test_config_file_pom_file_missing(self):
        config = {
            'tssc-config': {
                'generate-metadata': {
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
                r"Given pom file does not exist: does-not-exist.pom"):
            factory.run_step('generate-metadata')

    def test_config_file_pom_file_none_value(self):
        config = {
            'tssc-config': {
                'generate-metadata': {
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
                r"The runtime step configuration \(\{'pom-file': None\}\) is missing the required configuration keys \(\['pom-file'\]\)"):
            factory.run_step('generate-metadata')
