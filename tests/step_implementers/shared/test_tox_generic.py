import os
from pathlib import Path
from unittest.mock import PropertyMock, patch
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import WorkflowResult
from ploigos_step_runner.config import Config
from ploigos_step_runner.step_implementers.shared.tox_generic import ToxGeneric
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase

@patch("ploigos_step_runner.step_implementer.StepImplementer.__init__")
class TestStepImplementerSharedToxGeneric___init__(BaseStepImplementerTestCase):

    def test_no_environment_no_tox_args(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        step_implementer = ToxGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        self.assertIsNone(step_implementer._ToxGeneric__tox_env)
        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None
        )

    def test_with_environment_no_tox_args(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        step_implementer = ToxGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='fake-env'
        )

        self.assertIsNone(step_implementer._ToxGeneric__tox_env)
        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='fake-env'
        )

    def test_no_environment_with_tox_args(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        step_implementer = ToxGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            tox_env='fake-env'
        )

        self.assertEqual(
            step_implementer._ToxGeneric__tox_env,
            'fake-env'
        )
        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None
        )

class TestStepImplementerSharedToxGeneric_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            ToxGeneric.step_implementer_config_defaults(),
            {
                'tox-config': 'tox.ini',
                'quiet': True
            }
        )

class TestStepImplementerSharedToxGeneric__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            ToxGeneric._required_config_or_result_keys(),
            [
                'tox-config',
                'tox-env'
            ]
        )

class BaseTestStepImplementerSharedToxGeneric(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=ToxGeneric,
            step_config=step_config,
            step_name='foo',
            implementer='ToxGeneric',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

@patch("ploigos_step_runner.step_implementer.StepImplementer._validate_required_config_or_previous_step_result_artifact_keys")
class TestStepImplementerSharedToxGeneric__validate_required_config_or_previous_step_result_artifact_keys(
    BaseTestStepImplementerSharedToxGeneric
):
    def test_valid(self, mock_super_validate):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            tox_config_path = os.path.join(test_dir.path, 'tox.ini')
            step_config = {
                'tox-config': tox_config_path,
                'tox-env': 'fake-env'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            Path(tox_config_path).touch()
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once_with()

    def test_package_file_does_not_exist(self, mock_super_validate):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            tox_config_path = '/does/not/exist/tox.ini'
            step_config = {
                'tox-config': tox_config_path,
                'tox-env': 'fake-env'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                AssertionError,
                rf'Given tox config file \(tox-config\) does not exist: {tox_config_path}'
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
                mock_super_validate.assert_called_once_with()

class TestStepImplementerSharedToxGeneric_config(
    BaseTestStepImplementerSharedToxGeneric
):
    def test_use_object_property_no_config_value(self):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = None

        step_implementer = ToxGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            tox_env='test'
        )

        self.assertEqual(
            step_implementer.tox_env,
            'test'
        )

    def test_use_object_property_with_config_value(self):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        step_config = {
            'tox-env': 'config-value-fake-env'
        }
        config = Config({
            Config.CONFIG_KEY: {
                'foo': [
                    {
                        'implementer': 'ToxGeneric',
                        'config': step_config
                    }
                ]

            }
        })

        step_implementer = ToxGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            tox_env='object-property-fake-env'
        )

        self.assertEqual(
            step_implementer.tox_env,
            'object-property-fake-env'
        )

    def test_use_configured_tox_args(self):
        parent_work_dir_path = '/fake/path'
        step_config = {
            'tox-env': 'config-value-tox-env'
        }

        step_implementer = self.create_step_implementer(
            step_config=step_config,
            parent_work_dir_path=parent_work_dir_path,
        )

        self.assertEqual(
            step_implementer.tox_env,
            'config-value-tox-env'
        )



@patch('ploigos_step_runner.step_implementers.shared.tox_generic.run_tox')
@patch.object(
    ToxGeneric,
    'tox_env',
    new_callable=PropertyMock,
    return_value='fake-env'
)
class TestStepImplementerSharedToxGeneric__run_tox_step(BaseTestStepImplementerSharedToxGeneric):
    def test_defaults(self, mock_args, mock_run_tox):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            tox_config_file = os.path.join(test_dir.path, 'tox.ini')
            step_config = {
                'tox-config': tox_config_file
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            tox_output_file_path = os.path.join(test_dir.path, 'tox-output.txt')
            step_implementer._run_tox_step(
                tox_output_file_path=tox_output_file_path
            )

            mock_run_tox.assert_called_with(
                tox_output_file_path=tox_output_file_path,
                tox_args=('-q', '-e', 'fake-env',)
            )

    def test_disable_quiet(self, mock_args, mock_run_tox):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            tox_config_file = os.path.join(test_dir.path, 'tox.ini')
            step_config = {
                'tox-config': tox_config_file,
                'quiet': False
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            tox_output_file_path = os.path.join(test_dir.path, 'tox-output.txt')
            step_implementer._run_tox_step(
                tox_output_file_path=tox_output_file_path
            )

            mock_run_tox.assert_called_with(
                tox_output_file_path=tox_output_file_path,
                tox_args=('-e', 'fake-env',)
            )


@patch.object(ToxGeneric, '_run_tox_step')
@patch.object(ToxGeneric, 'write_working_file', return_value='/mock/tox_output.txt')
class TestStepImplementerSharedToxGeneric__run_step(
    BaseTestStepImplementerSharedToxGeneric):
    def test_success(self, mock_write_working_file, mock_run_tox_step):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='foo',
                sub_step_name='ToxGeneric',
                sub_step_implementer_name='ToxGeneric'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from tox.",
                name='tox-output',
                value='/mock/tox_output.txt'
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_run_tox_step.assert_called_with(
                tox_output_file_path='/mock/tox_output.txt'
            )

    def test_fail(self, mock_write_working_file, mock_run_tox_step):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step with mock failure
            mock_run_tox_step.side_effect = StepRunnerException('Mock error running tox')
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='foo',
                sub_step_name='ToxGeneric',
                sub_step_implementer_name='ToxGeneric'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from tox.",
                name='tox-output',
                value='/mock/tox_output.txt'
            )
            expected_step_result.message = "Error running tox. " \
                "More details maybe found in 'tox-output' report artifact: "\
                "Mock error running tox"
            expected_step_result.success = False

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_tox_step.assert_called_with(
                tox_output_file_path='/mock/tox_output.txt'
            )
