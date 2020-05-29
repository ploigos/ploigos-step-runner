import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.canary_test import Selenium

from test_utils import *

def test_tag_source_specify_selenium_implementer():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {    
                'canary-test': {
                    'implementer': 'Selenium',
                    'config': {}
                }
            }
        }
        expected_step_results = {'tssc-results': {'canary-test': {}}}

        run_step_test_with_result_validation(temp_dir, 'canary-test', config, expected_step_results)
