import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.tag_source import Git

from test_utils import *

def test_tag_source_default():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {}
        }
        expected_step_results = {'tssc-results': {'tag-source': {}}}

        run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results)

def test_tag_source_specify_git_implementer():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {    
                'tag-source': {
                    'implementer': 'Git',
                    'config': {}
                }
            }
        }
        expected_step_results = {'tssc-results': {'tag-source': {}}}

        run_step_test_with_result_validation(temp_dir, 'tag-source', config, expected_step_results)
