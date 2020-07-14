import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.push_container_image import Skopeo

from test_utils import *

def test_create_container_image_default_missing_args():

    passed = False
    with TempDirectory() as temp_dir:
        try:
            config = {
                'tssc-config': {}
            }
            expected_step_results = {'tssc-results': {'push-container-image': {'image_tag': ''}}}

            run_step_test_with_result_validation(temp_dir, 'push-container-image', config, expected_step_results)
        except ValueError as err:
             if (err.__str__() == 'Key (source) must have non-empty value in the step configuration' or
                 err.__str__() == 'Key (destination) must have non-empty value in the step configuration'):
                passed = True

    assert passed

def test_push_container_image_specify_skopeo_implementer_missing_args():

    passed = False
    with TempDirectory() as temp_dir:
        try:
            config = {
                'tssc-config': {    
                    'push-container-image': {
                        'implementer': 'Skopeo',
                        'config': {}
                    }
                }
            }
            expected_step_results = {'tssc-results': {'push-container-image': {'image_tag': ''}}}

            run_step_test_with_result_validation(temp_dir, 'push-container-image', config, expected_step_results)
        except ValueError as err:
             if (err.__str__() == 'Key (source) must have non-empty value in the step configuration' or
                 err.__str__() == 'Key (destination) must have non-empty value in the step configuration'):
                passed = True

    assert passed

def test_create_container_image_specify_skopeo_implementer_invalid_arguments():

    passed = False
    with TempDirectory() as temp_dir:
        try:
            config = {
                'tssc-config': {    
                    'push-container-image': {
                        'implementer': 'Skopeo',
                        'config': {
                            'source' : 'bogus-transport://quay.io/tssc/tssc-base',
                            'destination' : 'docker-archive:' + temp_dir.path + '/image.tar' 
                        }
                    }
                }
            }
            expected_step_results = {'tssc-results': {'push-container-image': {'image_tag': 'docker-archive:' + temp_dir.path + '/image.tar'}}}

            run_step_test_with_result_validation(temp_dir, 'push-container-image', config, expected_step_results)
        except RuntimeError as err:
            if (err.__str__().startswith('Error invoking')):
                passed = True

    assert passed


def test_create_container_image_specify_skopeo_implementer_valid_arguments():

    with TempDirectory() as temp_dir:
        config = {
            'tssc-config': {    
                'push-container-image': {
                    'implementer': 'Skopeo',
                    'config': {
                        'source' : 'docker://quay.io/tssc/tssc-base:latest',
                        'destination' : 'docker-archive:' + temp_dir.path + '/image.tar' 
                    }
                }
            }
        }
        expected_step_results = {'tssc-results': {'push-container-image': {'image_tag': 'docker-archive:' + temp_dir.path + '/image.tar'}}}
        run_step_test_with_result_validation(temp_dir, 'push-container-image', config, expected_step_results)
