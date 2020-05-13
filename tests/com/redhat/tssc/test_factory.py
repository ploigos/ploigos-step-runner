import pytest

from com.redhat.tssc import TSSCFactory

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
