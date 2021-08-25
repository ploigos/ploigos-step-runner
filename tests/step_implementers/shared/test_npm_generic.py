
import os
from pathlib import Path
# from shutil import copyfile
from unittest.mock import PropertyMock, patch
from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from ploigos_step_runner.config.config import Config
from ploigos_step_runner.step_implementers.shared.npm_generic import NpmGeneric
# from ploigos_step_runner.utils.file import create_parent_dir
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


@patch("ploigos_step_runner.StepImplementer.__init__")
class TestStepImplementerSharedNpmGeneric___init__(BaseStepImplementerTestCase):

    def test_no_environment_no_npm_args(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        step_implementer = NpmGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        self.assertIsNone(step_implementer._NpmGeneric__npm_args)
        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None
        )

    def test_with_environment_no_npm_args(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        step_implementer = NpmGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='test-env'
        )

        self.assertIsNone(step_implementer._NpmGeneric__npm_args)
        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='test-env'
        )

    def test_no_environment_with_npm_args(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        step_implementer = NpmGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            npm_args=['fake-arg']
        )

        self.assertEqual(
            step_implementer._NpmGeneric__npm_args,
            ['fake-arg']
        )
        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None
        )

class TestStepImplementerSharedNpmGeneric_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            NpmGeneric.step_implementer_config_defaults(),
            {
                'package-file': 'package.json',
            }
        )

class TestStepImplementerSharedNpmGeneric__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            NpmGeneric._required_config_or_result_keys(),
            [
                'package-file',
                'npm-args'
            ]
        )

class BaseTestStepImplementerSharedNpmGeneric(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=NpmGeneric,
            step_config=step_config,
            step_name='foo',
            implementer='NpmGeneric',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

@patch("ploigos_step_runner.StepImplementer._validate_required_config_or_previous_step_result_artifact_keys")
class TestStepImplementerSharedNpmGeneric__validate_required_config_or_previous_step_result_artifact_keys(
    BaseTestStepImplementerSharedNpmGeneric
):
    def test_valid(self, mock_super_validate):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            package_file_path = os.path.join(test_dir.path, 'package.json')
            step_config = {
                'package-file': package_file_path,
                'npm-run-scripts': ['fake-script']
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            Path(package_file_path).touch()
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once_with()

    def test_package_file_does_not_exist(self, mock_super_validate):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            package_file_path = '/does/not/exist/package.json'
            step_config = {
                'package-file': package_file_path,
                'npm-run-scripts': 'fake-arg'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                AssertionError,
                rf'Given npm package file \(package-file\) does not exist: {package_file_path}'
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
                mock_super_validate.assert_called_once_with()

class TestStepImplementerSharedNpmGeneric_config(
    BaseTestStepImplementerSharedNpmGeneric
):
    def test_use_object_property_no_config_value(self):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = None

        step_implementer = NpmGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            npm_args=['run fake:script']
        )

        self.assertEqual(
            step_implementer.npm_args,
            ['run fake:script']
        )

    def test_use_object_property_with_config_value(self):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        step_config = {
            'npm-args': ['config-value-fake-arg']
        }
        config = Config({
            Config.CONFIG_KEY: {
                'foo': [
                    {
                        'implementer': 'NpmGeneric',
                        'config': step_config
                    }
                ]

            }
        })

        step_implementer = NpmGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            npm_args=['object-property-fake-arg']
        )

        self.assertEqual(
            step_implementer.npm_args,
            ['object-property-fake-arg']
        )

    def test_use_configured_npm_args(self):
        parent_work_dir_path = '/fake/path'
        step_config = {
            'npm-args': ['config-value-npm-args']
        }

        step_implementer = self.create_step_implementer(
            step_config=step_config,
            parent_work_dir_path=parent_work_dir_path,
        )

        self.assertEqual(
            step_implementer.npm_args,
            ['config-value-npm-args']
        )

@patch('ploigos_step_runner.step_implementers.shared.npm_generic.run_npm')
@patch.object(
    NpmGeneric,
    'npm_args',
    new_callable=PropertyMock,
    return_value=['fake-arg']
)

class TestStepImplementerSharedNpmGeneric__run_npm_step(BaseTestStepImplementerSharedNpmGeneric):
    def test_defaults(self, mock_args, mock_run_npm):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            package_file_path = os.path.join(test_dir.path, 'package.json')
            step_config = {
                'package-file': package_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            npm_output_file_path = os.path.join(test_dir.path, 'npm-output.txt')
            step_implementer._run_npm_step(
                npm_output_file_path=npm_output_file_path
            )

            mock_run_npm.assert_called_with(
                npm_output_file_path=npm_output_file_path,
                npm_args=['fake-arg']
                )

@patch.object(NpmGeneric, '_run_npm_step')
@patch.object(NpmGeneric, 'write_working_file', return_value='/mock/npm_output.txt')
class TestStepImplementerSharedNpmGeneric__run_step(
    BaseTestStepImplementerSharedNpmGeneric):
    def test_success(self, mock_write_working_file, mock_run_npm_step):
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
                sub_step_name='NpmGeneric',
                sub_step_implementer_name='NpmGeneric'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from npm.",
                name='npm-output',
                value='/mock/npm_output.txt'
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_run_npm_step.assert_called_with(
                npm_output_file_path='/mock/npm_output.txt'
            )

    def test_fail(self, mock_write_working_file, mock_run_npm_step):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step with mock failure
            mock_run_npm_step.side_effect = StepRunnerException('Mock error running npm')
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='foo',
                sub_step_name='NpmGeneric',
                sub_step_implementer_name='NpmGeneric'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from npm.",
                name='npm-output',
                value='/mock/npm_output.txt'
            )
            expected_step_result.message = "Error running npm. " \
                "More details maybe found in 'npm-output' report artifact: "\
                "Mock error running npm"
            expected_step_result.success = False

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_npm_step.assert_called_with(
                npm_output_file_path='/mock/npm_output.txt'
            )
