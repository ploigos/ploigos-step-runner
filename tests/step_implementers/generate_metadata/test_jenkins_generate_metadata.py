

from mock import patch
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.generate_metadata import Jenkins
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestStepImplementerJenkinsGenerateMetadataBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Jenkins,
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Jenkins',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

class TestStepImplementerJenkinsGenerateMetadata_misc(TestStepImplementerJenkinsGenerateMetadataBase):
    def test_step_implementer_config_defaults(self):
        defaults = Jenkins.step_implementer_config_defaults()
        expected_defaults = {
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Jenkins._required_config_or_result_keys()
        expected_required_keys = [
        ]
        self.assertEqual(required_keys, expected_required_keys)

@patch('os.environ.get')
class TestStepImplementerJenkinsGenerateMetadata_run_step(TestStepImplementerJenkinsGenerateMetadataBase):
    def test_success_release_branch_default_release_branch_regexes(self, mock_os_env_get):
        with TempDirectory() as temp_dir:
            # setup
            step_config = {
                'repo-root': temp_dir.path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config
            )

            # setup mocks
            mock_os_env_get.return_value = '42'

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Jenkins',
                sub_step_implementer_name='Jenkins'
            )
            expected_step_result.add_artifact(
                name='workflow-run-num',
                value='42',
                description='Incremental workflow run number'
            )

            self.assertEqual(actual_step_result, expected_step_result)
