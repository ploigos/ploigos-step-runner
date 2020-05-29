import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.push_artifacts import NPM

from test_utils import *

def test_tag_source_specify_npm_implementer():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {    
                'push-artifacts': {
                    'implementer': 'NPM',
                    'config': {}
                }
            }
        }
        expected_step_results = {'tssc-results': {'push-artifacts': {}}}

        run_step_test_with_result_validation(temp_dir, 'push-artifacts', config, expected_step_results)
