import pytest

from com.redhat.tssc import TSSCFactory, StepImplementer, TSSCException

class FooStepImplementer(StepImplementer):
    STEP_NAME = 'foo'

    def run_step(self):
        print('FooStepImplementer.run_step - hello world: ' + str(self.config))

def test_TSSCFactory_init_valid_config():
    config = {
        'tssc-config': {
        }
    }
    factory = TSSCFactory(config)
    
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
    factory = TSSCFactory(config)

    with pytest.raises(TSSCException):
        factory.run_step('does-not-exist')

def test_TSSCFactory_run_step_no_default_StepImplementer_for_step_without_config():
    config = {
        'tssc-config': {
        }
    }
    factory = TSSCFactory(config)
    TSSCFactory.register_step_implementer(FooStepImplementer)

    with pytest.raises(TSSCException):
        factory.run_step('foo')

def test_TSSCFactory_run_step_default_StepImplementer_for_step_without_config():
    config = {
        'tssc-config': {
        }
    }
    factory = TSSCFactory(config)
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
    factory = TSSCFactory(config)
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
    factory = TSSCFactory(config)
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
    factory = TSSCFactory(config)
    TSSCFactory.register_step_implementer(FooStepImplementer)

    factory.run_step('foo')
