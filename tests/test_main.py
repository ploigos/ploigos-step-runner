import unittest
from unittest.mock import patch

import os
from testfixtures import TempDirectory

from tssc.__main__ import main
from tssc import TSSCFactory, StepImplementer, TSSCException

class FooStepImplementer(StepImplementer):
    @staticmethod
    def step_name():
        print ('test------')
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

class RequiredStepConfigStepImplementer(StepImplementer):
    @staticmethod
    def step_name():
        return 'required-step-config-test'

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
        return [
            'required-config-key'
        ]

    def _run_step(self, runtime_step_config):
        pass

class RequiredRuntimeStepConfigStepImplementer(StepImplementer):
    @staticmethod
    def step_name():
        return 'required-runtime-step-config-test'

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
        if 'required-rutnime-config-key' not in runtime_step_config:
            raise TSSCException('Key (required-rutnime-config-key) must be in the step configuration')

class TestInit(unittest.TestCase):
    def _run_main_test(self, argv, expected_exit_code=None, config_file_contents=None, config_file_name='tssc-config'):
        with TempDirectory() as temp_dir:
            if config_file_contents:
                temp_dir.write(config_file_name, bytes(config_file_contents, 'utf-8'))
                config_file_path = os.path.join(temp_dir.path, config_file_name)
                argv.append('--config-file')
                argv.append(config_file_path)
    
            if expected_exit_code is not None:
                with self.assertRaises(SystemExit) as cm:
                    main(argv)
                
                exception = cm.exception
                self.assertEqual(exception.code, expected_exit_code,
                    "Expected system exit with code: {code}".format(code=expected_exit_code))
            else:
                main(argv)
    
    def test_init(self):
        """
        Notes
        -----
        See https://medium.com/opsops/how-to-test-if-name-main-1928367290cb
        """
        from tssc import __main__
        with patch.object(__main__, "main", return_value=42):
            with patch.object(__main__, "__name__", "__main__"):
                with patch.object(__main__.sys, 'exit') as mock_exit:
                    __main__.init()
                    assert mock_exit.call_args[0][0] == 42

    def test_no_arguments(self):
        self._run_main_test(None, 2)

    def test_help(self):
        self._run_main_test(['--help'], 0)

    def test_bad_arg(self):
        self._run_main_test(['--bad-arg'], 2)

    def test_config_file_does_not_exist(self):
        self._run_main_test(['--step', 'generate-metadata', '--config-file', 'does-not-exist.yml'], 101)

    def test_config_file_not_json_or_yaml(self):
        self._run_main_test(['--step', 'generate-metadata'], 102,
            ": blarg this: is {} bad syntax")

    def test_config_file_no_root_tssc_config_key(self):
        self._run_main_test(['--step', 'generate-metadata'], 103, "{}")

    def test_config_file_valid_yaml(self):
        TSSCFactory.register_step_implementer(FooStepImplementer, True)
        self._run_main_test(['--step', 'foo'], None,
            '''tssc-config: {}'''
        )

    def test_config_file_valid_json(self):
        TSSCFactory.register_step_implementer(FooStepImplementer, True)
        self._run_main_test(['--step', 'foo'], None,
            '''{"tssc-config":{}}'''
        )

    def test_required_step_config_missing(self):
        TSSCFactory.register_step_implementer(RequiredStepConfigStepImplementer, True)
        self._run_main_test(['--step', 'required-step-config-test'], 200,
            '''{"tssc-config":{}}'''
        )

    def test_required_step_config_pass_via_config_file(self):
        TSSCFactory.register_step_implementer(RequiredStepConfigStepImplementer, True)
        self._run_main_test(['--step', 'required-step-config-test'], None,
            '''---
            tssc-config:
              required-step-config-test:
                implementer: RequiredStepConfigStepImplementer
                config:
                  required-config-key: "hello world"
            '''
        )

    def test_required_step_config_pass_via_runtime_arg_missing(self):
        TSSCFactory.register_step_implementer(RequiredRuntimeStepConfigStepImplementer, True)
        self._run_main_test(
            [
                '--step', 'required-runtime-step-config-test',
                '--step-config', 'wrong-config="hello world"'
            ],
            200,
            '''---
            tssc-config: {}
            '''
        )

    def test_required_step_config_pass_via_runtime_arg_valid(self):
        TSSCFactory.register_step_implementer(RequiredRuntimeStepConfigStepImplementer, True)
        self._run_main_test(
            [
                '--step', 'required-runtime-step-config-test',
                '--step-config', 'required-rutnime-config-key="hello world"'
            ],
            None,
            '''---
            tssc-config: {}
            '''
        )
