import os

from testfixtures import TempDirectory

from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from tssc import TSSCFactory


class TestStepImplementerGenerateMetadataMaven(BaseStepImplementerTestCase):
    def test_pom_file_valid_runtime_config_pom_file(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('pom.xml', b'''<project>
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
            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version': {'value': '42.1', 'type': 'str', 'description': ''},
                        },
                    }
                }
            }

            runtime_args = {'pom-file': str(pom_file_path)}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_pom_file_valid_old(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('pom.xml', b'''<project>
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
            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version': {'value': '42.1', 'type': 'str', 'description': ''},
                        },
                    }
                }
            }

            runtime_args = {}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_pom_file_valid_with_namespace(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('pom.xml', b'''<?xml version="1.0"?>
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
            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version': {'value': '42.1', 'type': 'str', 'description': ''},
                        },
                    }
                }
            }

            runtime_args = {}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_pom_file_missing_version(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('pom.xml', b'''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
            pom_file = str(pom_file_path)

            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': pom_file
                        }
                    }
                }
            }

            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': False,
                        'message': f'Given pom file missing version: {pom_file}',
                        'artifacts': {}
                    }
                }
            }
            runtime_args={}
            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_default_pom_file_missing(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Maven'
                    }
                }
            }
            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': False,
                        'message': f'Given pom file does not exist: pom.xml',
                        'artifacts': {}
                    }
                }
            }
            runtime_args = {}
            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_runtime_pom_file_missing(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Maven'
                    }
                }
            }
            pom_file = 'does-not-exist-pom.xml'
            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': False,
                        'message': f'Given pom file does not exist: {pom_file}',
                        'artifacts': {}
                    }
                }
            }
            runtime_args = {'pom-file': pom_file}
            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_config_file_pom_file_missing(self):
        with TempDirectory() as temp_dir:
            pom_file = 'does-not-exist-pom.xml'
            config = {
                'tssc-config': {
                    'generate-metadata': {
                        'implementer': 'Maven',
                        'config': {
                            'pom-file': pom_file
                        }
                    }
                }
            }
            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': False,
                        'message': f'Given pom file does not exist: {pom_file}',
                        'artifacts': {}
                    }
                }
            }
            runtime_args = {}
            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args,
            )

    def test_config_file_pom_file_none_value(self):
        with TempDirectory() as temp_dir:
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
            expected_step_results = {}
            runtime_args = {}
            with self.assertRaisesRegex(
                    AssertionError,
                    r"The runtime step configuration \(\{'pom-file': None\}\) is missing the required configuration keys \(\['pom-file'\]\)"):
                self.run_step_test_with_result_validation(
                    temp_dir=temp_dir,
                    step_name='generate-metadata',
                    config=config,
                    expected_step_results=expected_step_results,
                    runtime_args=runtime_args
                )
