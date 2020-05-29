import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc.step_implementers.linting_static_code_analysis import SonarQube

from test_utils import *

def test_tag_source_specify_sonarqube_implementer():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {    
                'linting-static-code-analysis': {
                    'implementer': 'SonarQube',
                    'config': {}
                }
            }
        }
        expected_step_results = {'tssc-results': {'linting-static-code-analysis': {}}}

        run_step_test_with_result_validation(temp_dir, 'linting-static-code-analysis', config, expected_step_results)
