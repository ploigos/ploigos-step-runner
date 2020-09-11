import unittest

import re

from tssc import TSSCFactory, TSSCException, StepImplementer
from tssc.config import Config

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.sample_step_implementers import *

class TestFactory(BaseTSSCTestCase):
    def test_init_valid_config(self):
        config = {
            'tssc-config': {
            }
        }
        TSSCFactory(config, 'results.yml')

    def test_init_invalid_config(self):
        config = {
            'blarg-config': {
            }
        }

        with self.assertRaisesRegex(
                AssertionError,
                r"Failed to add invalid TSSC config. Missing expected top level key \(tssc-config\): {'blarg-config': {}}"):
            TSSCFactory(config)

    def test_run_step_with_no_config(self):
        config = {
            'tssc-config': {
            }
        }
        factory = TSSCFactory(config, 'results.yml')

        with self.assertRaisesRegex(
                AssertionError,
                r"Can not run step \(foo\) because no step configuration provided."):
            factory.run_step('foo')

    def test_run_step_config_specfied_StepImplementer_does_not_exist(self):
        config = {
            'tssc-config': {
                'foo': [
                    {
                        'implementer': 'DoesNotExist'
                    }
                ]
            }
        }
        factory = TSSCFactory(config, 'results.yml')

        with self.assertRaisesRegex(
                TSSCException,
                r"Could not dynamically load step \(foo\) step implementer \(DoesNotExist\) from module \(tssc.step_implementers.foo\) with class name \(DoesNotExist\)"):
            factory.run_step('foo')

    def test_run_step_config_implementer_specfied_and_sub_step_config_specified_StepImplementer(self):
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
        factory = TSSCFactory(config, 'results.yml')

        factory.run_step('foo')

    def test_run_step_config_implementer_specfied_and_no_sub_step_config_specified_StepImplementer(self):
        config = {
            'tssc-config': {
                'foo': [
                    {
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                    }
                ]
            }
        }
        factory = TSSCFactory(config, 'results.yml')

        factory.run_step('foo')

    def test_run_step_config_only_sub_step_and_is_dict_rather_then_array(self):
        config = {
            'tssc-config': {
                'foo': {
                        'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer'
                }
            }
        }
        factory = TSSCFactory(config, 'results.yml')

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
        factory = TSSCFactory(tssc_config, 'results.yml')

        self.assertEqual(factory.config, tssc_config)

    def test_init_with_dict(self):
        config = {
            Config.TSSC_CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo'
                }
            }
        }
        factory = TSSCFactory(config, 'results.yml')

        sub_step_configs = factory.config.get_sub_step_configs('step-foo')

        self.assertEqual(len(sub_step_configs), 1)

    def test__get_step_implementer_class_does_not_exist_using_default_steps_module(self):
        with self.assertRaisesRegex(
                TSSCException,
                r"Could not dynamically load step \(foo\) step implementer \(bar\) from module \(tssc.step_implementers.foo\) with class name \(bar\)"):

            TSSCFactory._TSSCFactory__get_step_implementer_class('foo', 'bar')

    def test__get_step_implementer_name_class_does_not_exist_given_module_path(self):
        with self.assertRaisesRegex(
                TSSCException,
                r"Could not dynamically load step \(foo\) step implementer \(tests.helpers.sample_step_implementers.DoesNotExist\) from module \(tests.helpers.sample_step_implementers\) with class name \(DoesNotExist\)"):

            TSSCFactory._TSSCFactory__get_step_implementer_class('foo', 'tests.helpers.sample_step_implementers.DoesNotExist')

    def test__get_step_implementer_name_class_is_not_subclass_of_StepImplementer(self):
        with self.assertRaisesRegex(
            TSSCException,
            re.compile(
                "Step \(foo\) is configured to use step implementer "
                "\(tests.helpers.sample_step_implementers.NotSubClassOfStepImplementer\) "
                "from module \(tests.helpers.sample_step_implementers\) with class name "
                "\(NotSubClassOfStepImplementer\), and dynamically loads as class "
                "\(<class 'tests.helpers.sample_step_implementers.NotSubClassOfStepImplementer'>\) "
                "which is not a subclass of required parent class "
                "\(<class 'tssc.step_implementer.StepImplementer'>\)."
            )
        ):

            TSSCFactory._TSSCFactory__get_step_implementer_class('foo', 'tests.helpers.sample_step_implementers.NotSubClassOfStepImplementer')

    def test__get_step_implementer_class_exists_defaultt_steps_module(self):
        self.assertIsNotNone(
            TSSCFactory._TSSCFactory__get_step_implementer_class('package', 'Maven')
        )

    def test__get_step_implementer_class_exists_include_module(self):
        self.assertIsNotNone(
            TSSCFactory._TSSCFactory__get_step_implementer_class(
                'foo',
                'tests.helpers.sample_step_implementers.FooStepImplementer'
            )
        )
