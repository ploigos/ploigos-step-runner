import pytest

from tssc import StepRunnerException

def raise_StepRunnerException():
    raise StepRunnerException('test')

def test_StepRunnerException():
    with pytest.raises(StepRunnerException):
        raise_StepRunnerException()
