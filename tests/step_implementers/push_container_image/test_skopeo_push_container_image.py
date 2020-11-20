# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
from io import IOBase
from unittest.mock import patch
from pathlib import Path

import sh
from testfixtures import TempDirectory
from tssc.step_implementers.push_container_image import Skopeo
from tssc.step_result import StepResult

from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from tests.helpers.test_utils import Any


class TestStepImplementerSkopeoSourceBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Skopeo,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    # TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = Skopeo.step_implementer_config_defaults()
        expected_defaults = {
            'containers-config-auth-file': os.path.join(Path.home(), '.skopeo-auth.json'),
            'dest-tls-verify': 'true',
            'src-tls-verify': 'true'
        }
        self.assertEqual(defaults, expected_defaults)

    def test_required_runtime_step_config_keys(self):
        required_keys = Skopeo.required_runtime_step_config_keys()
        expected_required_keys = [
            'containers-config-auth-file',
            'destination-url',
            'src-tls-verify',
            'dest-tls-verify',
            'service-name',
            'application-name',
            'organization'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_runtime_step_config_valid(self):
        step_config = {
            'containers-config-auth-file':'notused',
            'destination-url':'notused',
            'src-tls-verify':'notused',
            'dest-tls-verify':'notused',
            'service-name':'notused',
            'application-name':'notused',
            'organization':'notused'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='push-container-image',
            implementer='Skopeo'
        )

        step_implementer._validate_runtime_step_config(step_config)

    def test__validate_runtime_step_config_invalid(self):
        step_config = {
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='push-container-image',
            implementer='Skopeo'
        )
        with self.assertRaisesRegex(
                AssertionError,
                "The runtime step configuration .*"
        ):
            step_implementer._validate_runtime_step_config(step_config)
