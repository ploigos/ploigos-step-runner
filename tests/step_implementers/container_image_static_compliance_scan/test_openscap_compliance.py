import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.container_image_static_compliance_scan import OpenSCAP

from test_utils import *

def test_container_image_static_compliance_scan_specify_openscap_implementer():
    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {    
                'container-image-static-compliance-scan': {
                    'implementer': 'OpenSCAP',
                    'config': {}
                }
            }
        }
        expected_step_results = {'tssc-results': {'container-image-static-compliance-scan': {}}}

        run_step_test_with_result_validation(temp_dir, 'container-image-static-compliance-scan', config, expected_step_results)
