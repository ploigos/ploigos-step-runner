import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.package import NPM

from test_utils import *

def test_tag_source_specify_git_implementer():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {    
                'package': {
                    'implementer': 'NPM',
                    'config': {}
                }
            }
        }
        expected_step_results = {'tssc-results': {'package': {}}}

        run_step_test_with_result_validation(temp_dir, 'package', config, expected_step_results)
