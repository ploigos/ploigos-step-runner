import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.unit_test import JUnit

from test_utils import *

def test_tag_source_specify_junit_implementer():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {    
                'unit-test': {
                    'implementer': 'JUnit',
                    'config': {}
                }
            }
        }
        expected_step_results = {'tssc-results': {'unit-test': {}}}

        run_step_test_with_result_validation(temp_dir, 'unit-test', config, expected_step_results)
