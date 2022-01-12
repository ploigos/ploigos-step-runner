import re
from unittest.mock import patch

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_runner import StepRunner
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.config import Config
from testfixtures import TempDirectory

from tests.helpers.base_test_case import BaseTestCase


class TestStepRunner(BaseTestCase):
    def test_init_valid_config(self):
        config = {
            'step-runner-config': {
            }
        }

        StepRunner(config)

    def test_init_invalid_config(self):
        config = {
            'blarg-config': {
            }
        }

        with self.assertRaisesRegex(
                AssertionError,
                r"Failed to add invalid config. "
                r"Missing expected top level key \(step-runner-config\): {'blarg-config': {}}"):
            StepRunner(config)

    def test_run_step_with_no_config(self):
        config = {
            'step-runner-config': {
            }
        }

        factory = StepRunner(config)

        with self.assertRaisesRegex(
           AssertionError,
               r"Can not run step \(foo\) because no step configuration provided."):
               factory.run_step('foo')

    def test_run_step_config_specified_StepImplementer_does_not_exist(self):
        config = {
            'step-runner-config': {
                'foo': [
                    {
                        'implementer': 'DoesNotExist'
                    }
                ]
            }
        }

        factory = StepRunner(config)

        with self.assertRaisesRegex(
            StepRunnerException,
                r"Could not dynamically load step \(foo\) step implementer \(DoesNotExist\)"
                r" from module \(ploigos_step_runner.step_implementers.foo\) with class name \(DoesNotExist\)"):
            factory.run_step('foo')

    def test_run_step_config_implementer_specified_and_sub_step_config_specified_StepImplementer(self):
        config = {
            'step-runner-config': {
                'foo': [
                    {
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                        'config': {}
                    }
                ]
            }
        }
        with TempDirectory() as temp_dir:
            factory = StepRunner(config)
            factory.run_step('foo')

    def test_run_step_config_implementer_specified_and_no_sub_step_config_specified_StepImplementer(self):
        config = {
            'step-runner-config': {
                'foo': [
                    {
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                    }
                ]
            }
        }
        with TempDirectory() as temp_dir:
            factory = StepRunner(config)
            factory.run_step('foo')

    def test_run_step_config_only_sub_step_and_is_dict_rather_then_array(self):
        config = {
            'step-runner-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                }
            }
        }
        with TempDirectory() as temp_dir:
            factory = StepRunner(config)
            factory.run_step('foo')

    def test_init_with_config_object(self):
        config = {
            Config.CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo'
                }
            }
        }
        config = Config(config)
        factory = StepRunner(config)
        self.assertEqual(factory.config, config)

    def test_init_with_dict(self):
        config = {
            Config.CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo'
                }
            }
        }

        factory = StepRunner(config)
        sub_step_configs = factory.config.get_sub_step_configs('step-foo')
        self.assertEqual(len(sub_step_configs), 1)

    def test__get_step_implementer_class_does_not_exist_using_default_steps_module(self):
        with self.assertRaisesRegex(
                StepRunnerException,
                r"Could not dynamically load step \(foo\) step implementer \(bar\) "
                r"from module \(ploigos_step_runner.step_implementers.foo\) with class name \(bar\)"):
            StepRunner._StepRunner__get_step_implementer_class('foo', 'bar')

    def test__get_step_implementer_name_class_does_not_exist_given_module_path(self):
        with self.assertRaisesRegex(
                StepRunnerException,
                r"Could not dynamically load step \(foo\) step implementer"
                r" \(tests.helpers.sample_step_implementers.DoesNotExist\) from module \(tests.helpers.sample_step_implementers\) with class name \(DoesNotExist\)"):
            StepRunner._StepRunner__get_step_implementer_class('foo',
                                                                 'tests.helpers.sample_step_implementers.DoesNotExist')

    def test__get_step_implementer_name_class_is_not_subclass_of_StepImplementer(self):
        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Step \(foo\) is configured to use step implementer "
                    r"\(tests.helpers.sample_step_implementers.NotSubClassOfStepImplementer\) "
                    r"from module \(tests.helpers.sample_step_implementers\) with class name "
                    r"\(NotSubClassOfStepImplementer\), and dynamically loads as class "
                    r"\(<class 'tests.helpers.sample_step_implementers.NotSubClassOfStepImplementer'>\) "
                    r"which is not a subclass of required parent class "
                    r"\(<class 'ploigos_step_runner.step_implementer.StepImplementer'>\)."
                )
        ):
            StepRunner._StepRunner__get_step_implementer_class('foo',
                                                                 'tests.helpers.sample_step_implementers.NotSubClassOfStepImplementer')

    def test__get_step_implementer_class_exists_defaultt_steps_module(self):
        self.assertIsNotNone(
            StepRunner._StepRunner__get_step_implementer_class('container_image_static_compliance_scan', 'OpenSCAP')
        )

    def test__get_step_implementer_class_exists_include_module(self):
        self.assertIsNotNone(
            StepRunner._StepRunner__get_step_implementer_class(
                'foo',
                'tests.helpers.sample_step_implementers.FooStepImplementer'
            )
        )

    @patch('tests.helpers.sample_step_implementers.FooStepImplementer2._run_step')
    @patch('tests.helpers.sample_step_implementers.FooStepImplementer._run_step')
    def test_run_step_multiple_sub_steps_all_succeed(
        self,
        foo_step_implementer_run_step_mock,
        foo_step_implementer2_run_step_mock
    ):
        config = {
            'step-runner-config': {
                'foo': [
                    {
                        'name': 'Mock Sub Step 1',
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                    },
                    {
                        'name': 'Mock Sub Step 2',
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer2'
                    }
                ]
            }
        }

        # mock return value
        mock_sub_step_1_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 1',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_1_result.success = True
        mock_sub_step_2_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 2',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_2_result.success = True

        foo_step_implementer_run_step_mock.return_value = mock_sub_step_1_result
        foo_step_implementer2_run_step_mock.return_value = mock_sub_step_2_result

        # run test
        step_runner = StepRunner(config)
        actual_success = step_runner.run_step('foo')

        # validate
        self.assertTrue(actual_success)
        foo_step_implementer_run_step_mock.assert_called_once()
        foo_step_implementer2_run_step_mock.assert_called_once()

    @patch('tests.helpers.sample_step_implementers.FooStepImplementer2._run_step')
    @patch('tests.helpers.sample_step_implementers.FooStepImplementer._run_step')
    def test_run_step_multiple_sub_steps_first_sub_step_fail(
        self,
        foo_step_implementer_run_step_mock,
        foo_step_implementer2_run_step_mock
    ):
        config = {
            'step-runner-config': {
                'foo': [
                    {
                        'name': 'Mock Sub Step 1',
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                    },
                    {
                        'name': 'Mock Sub Step 2',
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer2'
                    }
                ]
            }
        }

        # mock return value
        mock_sub_step_1_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 1',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_1_result.success = False
        mock_sub_step_2_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 2',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_2_result.success = True

        foo_step_implementer_run_step_mock.return_value = mock_sub_step_1_result
        foo_step_implementer2_run_step_mock.return_value = mock_sub_step_2_result

        # run test
        step_runner = StepRunner(config)
        actual_success = step_runner.run_step('foo')

        # validate
        self.assertFalse(actual_success)
        foo_step_implementer_run_step_mock.assert_called_once()
        foo_step_implementer2_run_step_mock.assert_not_called()

    @patch('tests.helpers.sample_step_implementers.FooStepImplementer2._run_step')
    @patch('tests.helpers.sample_step_implementers.FooStepImplementer._run_step')
    def test_run_step_multiple_sub_steps_second_sub_step_fail(
        self,
        foo_step_implementer_run_step_mock,
        foo_step_implementer2_run_step_mock
    ):
        config = {
            'step-runner-config': {
                'foo': [
                    {
                        'name': 'Mock Sub Step 1',
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                    },
                    {
                        'name': 'Mock Sub Step 2',
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer2'
                    }
                ]
            }
        }

        # mock return value
        mock_sub_step_1_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 1',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_1_result.success = True
        mock_sub_step_2_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 2',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_2_result.success = False

        foo_step_implementer_run_step_mock.return_value = mock_sub_step_1_result
        foo_step_implementer2_run_step_mock.return_value = mock_sub_step_2_result

        # run test
        step_runner = StepRunner(config)
        actual_success = step_runner.run_step('foo')

        # validate
        self.assertFalse(actual_success)
        foo_step_implementer_run_step_mock.assert_called_once()
        foo_step_implementer2_run_step_mock.assert_called_once()

    @patch('tests.helpers.sample_step_implementers.FooStepImplementer2._run_step')
    @patch('tests.helpers.sample_step_implementers.FooStepImplementer._run_step')
    def test_run_step_multiple_sub_steps_first_sub_step_fail_contine_sub_steps_on_failure_bool(
        self,
        foo_step_implementer_run_step_mock,
        foo_step_implementer2_run_step_mock
    ):
        config = {
            'step-runner-config': {
                'foo': [
                    {
                        'name': 'Mock Sub Step 1',
                        'continue-sub-steps-on-failure': True,
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                    },
                    {
                        'name': 'Mock Sub Step 2',
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer2'
                    }
                ]
            }
        }

        # mock return value
        mock_sub_step_1_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 1',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_1_result.success = False
        mock_sub_step_2_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 2',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_2_result.success = True

        foo_step_implementer_run_step_mock.return_value = mock_sub_step_1_result
        foo_step_implementer2_run_step_mock.return_value = mock_sub_step_2_result

        # run test
        step_runner = StepRunner(config)
        actual_success = step_runner.run_step('foo')

        # validate
        self.assertFalse(actual_success)
        foo_step_implementer_run_step_mock.assert_called_once()
        foo_step_implementer2_run_step_mock.assert_called_once()

    @patch('tests.helpers.sample_step_implementers.FooStepImplementer2._run_step')
    @patch('tests.helpers.sample_step_implementers.FooStepImplementer._run_step')
    def test_run_step_multiple_sub_steps_first_sub_step_fail_contine_sub_steps_on_failure_str(
        self,
        foo_step_implementer_run_step_mock,
        foo_step_implementer2_run_step_mock
    ):
        config = {
            'step-runner-config': {
                'foo': [
                    {
                        'name': 'Mock Sub Step 1',
                        'continue-sub-steps-on-failure': 'true',
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                    },
                    {
                        'name': 'Mock Sub Step 2',
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer2'
                    }
                ]
            }
        }

        # mock return value
        mock_sub_step_1_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 1',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_1_result.success = False
        mock_sub_step_2_result = StepResult(
            step_name='foo',
            sub_step_name='Mock Sub Step 2',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        mock_sub_step_2_result.success = True

        foo_step_implementer_run_step_mock.return_value = mock_sub_step_1_result
        foo_step_implementer2_run_step_mock.return_value = mock_sub_step_2_result

        # run test
        step_runner = StepRunner(config)
        actual_success = step_runner.run_step('foo')

        # validate
        self.assertFalse(actual_success)
        foo_step_implementer_run_step_mock.assert_called_once()
        foo_step_implementer2_run_step_mock.assert_called_once()
