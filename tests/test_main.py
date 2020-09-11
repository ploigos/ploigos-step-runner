import unittest
from unittest.mock import patch

import io
import os
import yaml
from testfixtures import TempDirectory
from contextlib import redirect_stdout

from tssc.__main__ import main
from tssc import TSSCFactory, StepImplementer, TSSCException

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.sample_step_implementers import *
from tests.helpers.test_utils import create_sops_side_effect

class TestInit(BaseTSSCTestCase):
    def _run_main_test(self, argv, expected_exit_code=None, config_files=None, expected_results=None):
        if argv is None:
            argv = []

        with TempDirectory() as temp_dir:
            if config_files:
                argv.append('--config')
                for config_file in config_files:
                    if isinstance(config_file, dict):
                        config_file_name = config_file['name']
                        config_file_contents = config_file['contents']

                        temp_dir.write(config_file_name, bytes(config_file_contents, 'utf-8'))
                        config_file_path = os.path.join(temp_dir.path, config_file_name)
                        argv.append(config_file_path)
                    else:
                        argv.append(config_file)

            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            argv.append('--results-dir')
            argv.append(results_dir_path)

            if expected_exit_code is not None:
                with self.assertRaisesRegex(SystemExit, f"{expected_exit_code}") as cm:
                    main(argv)
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
        self._run_main_test(['--step', 'generate-metadata'], 102, [
            {
                'name': 'tssc-config.yaml',
                'contents': '{}'
            }]
        )

    def test_config_file_valid_yaml(self):
        self._run_main_test(['--step', 'foo'], None, [
            {
                'name': 'tssc-config.yaml',
                'contents': '''---
                tssc-config:
                    foo:
                        implementer: 'tests.helpers.sample_step_implementers.FooStepImplementer'
                '''
            }]
        )

    def test_config_file_valid_json(self):
        self._run_main_test(['--step', 'foo'], None,[
            {
                'name': 'tssc-config.json',
                'contents': '''
                {
                    "tssc-config": {
                        "foo": {
                        "implementer": 'tests.helpers.sample_step_implementers.FooStepImplementer'
                        }
                    }
                }
                '''
            }]
        )

    def test_required_step_config_missing(self):
        self._run_main_test(['--step', 'required-step-config-test'], 200, [
            {
                'name': 'tssc-config.yaml',
                'contents': '''---
                tssc-config: {}
                '''
            }]
        )

    def test_required_step_config_pass_via_config_file(self):
        self._run_main_test(['--step', 'required-step-config-test'], None,[
            {
                'name': 'tssc-config.yaml',
                'contents': '''---
                    tssc-config:
                        required-step-config-test:
                            implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                            config:
                                required-config-key: "hello world"
                '''
            }]
        )

    def test_required_step_config_pass_via_runtime_arg_missing(self):
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
                    tssc-config:
                        'required-runtime-step-config-test':
                             implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                             config: {}
                    '''
                }
            ]
        )

    def test_required_step_config_pass_via_runtime_arg_valid(self):
        self._run_main_test(
            [
                '--step', 'required-step-config-test',
                '--step-config', 'required-config-key="hello world"'
            ],
            None,
            [
                {
                    'name': 'tssc-config.yaml',
                    'contents': '''---
                    tssc-config:
                        'required-step-config-test':
                             implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                             config: {}
                    '''
                }
            ]
        )

    def test_multiple_config_files_verify_required_key_not_overwritten(self):
        self._run_main_test(
            ['--step', 'required-step-config-test'],
            None,
            [
                {
                    'name': 'tssc-config1.yaml',
                    'contents': '''---
                        tssc-config:
                            required-step-config-test:
                                implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
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
                                implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                                config:
                                    key2: "goodbye world"
                    '''
                }
            ]
        )

    def test_multiple_config_files_verify_expected_merge(self):
        self._run_main_test(
            ['--step', 'write-config-as-results'],
            None,
            [
                {
                    'name': 'tssc-config1.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
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
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
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
        self._run_main_test(
            ['--step', 'required-step-config-test'],
            102,
            [
                {
                    'name': 'tssc-config1.yaml',
                    'contents': '''---
                        tssc-config:
                            required-step-config-test:
                                implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
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
                                implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                                config:
                                    bar: "goodbye world"
                    '''
                }
            ]
        )

    def test_multiple_config_files_from_dir(self):
        args = ['--step', 'write-config-as-results']

        with TempDirectory() as temp_dir:
            config_files = [
                {
                    'name': 'tssc-config1.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    required-config-key: 'value'
                    '''
                },
                {
                    'name': 'foo/a.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    keya: "a"

                    '''
                },
                {
                    'name': 'foo/b.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    keyb: "b"
                    '''
                },
                {
                    'name': 'foo/bar/c.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    keyc: "c"
                    '''
                },
                {
                    'name': 'foo/bar2/c2.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    keyc2: "c2"
                    '''
                },
                {
                    'name': 'foo/bar/meh/d.yaml',
                    'contents': '''---
                        tssc-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
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

    def test_encrypted_value_no_decryptor(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'tssc-config-secret-stuff.yml'
        )

        config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'tssc-config.yml'
        )

        self._run_main_test(
            argv=[
                '--step', 'required-step-config-test',
                '--environment', 'DEV'
            ],
            config_files=[encrypted_config_file_path, config_file_path],
            expected_results={
                'tssc-results': {
                    'required-step-config-test': {
                        'environment-name': 'DEV',
                        'kube-api-token':'ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
                        'required-config-key':'ENC[AES256_GCM,data:McsZ87srP8gCRNDOysExE/XJ6OaCGyAT3lmNcPXnNvwrucMrBQ==,iv:0cmnMa3tRDaHHdRekzUR57KgGj9fdCLGnWpD+1TUAyM=,tag:svFAjgdBI+mmqopwgKlRFg==,type:str]'
                    }
                }
            }
        )

    @patch('sh.sops', create=True)
    def test_encrypted_value_with_sops_decryptor(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'tssc-config-secret-stuff.yml'
        )

        config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'tssc-config.yml'
        )

        decryptors_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'tssc-config-decryptors.yml'
        )

        mock_decrypted_value = 'mock decrypted value'
        sops_mock.side_effect=create_sops_side_effect(mock_decrypted_value)
        self._run_main_test(
            argv=[
                '--step', 'required-step-config-test',
                '--environment', 'DEV'
            ],
            config_files=[encrypted_config_file_path, config_file_path, decryptors_config_file_path],
            expected_results={
                'tssc-results': {
                    'required-step-config-test': {
                        'environment-name': 'DEV',
                        'kube-api-token': mock_decrypted_value,
                        'required-config-key': mock_decrypted_value
                    }
                }
            }
        )
