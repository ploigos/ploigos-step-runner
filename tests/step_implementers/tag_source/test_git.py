import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.tag_source import Git

def test_tag_source_default():
    config = {
        'tssc-config': {}
    }
    factory = TSSCFactory(config)
    factory.run_step('tag-source')

def test_tag_source_specify_git_implementer():
    config = {
        'tssc-config': {    
            'tag-source': {
                'implementer': 'Git',
                'config': {}
            }
        }
    }
    factory = TSSCFactory(config)
    factory.run_step('tag-source')
