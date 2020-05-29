import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.uat import Cucumber

from test_utils import *

def test_tag_source_specify_cucumber_implementer():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {    
                'uat': {
                    'implementer': 'Cucumber',
                    'config': {}
                }
            }
        }
        expected_step_results = {'tssc-results': {'uat': {}}}

        run_step_test_with_result_validation(temp_dir, 'uat', config, expected_step_results)
