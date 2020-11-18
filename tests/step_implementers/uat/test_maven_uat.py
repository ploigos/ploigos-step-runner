# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os

from unittest.mock import patch
import sh

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase

from tssc.step_result import StepResult
from tssc.step_implementers.uat import Maven


class TestStepImplementerMavenUat(BaseStepImplementerTestCase):
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
            step_implementer=Maven,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        actual_defaults = Maven.step_implementer_config_defaults()
        expected_defaults = {
            'fail-on-no-tests': True,
            'pom-file': 'pom.xml',
            'report-dir': 'cucumber',
            'target-base-url': None
        }
        self.assertEqual(expected_defaults, actual_defaults)

    def test_required_runtime_step_config_keys(self):
        actual_required_keys = Maven.required_runtime_step_config_keys()
        expected_required_keys = ['fail-on-no-tests', 'pom-file', 'selenium-hub-url', 'report-dir']
        self.assertEqual(expected_required_keys, actual_required_keys)
