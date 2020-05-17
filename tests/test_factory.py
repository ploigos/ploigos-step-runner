import pytest

from tssc import TSSCFactory, TSSCException, StepImplementer

class FooStepImplementer(StepImplementer):
    def __init__(self, config, results_file):
        super().__init__(config, results_file, {})

    @classmethod
    def step_name(cls):
        return 'foo'

    def _run_step(self, runtime_step_config):
        pass

def test_TSSCFactory_init_valid_config():
    config = {
        'tssc-config': {
        }
    }
    factory = TSSCFactory(config, 'results.yml')
    
def test_TSSCFactory_init_invalid_config():
    config = {
        'blarg-config': {
        }
    }
    with pytest.raises(ValueError):
        factory = TSSCFactory(config)

def test_TSSCFactory_run_step_no_StepImplementers_for_step():
    config = {
        'tssc-config': {
        }
    }
    factory = TSSCFactory(config, 'results.yml')

    with pytest.raises(TSSCException):
        factory.run_step('does-not-exist')

def test_TSSCFactory_run_step_no_default_StepImplementer_for_step_without_config():
    config = {
        'tssc-config': {
        }
    }
    factory = TSSCFactory(config, 'results.yml')
    TSSCFactory.register_step_implementer(FooStepImplementer)

    with pytest.raises(TSSCException):
        factory.run_step('foo')

def test_TSSCFactory_run_step_default_StepImplementer_for_step_without_config():
    config = {
        'tssc-config': {
        }
    }
    factory = TSSCFactory(config, 'results.yml')
    TSSCFactory.register_step_implementer(FooStepImplementer, True)

    factory.run_step('foo')

def test_TSSCFactory_run_step_config_specfied_StepImplementer_does_not_exist():
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

    with pytest.raises(TSSCException):
        factory.run_step('foo')

def test_TSSCFactory_run_step_config_implementer_specfied_and_sub_step_config_specified_StepImplementer():
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

def test_TSSCFactory_run_step_config_implementer_specfied_and_no_sub_step_config_specified_StepImplementer():
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

def test_TSSCFactory_run_step_config_only_sub_step_and_is_dict_rather_then_array():
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
