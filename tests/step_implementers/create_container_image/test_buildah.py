import os

import pytest
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.create_container_image import Buildah

from test_utils import *

def test_create_container_image_default():

    passed = False
    with TempDirectory() as temp_dir:
        try:
            config = {
                'tssc-config': {}
            }
            expected_step_results = {'tssc-results': {'create-container-image': {'image_tag': ''}}}

            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
        except ValueError as err:
             if (err.__str__() == 'Key (tag) must have non-empty value in the step configuration'):
                passed = True

    assert passed

def test_create_container_image_specify_buildah_implementer():

    passed = False
    with TempDirectory() as temp_dir:
        try:
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {}
                    }
                }
            }
            expected_step_results = {'tssc-results': {'create-container-image': {'image_tag': ''}}}

            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
        except ValueError as err:
            if (err.__str__() == 'Key (tag) must have non-empty value in the step configuration'):
                passed = True

    assert passed

def test_create_container_image_specify_buildah_implementer_missing_config():

    passed = False
    with TempDirectory() as temp_dir:
        try:
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tag' : 'localhost:test',
                            'tlsverify' : None,
                        }
                    }
                }
            }
            expected_step_results = {'tssc-results': {'create-container-image': {'image_tag': 'localhost:test'}}}

            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
        except ValueError as err:
            if (err.__str__()  == 'Key (tlsverify) must have non-empty value in the step configuration'):
                passed = True

    assert passed

def test_create_container_image_specify_buildah_implementer_with_tag_no_dockerfile():

    passed = False
    with TempDirectory() as temp_dir:
        try:
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tag' : 'localhost:test',
                            'context' : temp_dir.path
                        }
                    }
                }
            }
            expected_step_results = {'tssc-results': {'create-container-image': {'image_tag': 'localhost:test'}}}

            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
        except ValueError as err:
            if (err.__str__().startswith('Image specification file does not exist in location')):
                passed = True

    assert passed

def test_create_container_image_specify_buildah_implementer_with_tag_invalid_dockerfile():

    passed = False
    with TempDirectory() as temp_dir:
        temp_dir.write('Dockerfile',b'Invalid Dockerfile')
        try:
            config = {
                'tssc-config': {    
                    'create-container-image': {
                        'implementer': 'Buildah',
                        'config': {
                            'tag' : 'localhost:test',
                            'context' : temp_dir.path
                        }
                    }
                }
            }
            expected_step_results = {'tssc-results': {'create-container-image': {'image_tag': 'localhost:test'}}}

            run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
        except RuntimeError as err:
            if (err.__str__().startswith('Issue invoking')):
                passed = True

    assert passed

def test_create_container_image_specify_buildah_implementer_with_tag_valid_dockerfile():

    with TempDirectory() as temp_dir:
        temp_dir.write('Dockerfile',b'FROM registry.access.redhat.com/ubi8:latest')
        config = {
            'tssc-config': {    
                'create-container-image': {
                    'implementer': 'Buildah',
                    'config': {
                        'tag' : 'localhost:test',
                        'context' : temp_dir.path
                    }
                }
            }
        }
        expected_step_results = {'tssc-results': {'create-container-image': {'image_tag': 'localhost:test'}}}
        run_step_test_with_result_validation(temp_dir, 'create-container-image', config, expected_step_results)
