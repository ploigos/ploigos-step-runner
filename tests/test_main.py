import pytest
import mock
import os
from testfixtures import TempDirectory

from tssc.__main__ import main
from tssc import TSSCFactory, StepImplementer, TSSCException

class FooStepImplementer(StepImplementer):
    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, {})

    @classmethod
    def step_name(cls):
        return 'foo'

    def _run_step(self, runtime_step_config):
        pass

class RequiredStepConfigStepImplementer(StepImplementer):
    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, {})

    @classmethod
    def step_name(cls):
        return 'required-step-config-test'

    def _validate_step_config(self, step_config):
        if 'required-config-key' not in step_config:
            raise ValueError('Key (required-config-key) must be in the step configuration')

    def _run_step(self, runtime_step_config):
        pass

class RequiredRuntimeStepConfigStepImplementer(StepImplementer):
    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, {})

    @classmethod
    def step_name(cls):
        return 'required-runtime-step-config-test'

    def _run_step(self, runtime_step_config):
        if 'required-rutnime-config-key' not in runtime_step_config:
            raise TSSCException('Key (required-rutnime-config-key) must be in the step configuration')

def _run_main_test(argv, expected_exit_code=None, config_file_contents=None, config_file_name='tssc-config'):
    with TempDirectory() as temp_dir:
        if config_file_contents:
            temp_dir.write(config_file_name, bytes(config_file_contents, 'utf-8'))
            config_file_path = os.path.join(temp_dir.path, config_file_name)
            argv.append('--config-file')
            argv.append(config_file_path)

        if expected_exit_code is not None:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                main(argv)
            assert pytest_wrapped_e.type == SystemExit, \
                "Expected system exit"
            assert pytest_wrapped_e.value.code == expected_exit_code, \
                "Expected exit code (%d) got (%d)" % (expected_exit_code, pytest_wrapped_e.value.code)
        else:
            main(argv)

def test_init():
    """
    Notes
    -----
    See https://medium.com/opsops/how-to-test-if-name-main-1928367290cb
    """
    from tssc import __main__
    with mock.patch.object(__main__, "main", return_value=42):
        with mock.patch.object(__main__, "__name__", "__main__"):
            with mock.patch.object(__main__.sys, 'exit') as mock_exit:
                __main__.init()
                assert mock_exit.call_args[0][0] == 42

def test_no_arguments():
    _run_main_test(None, 2)

def test_help():
    _run_main_test(['--help'], 0)

def test_bad_arg():
    _run_main_test(['--bad-arg'], 2)

def test_config_file_does_not_exist():
    _run_main_test(['--step', 'generate-metadata', '--config-file', 'does-not-exist.yml'], 101)

def test_config_file_not_json_or_yaml():
    _run_main_test(['--step', 'generate-metadata'], 102,
        ": blarg this: is {} bad syntax")

def test_config_file_no_root_tssc_config_key():
    _run_main_test(['--step', 'generate-metadata'], 103, "{}")

def test_config_file_valid_yaml():
    TSSCFactory.register_step_implementer(FooStepImplementer, True)
    _run_main_test(['--step', 'foo'], None,
        '''tssc-config: {}'''
    )

def test_config_file_valid_json():
    TSSCFactory.register_step_implementer(FooStepImplementer, True)
    _run_main_test(['--step', 'foo'], None,
        '''{"tssc-config":{}}'''
    )

def test_required_step_config_missing():
    TSSCFactory.register_step_implementer(RequiredStepConfigStepImplementer, True)
    _run_main_test(['--step', 'required-step-config-test'], 200,
        '''{"tssc-config":{}}'''
    )

def test_required_step_config_pass_via_config_file():
    TSSCFactory.register_step_implementer(RequiredStepConfigStepImplementer, True)
    _run_main_test(['--step', 'required-step-config-test'], None,
        '''---
        tssc-config:
          required-step-config-test:
            implementer: RequiredStepConfigStepImplementer
            config:
              required-config-key: "hello world"
        '''
    )

def test_required_step_config_pass_via_runtime_arg_missing():
    TSSCFactory.register_step_implementer(RequiredRuntimeStepConfigStepImplementer, True)
    _run_main_test(
        [
            '--step', 'required-runtime-step-config-test',
            '--step-config', 'wrong-config="hello world"'
        ],
        200,
        '''---
        tssc-config: {}
        '''
    )

def test_required_step_config_pass_via_runtime_arg_valid():
    TSSCFactory.register_step_implementer(RequiredRuntimeStepConfigStepImplementer, True)
    _run_main_test(
        [
            '--step', 'required-runtime-step-config-test',
            '--step-config', 'required-rutnime-config-key="hello world"'
        ],
        None,
        '''---
        tssc-config: {}
        '''
    )
