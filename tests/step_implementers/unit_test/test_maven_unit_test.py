import os
from io import IOBase, StringIO

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase

from tssc.config.config import Config
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult
from tssc.step_implementers.unit_test import Maven


class TestStepImplementerMavenUnitTest(BaseStepImplementerTestCase):
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
        defaults = Maven.step_implementer_config_defaults()
        expected_defaults = {
            'fail-on-no-tests': True,
            'pom-file': 'pom.xml'
        }
        self.assertEqual(defaults, expected_defaults)

    def test_required_runtime_step_config_keys(self):
        required_keys = Maven.required_runtime_step_config_keys()
        expected_required_keys = ['fail-on-no-tests','pom-file']
        self.assertEqual(required_keys, expected_required_keys)

