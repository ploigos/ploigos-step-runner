import pytest

from ploigos_step_runner.exceptions import StepRunnerException

def raise_StepRunnerException():
    raise StepRunnerException('test')

def test_StepRunnerException():
    with pytest.raises(StepRunnerException):
        raise_StepRunnerException()
