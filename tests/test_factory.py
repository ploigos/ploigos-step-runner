import unittest

from tssc import TSSCFactory, TSSCException, StepImplementer

class FooStepImplementer(StepImplementer):
    @staticmethod
    def step_name():
        return 'foo'

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

        Notes
        -----
        These are the lowest precedence configuration values.

        Returns
        -------
        dict
            Default values to use for step configuration values.
        """
        return {}

    @staticmethod
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.

        See Also
        --------
        _validate_runtime_step_config

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.
        """
        return []

    def _run_step(self, runtime_step_config):
        pass

class TestFactory(unittest.TestCase):
    def test_TSSCFactory_init_valid_config(self):
        config = {
            'tssc-config': {
            }
        }
        factory = TSSCFactory(config, 'results.yml')
    
    def test_TSSCFactory_init_invalid_config(self):
        config = {
            'blarg-config': {
            }
        }

        with self.assertRaisesRegex(
                ValueError,
                r"config must contain key: tssc-config"):
            TSSCFactory(config)
    
    def test_TSSCFactory_run_step_no_StepImplementers_for_step(self):
        config = {
            'tssc-config': {
            }
        }
        factory = TSSCFactory(config, 'results.yml')
    
        with self.assertRaisesRegex(
                TSSCException,
                r"No implementers registered for step: does-not-exist"):
            factory.run_step('does-not-exist')
    
    def test_TSSCFactory_run_step_no_default_StepImplementer_for_step_without_config(self):
        config = {
            'tssc-config': {
            }
        }
        factory = TSSCFactory(config, 'results.yml')
        TSSCFactory.register_step_implementer(FooStepImplementer)
    
        with self.assertRaisesRegex(
                TSSCException,
                r"No implementer specified for step\(foo\) in config\(\{\}\) and no default step implementer registered in step implementers(.*)"):
            factory.run_step('foo')
    
    def test_TSSCFactory_run_step_default_StepImplementer_for_step_without_config(self):
        config = {
            'tssc-config': {
            }
        }
        factory = TSSCFactory(config, 'results.yml')
        TSSCFactory.register_step_implementer(FooStepImplementer, True)
    
        factory.run_step('foo')
    
    def test_TSSCFactory_run_step_default_StepImplementer_for_step_without_config_with_global_defaults(self):
        config = {
            'tssc-config': {
                'global-defaults': {
                    'foo': 'bar'
                }
            }
        }
        factory = TSSCFactory(config, 'results.yml')
        TSSCFactory.register_step_implementer(FooStepImplementer, True)
    
        factory.run_step('foo')
    
    def test_TSSCFactory_run_step_config_specfied_StepImplementer_does_not_exist(self):
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
    
    def test_TSSCFactory_run_step_config_implementer_specfied_and_sub_step_config_specified_StepImplementer(self):
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
    
    def test_TSSCFactory_run_step_config_implementer_specfied_and_no_sub_step_config_specified_StepImplementer(self):
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
    
    def test_TSSCFactory_run_step_config_only_sub_step_and_is_dict_rather_then_array(self):
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
