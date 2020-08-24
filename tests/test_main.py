import unittest
from unittest.mock import patch

import os
import yaml
from testfixtures import TempDirectory

from tssc.__main__ import main
from tssc import TSSCFactory, StepImplementer, TSSCException
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

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

class WriteConfigAsResultsStepImplementer(StepImplementer):
    @staticmethod
    def step_name():
        return 'write-config-as-results'
    
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
        return runtime_step_config

class TestInit(BaseTSSCTestCase):
    def _run_main_test(self, argv, expected_exit_code=None, config_files=None, expected_results=None):
        if argv is None:
            argv = []

        with TempDirectory() as temp_dir:
            if config_files:
                argv.append('--config')
                for config_file in config_files:
                    config_file_name = config_file['name']
                    config_file_contents = config_file['contents']
                    
                    temp_dir.write(config_file_name, bytes(config_file_contents, 'utf-8'))
                    config_file_path = os.path.join(temp_dir.path, config_file_name)
                    argv.append(config_file_path)

            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            argv.append('--results-dir')
            argv.append(results_dir_path)
    
            if expected_exit_code is not None:
                with self.assertRaises(SystemExit) as cm:
                    main(argv)
                
                exception = cm.exception
                self.assertEqual(exception.code, expected_exit_code,
                    "Expected system exit with code: {code}".format(code=expected_exit_code))
            else:
                main(argv)
                
                if expected_results:
                    with open(os.path.join(results_dir_path, "tssc-results.yml"), 'r') as step_results_file:
                        results = yaml.safe_load(step_results_file.read())
                        self.assertEqual(results, expected_results)
    
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
        self._run_main_test(['--step', 'generate-metadata', '--config', 'does-not-exist.yml'], 101)

    def test_config_file_not_json_or_yaml(self):
        self._run_main_test(['--step', 'generate-metadata'], 102,[
            {
                'name': 'tssc-config.yaml',
                'contents': ": blarg this: is {} bad syntax"
            }]
        )

    def test_config_file_no_root_tssc_config_key(self):
        self._run_main_test(['--step', 'generate-metadata'], 103, [
            {
                'name': 'tssc-config.yaml',
                'contents': '{}'
            }]
        )

    def test_config_file_valid_yaml(self):
        TSSCFactory.register_step_implementer(FooStepImplementer, True)
        self._run_main_test(['--step', 'foo'], None, [
            {
                'name': 'tssc-config.yaml',
                'contents': '''---
                tssc-config: {}
                '''
            }]
        )

    def test_config_file_valid_json(self):
        TSSCFactory.register_step_implementer(FooStepImplementer, True)
        self._run_main_test(['--step', 'foo'], None,[
            {
                'name': 'tssc-config.json',
                'contents': '''---
                tssc-config: {}
                '''
            }]
        )

    def test_required_step_config_missing(self):
        TSSCFactory.register_step_implementer(RequiredStepConfigStepImplementer, True)
        self._run_main_test(['--step', 'required-step-config-test'], 200, [
            {
                'name': 'tssc-config.yaml',
                'contents': '''---
                tssc-config: {}
                '''
            }]
        )

    def test_required_step_config_pass_via_config_file(self):
        TSSCFactory.register_step_implementer(RequiredStepConfigStepImplementer, True)
        self._run_main_test(['--step', 'required-step-config-test'], None,[
            {
                'name': 'tssc-config.yaml',
                'contents': '''---
                    tssc-config:
                        required-step-config-test:
                            implementer: RequiredStepConfigStepImplementer
                            config:
                                required-config-key: "hello world"
                '''
            }]
        )

    def test_required_step_config_pass_via_runtime_arg_missing(self):
        TSSCFactory.register_step_implementer(RequiredRuntimeStepConfigStepImplementer, True)
        self._run_main_test(
            [
                '--step', 'required-runtime-step-config-test',
                '--step-config', 'wrong-config="hello world"'
            ],
            200,
            [
                {
                    'name': 'tssc-config.yaml',
                    'contents': '''---
                    tssc-config: {}
                    '''
                }
            ]
        )

    def test_required_step_config_pass_via_runtime_arg_valid(self):
        TSSCFactory.register_step_implementer(RequiredRuntimeStepConfigStepImplementer, True)
        self._run_main_test(
            [
                '--step', 'required-runtime-step-config-test',
                '--step-config', 'required-rutnime-config-key="hello world"'
            ],
            None,
            [
                {
                    'name': 'tssc-config.yaml',
                    'contents': '''---
                    tssc-config: {}
                    '''
                }
            ]
        )

    def test_multiple_config_files_verify_required_key_not_overwritten(self):
        TSSCFactory.register_step_implementer(RequiredStepConfigStepImplementer, True)
        self._run_main_test(
            ['--step', 'required-step-config-test'],
            None,
            [
                {
                    'name': 'tssc-config1.yaml',
                    'contents': '''---
                        tssc-config:
                            required-step-config-test:
                                implementer: RequiredStepConfigStepImplementer
                                config:
                                    required-config-key: "hello world"
                                    bar: 'test'
                    '''
                },
                {
                    'name': 'tssc-config2.yaml',
                    'contents': '''---
                        tssc-config:
                            required-step-config-test:
                                implementer: RequiredStepConfigStepImplementer
                                config:
                                    key2: "goodbye world"
                    '''
                }
            ]
        )

    def test_multiple_config_files_verify_expected_merge(self):
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer, True)
        self._run_main_test(
            ['--step', 'write-config-as-results'],
            None,
            [
                {
                    'name': 'tssc-config1.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: WriteConfigAsResultsStepImplementer
                                config:
                                    key1: "value1"
                                    key2: "value1"
                    '''
                },
                {
                    'name': 'tssc-config2.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: WriteConfigAsResultsStepImplementer
                                config:
                                    key3: "value2"
                                    required-config-key: 'value'
                    '''
                }
            ],
            {
                'tssc-results': {
                    'write-config-as-results': {
                        'key1': 'value1',
                        'key2': 'value1',
                        'key3': 'value2',
                        'required-config-key': 'value'
                    }
                }
            }
        )

    def test_multiple_config_files_dup_keys_error(self):
        TSSCFactory.register_step_implementer(RequiredStepConfigStepImplementer, True)
        self._run_main_test(
            ['--step', 'required-step-config-test'],
            102,
            [
                {
                    'name': 'tssc-config1.yaml',
                    'contents': '''---
                        tssc-config:
                            required-step-config-test:
                                implementer: RequiredStepConfigStepImplementer
                                config:
                                    required-config-key: "hello world"
                                    bar: 'test'
                    '''
                },
                {
                    'name': 'tssc-config2.yaml',
                    'contents': '''---
                        tssc-config:
                            required-step-config-test:
                                implementer: RequiredStepConfigStepImplementer
                                config:
                                    bar: "goodbye world"
                    '''
                }
            ]
        )

    def test_multiple_config_files_from_dir(self):
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer, True)
        
        args = ['--step', 'write-config-as-results']
        
        with TempDirectory() as temp_dir:
            config_files = [
                {
                    'name': 'tssc-config1.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: WriteConfigAsResultsStepImplementer
                                config:
                                    required-config-key: 'value'
                    '''
                },
                {
                    'name': 'foo/a.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: WriteConfigAsResultsStepImplementer
                                config:
                                    keya: "a"

                    '''
                },
                {
                    'name': 'foo/b.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: WriteConfigAsResultsStepImplementer
                                config:
                                    keyb: "b"
                    '''
                },
                {
                    'name': 'foo/bar/c.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: WriteConfigAsResultsStepImplementer
                                config:
                                    keyc: "c"
                    '''
                },
                {
                    'name': 'foo/bar2/c2.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: WriteConfigAsResultsStepImplementer
                                config:
                                    keyc2: "c2"
                    '''
                },
                {
                    'name': 'foo/bar/meh/d.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: WriteConfigAsResultsStepImplementer
                                config:
                                    keyd: "d"
                    '''
                }
            ]
            for config_file in config_files:
                config_file_name = config_file['name']
                config_file_contents = config_file['contents']
                
                temp_dir.write(config_file_name, bytes(config_file_contents, 'utf-8'))

            args.append('--config')
            args.append(os.path.join(temp_dir.path, 'foo'))
            args.append(os.path.join(temp_dir.path, 'tssc-config1.yaml'))
            self._run_main_test(
                args,
                None,
                None,
                {
                    'tssc-results': {
                        'write-config-as-results': {
                            'keya': 'a',
                            'keyb': 'b',
                            'keyc': 'c',
                            'keyc2': 'c2',
                            'keyd': 'd',
                            'required-config-key': 'value'
                        }
                    }
                }
            )
