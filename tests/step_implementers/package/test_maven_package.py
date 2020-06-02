import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.package import Maven

from test_utils import *

def test_tag_source_specify_git_implementer():
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
        expected_step_results = {'tssc-results': {'package': {}}}

        run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)
