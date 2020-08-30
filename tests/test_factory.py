import unittest

from tssc import TSSCFactory, TSSCException, StepImplementer, TSSCConfig
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.sample_step_implementers import *

class TestFactory(BaseTSSCTestCase):
    def test_init_valid_config(self):
        config = {
            'tssc-config': {
            }
        }
        factory = TSSCFactory(config, 'results.yml')

    def test_init_invalid_config(self):
        config = {
            'blarg-config': {
            }
        }

        with self.assertRaisesRegex(
                AssertionError,
                r"Failed to add invalid TSSC config. Missing expected top level key \(tssc-config\): {'blarg-config': {}}"):
            TSSCFactory(config)

    def test_run_step_no_StepImplementers_for_step(self):
        config = {
            'tssc-config': {
                'step-with-none-existent-implementer': {
                    'implementer': 'does-not-exist'
                }
            }
        }
        factory = TSSCFactory(config, 'results.yml')

        with self.assertRaisesRegex(
                AssertionError,
                r"No implementers registered for step \(step-with-none-existent-implementer\)."):
            factory.run_step('step-with-none-existent-implementer')

    def test_run_step_with_no_config(self):
        config = {
            'tssc-config': {
            }
        }
        factory = TSSCFactory(config, 'results.yml')
        TSSCFactory.register_step_implementer(FooStepImplementer, True)

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
        TSSCFactory.register_step_implementer(FooStepImplementer)

        with self.assertRaisesRegex(
                TSSCException,
                r"No StepImplementer for step \(foo\) with TSSC config specified implementer name \(DoesNotExist\)"):
            factory.run_step('foo')

    def test_run_step_config_implementer_specfied_and_sub_step_config_specified_StepImplementer(self):
        config = {
            'tssc-config': {
                'foo': [
                    {
                        'implementer': 'FooStepImplementer',
                        'config': {}
                    }
                ]
            }
        }
        factory = TSSCFactory(config, 'results.yml')
        TSSCFactory.register_step_implementer(FooStepImplementer)

        factory.run_step('foo')

    def test_run_step_config_implementer_specfied_and_no_sub_step_config_specified_StepImplementer(self):
        config = {
            'tssc-config': {
                'foo': [
                    {
                        'implementer': 'FooStepImplementer'
                    }
                ]
            }
        }
        factory = TSSCFactory(config, 'results.yml')
        TSSCFactory.register_step_implementer(FooStepImplementer)

        factory.run_step('foo')

    def test_run_step_config_only_sub_step_and_is_dict_rather_then_array(self):
        config = {
            'tssc-config': {
                'foo': {
                        'implementer': 'FooStepImplementer'
                }
            }
        }
        factory = TSSCFactory(config, 'results.yml')
        TSSCFactory.register_step_implementer(FooStepImplementer)

        factory.run_step('foo')

    def test_init_with_tsscconfig(self):
        config = {
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo'
                }
            }
        }
        tssc_config = TSSCConfig(config)
        factory = TSSCFactory(tssc_config, 'results.yml')

        self.assertEqual(factory.config, tssc_config)

    def test_init_with_dict(self):
        config = {
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo'
                }
            }
        }
        factory = TSSCFactory(config, 'results.yml')

        sub_step_configs = factory.config.get_sub_step_configs('step-foo')

        self.assertEqual(len(sub_step_configs), 1)
