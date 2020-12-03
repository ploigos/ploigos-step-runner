# pylint: disable=line-too-long
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import re
from testfixtures import TempDirectory

from tssc import TSSCFactory, StepRunnerException
from tssc.config import Config

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase


class TestFactory(BaseTSSCTestCase):
    def test_init_valid_config(self):
        config = {
            'tssc-config': {
            }
        }

        TSSCFactory(config)

    def test_init_invalid_config(self):
        config = {
            'blarg-config': {
            }
        }

        with self.assertRaisesRegex(
                AssertionError,
                r"Failed to add invalid TSSC config. "
                r"Missing expected top level key \(tssc-config\): {'blarg-config': {}}"):
            TSSCFactory(config)

    def test_run_step_with_no_config(self):
        config = {
            'tssc-config': {
            }
        }

        factory = TSSCFactory(config)

        with self.assertRaisesRegex(
           AssertionError,
               r"Can not run step \(foo\) because no step configuration provided."):
               factory.run_step('foo')

    def test_run_step_config_specified_StepImplementer_does_not_exist(self):
        config = {
            'tssc-config': {
                'foo': [
                    {
                        'implementer': 'DoesNotExist'
                    }
                ]
            }
        }

        factory = TSSCFactory(config)

        with self.assertRaisesRegex(
            StepRunnerException,
                r"Could not dynamically load step \(foo\) step implementer \(DoesNotExist\)"
                r" from module \(tssc.step_implementers.foo\) with class name \(DoesNotExist\)"):
            factory.run_step('foo')

    def test_run_step_config_implementer_specified_and_sub_step_config_specified_StepImplementer(self):
        config = {
            'tssc-config': {
                'foo': [
                    {
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                        'config': {}
                    }
                ]
            }
        }
        with TempDirectory() as temp_dir:
            factory = TSSCFactory(config, temp_dir.path)
            factory.run_step('foo')

    def test_run_step_config_implementer_specified_and_no_sub_step_config_specified_StepImplementer(self):
        config = {
            'tssc-config': {
                'foo': [
                    {
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                    }
                ]
            }
        }
        with TempDirectory() as temp_dir:
            factory = TSSCFactory(config, temp_dir.path)
            factory.run_step('foo')

    def test_run_step_config_only_sub_step_and_is_dict_rather_then_array(self):
        config = {
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                }
            }
        }
        with TempDirectory() as temp_dir:
            factory = TSSCFactory(config, temp_dir.path)
            factory.run_step('foo')

    def test_init_with_config_object(self):
        config = {
            Config.TSSC_CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo'
                }
            }
        }
        tssc_config = Config(config)
        factory = TSSCFactory(tssc_config)
        self.assertEqual(factory.config, tssc_config)

    def test_init_with_dict(self):
        config = {
            Config.TSSC_CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo'
                }
            }
        }

        factory = TSSCFactory(config)
        sub_step_configs = factory.config.get_sub_step_configs('step-foo')
        self.assertEqual(len(sub_step_configs), 1)

    def test__get_step_implementer_class_does_not_exist_using_default_steps_module(self):
        with self.assertRaisesRegex(
                StepRunnerException,
                r"Could not dynamically load step \(foo\) step implementer \(bar\) "
                r"from module \(tssc.step_implementers.foo\) with class name \(bar\)"):
            TSSCFactory._TSSCFactory__get_step_implementer_class('foo', 'bar')

    def test__get_step_implementer_name_class_does_not_exist_given_module_path(self):
        with self.assertRaisesRegex(
                StepRunnerException,
                r"Could not dynamically load step \(foo\) step implementer"
                r" \(tests.helpers.sample_step_implementers.DoesNotExist\) from module \(tests.helpers.sample_step_implementers\) with class name \(DoesNotExist\)"):
            TSSCFactory._TSSCFactory__get_step_implementer_class('foo',
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
                    r"\(<class 'tssc.step_implementer.StepImplementer'>\)."
                )
        ):
            TSSCFactory._TSSCFactory__get_step_implementer_class('foo',
                                                                 'tests.helpers.sample_step_implementers.NotSubClassOfStepImplementer')

    def test__get_step_implementer_class_exists_defaultt_steps_module(self):
        self.assertIsNotNone(
            TSSCFactory._TSSCFactory__get_step_implementer_class('container_image_static_compliance_scan', 'OpenSCAP')
        )

    def test__get_step_implementer_class_exists_include_module(self):
        self.assertIsNotNone(
            TSSCFactory._TSSCFactory__get_step_implementer_class(
                'foo',
                'tests.helpers.sample_step_implementers.FooStepImplementer'
            )
        )
