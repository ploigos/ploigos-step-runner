import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.generate_metadata import Maven

def test_pom_file_valid():
    with TempDirectory() as temp_dir:
        temp_dir.write('pom.xml',b'''<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
    <version>42.1</version>
</project>''')
        pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
        results_dir_path = os.path.join(temp_dir.path, 'tssc-results')

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
        factory = TSSCFactory(config, results_dir_path)
        factory.run_step('generate-metadata')

        expected_step_results = {'tssc-results': {'generate-metadata': {'version': '42.1'}}}
        with open(os.path.join(results_dir_path, 'generate-metadata.yml'), 'r') as step_results_file:
            step_results = yaml.safe_load(step_results_file.read())
            assert step_results == expected_step_results
            

def test_pom_file_valid_runtime_config_pom_file():
    config = {
        'tssc-config': {
            'generate-metadata': {
                'implementer': 'Maven'
            }
        }
    }
    factory = TSSCFactory(config)

    with TempDirectory() as temp_dir:
        temp_dir.write('pom.xml',b'''<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
    <version>42.1</version>
</project>''')
        pom_file_path = os.path.join(temp_dir.path, 'pom.xml')
        factory.run_step('generate-metadata', {'pom-file': str(pom_file_path)})

def test_pom_file_missing_version():
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


        with pytest.raises(ValueError):
            factory.run_step('generate-metadata')

def test_default_pom_file_missing():
    config = {
        'tssc-config': {
            'generate-metadata': {
                'implementer': 'Maven'
            }
        }
    }
    factory = TSSCFactory(config)
    with pytest.raises(ValueError):
        factory.run_step('generate-metadata', {'pom-file': 'does-not-exist-pom.xml'})

def test_runtime_pom_file_missing():
    config = {
        'tssc-config': {
            'generate-metadata': {
                'implementer': 'Maven'
            }
        }
    }
    factory = TSSCFactory(config)
    with pytest.raises(ValueError):
        factory.run_step('generate-metadata', {'pom-file': 'does-not-exist-pom.xml'})

def test_config_file_pom_file_missing():
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
    with pytest.raises(ValueError):
        factory.run_step('generate-metadata')
