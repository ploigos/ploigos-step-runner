# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.step_implementers.validate_environment_configuration import \
    Configlint
from ploigos_step_runner.step_result import StepResult


class TestStepImplementerConfiglint(BaseStepImplementerTestCase):
    @staticmethod
    def create_config_lint_side_effect(
            config_lint_stdout="",
            config_lint_stderr="",
            config_lint_fail=False
    ):
        def config_lint_side_effect(*args, **kwargs):
            kwargs['_out'](config_lint_stdout)
            kwargs['_err'](config_lint_stderr)

            if config_lint_fail:
                raise sh.ErrorReturnCode_255(
                    'config-lint',
                    bytes(config_lint_stdout, 'utf-8'),
                    bytes(config_lint_stderr, 'utf-8')
                )

        return config_lint_side_effect

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
            step_implementer=Configlint,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    # TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = Configlint.step_implementer_config_defaults()
        expected_defaults = {
            'rules': './config-lint.rules'
        }
        self.assertEqual(expected_defaults, defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Configlint._required_config_or_result_keys()
        expected_required_keys = [
            'configlint-yml-path'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    @patch('sh.config_lint', create=True)
    def test_run_step_fail_bad_yml_path(self, config_lint_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            test_file_name = 'rules'
            test_file_path = os.path.join(temp_dir.path, test_file_name)
            temp_dir.write(test_file_path, b'ignored')
            step_config = {
                'rules': test_file_path,
                'configlint-yml-path': 'invalid_file'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='validate-environment-configuration',
                implementer='Configlint',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='validate-environment-configuration',
                sub_step_name='Configlint',
                sub_step_implementer_name='Configlint'
            )

            expected_step_result.success = False
            expected_step_result.message = 'File specified in configlint-yml-path not found: invalid_file'
            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())

    @patch('sh.config_lint', create=True)
    def test_run_step_fail_bad_rule_path(self, config_lint_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            test_file_name = 'rules'
            test_file_path = os.path.join(temp_dir.path, test_file_name)
            temp_dir.write(test_file_path, b'ignored')
            step_config = {
                'configlint-yml-path': test_file_path,
                'rules': 'invalid_file'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='validate-environment-configuration',
                implementer='Configlint',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='validate-environment-configuration',
                sub_step_name='Configlint',
                sub_step_implementer_name='Configlint'
            )

            expected_step_result.success = False
            expected_step_result.message = 'File specified in rules not found: invalid_file'
            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())

    @patch('sh.config_lint', create=True)
    def test_run_step_pass_prev_step(self, config_lint_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            test_file_name = 'rules'
            test_file_path = os.path.join(temp_dir.path, test_file_name)
            temp_dir.write(test_file_path, b'ignored')
            step_config = {
                'rules': test_file_path,
            }

            artifact_config = {
                'configlint-yml-path': {'value': f'{test_file_path}'}
            }
            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='validate-environment-configuration',
                implementer='Configlint',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='validate-environment-configuration',
                sub_step_name='Configlint',
                sub_step_implementer_name='Configlint'
            )

            expected_step_result.add_artifact(
                name='configlint-result-set',
                value=f'{work_dir_path}/validate-environment-configuration/configlint_results_file.txt'
            )
            expected_step_result.add_artifact(
                name='configlint-yml-path',
                value=test_file_path
            )
            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())

    @patch('sh.config_lint', create=True)
    def test_run_step_fail_scan(self, configlint_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            file_to_validate_contents = 'notused'
            temp_dir.write('config-file-to-validate.yml', file_to_validate_contents.encode())
            file_to_validate_file_path = str(os.path.join(temp_dir.path, 'config-file-to-validate.yml'))

            # write config-lint rules file
            configlint_rules_content = 'not used'
            config_lint_rules_file_name = 'config-lint-test-rules.yml'
            temp_dir.write(config_lint_rules_file_name, configlint_rules_content.encode())
            config_lint_rules_file_path = os.path.join(temp_dir.path, config_lint_rules_file_name)

            step_config = {
                'configlint-yml-path': file_to_validate_file_path,
                'rules': config_lint_rules_file_path
            }

            configlint_mock.side_effect = \
                TestStepImplementerConfiglint.create_config_lint_side_effect(
                    config_lint_fail=True
                )

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='validate-environment-configuration',
                implementer='Configlint',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='validate-environment-configuration',
                sub_step_name='Configlint',
                sub_step_implementer_name='Configlint'
            )

            expected_step_result.success = False
            expected_step_result.message = 'Failed config-lint scan.'
            expected_step_result.add_artifact(
                name='configlint-result-set',
                value=f'{work_dir_path}/validate-environment-configuration/configlint_results_file.txt'
            )
            expected_step_result.add_artifact(
                name='configlint-yml-path',
                value=file_to_validate_file_path
            )
            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())

    @patch('sh.config_lint', create=True)
    def test_run_step_pass(self, config_lint_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            test_file_name = 'file.txt'
            test_file_path = os.path.join(temp_dir.path, test_file_name)
            temp_dir.write(test_file_path, b'ignored')
            step_config = {
                'rules': test_file_path,
                'configlint-yml-path': test_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='validate-environment-configuration',
                implementer='Configlint',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            config_lint_mock.side_effect = sh.ErrorReturnCode('config_lint', b'mock out', b'mock error')
            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='validate-environment-configuration',
                sub_step_name='Configlint',
                sub_step_implementer_name='Configlint'
            )

            expected_step_result.success = False
            expected_step_result.message = 'Unexpected Error invoking config-lint.'
            expected_step_result.add_artifact(
                name='configlint-result-set',
                value=f'{work_dir_path}/validate-environment-configuration/configlint_results_file.txt'
            )
            expected_step_result.add_artifact(
                name='configlint-yml-path',
                value=test_file_path
            )
            self.assertEqual(expected_step_result.get_step_result_dict(), result.get_step_result_dict())
