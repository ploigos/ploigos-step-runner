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

#TODO: Mock out pom file, etc for test to pass
    # def test_run_step_pass(self):
    #     with TempDirectory() as temp_dir:
    #         results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
    #         results_file_name = 'tssc-results.yml'
    #         work_dir_path = os.path.join(temp_dir.path, 'working')

    #         step_config = {}

    #         step_implementer = self.create_step_implementer(
    #             step_config=step_config,
    #             step_name='unit-test',
    #             implementer='Maven',
    #             results_dir_path=results_dir_path,
    #             results_file_name=results_file_name,
    #             work_dir_path=work_dir_path,
    #         )

    #         result = step_implementer._run_step()

    #         expected_step_result = StepResult(step_name='unit-test', sub_step_name='Maven', sub_step_implementer_name='Maven')
    #         expected_step_result.add_artifact(name='pom-path', value='pom.xml')
    #         expected_step_result.add_artifact(name='maven unit test results generated using junit', value='42.1.0')

    #         self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())
