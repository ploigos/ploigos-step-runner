# pylint: disable=line-too-long
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from unittest.mock import patch

import os
import yaml
from testfixtures import TempDirectory

from ploigos_step_runner.__main__ import main

from tests.helpers.base_test_case import BaseTestCase
from tests.helpers.test_utils import create_sops_side_effect


class TestInit(BaseTestCase):
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

            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            argv.append('--results-dir')
            argv.append(results_dir_path)

            if expected_exit_code is not None:
                with self.assertRaisesRegex(SystemExit, f"{expected_exit_code}") as cm:
                    main(argv)
            else:
                main(argv)

                if expected_results:
                    with open(os.path.join(results_dir_path, "step-runner-results.yml"), 'r') as step_results_file:
                        results = yaml.safe_load(step_results_file.read())
                        print(expected_results)
                        print(results)
                        self.assertEqual(results, expected_results)

    def test_init(self):
        """
        Notes
        -----
        See https://medium.com/opsops/how-to-test-if-name-main-1928367290cb
        """
        from ploigos_step_runner import __main__
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
        self._run_main_test(['--step', 'generate-metadata'], 102, [
            {
                'name': 'step-runner-config.yaml',
                'contents': ": blarg this: is {} bad syntax"
            }]
                            )

    def test_config_file_no_root_config_key(self):
        self._run_main_test(['--step', 'generate-metadata'], 102, [
            {
                'name': 'step-runner-config.yaml',
                'contents': '{}'
            }]
                            )

    def test_config_file_valid_yaml(self):
        self._run_main_test(['--step', 'foo'], None, [
            {
                'name': 'step-runner-config.yaml',
                'contents': '''---
                step-runner-config:
                    foo:
                        implementer: 'tests.helpers.sample_step_implementers.FooStepImplementer'
                '''
            }]
                            )

    def test_config_file_valid_json(self):
        self._run_main_test(['--step', 'foo'], None, [
            {
                'name': 'step-runner-config.json',
                'contents': '''
                {
                    "step-runner-config": {
                        "foo": {
                        "implementer": 'tests.helpers.sample_step_implementers.FooStepImplementer'
                        }
                    }
                }
                '''
            }]
                            )

    def test_required_step_config_missing(self):
        self._run_main_test(['--step', 'required-step-config-test'], 300, [
            {
                'name': 'step-runner-config.yaml',
                'contents': '''---
                step-runner-config: {}
                '''
            }]
                            )

    def test_required_step_config_pass_via_config_file(self):
        self._run_main_test(['--step', 'required-step-config-test'], None, [
            {
                'name': 'step-runner-config.yaml',
                'contents': '''---
                    step-runner-config:
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
                    'name': 'step-runner-config.yaml',
                    'contents': '''---
                    step-runner-config:
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
                    'name': 'step-runner-config.yaml',
                    'contents': '''---
                    step-runner-config:
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
                    'name': 'step-runner-config1.yaml',
                    'contents': '''---
                        step-runner-config:
                            required-step-config-test:
                                implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                                config:
                                    required-config-key: "hello world"
                                    bar: 'test'
                    '''
                },
                {
                    'name': 'step-runner-config2.yaml',
                    'contents': '''---
                        step-runner-config:
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
                    'name': 'step-runner-config1.yaml',
                    'contents': '''---
                        step-runner-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    key1: "value1"
                                    key2: "value1"
                    '''
                },
                {
                    'name': 'step-runner-config2.yaml',
                    'contents': '''---
                        step-runner-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    key3: "value2"
                                    required-config-key: 'value'
                    '''
                }
            ],
            {
                'step-runner-results': {
                    'write-config-as-results': {
                        'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer': {
                            'artifacts': {
                                'key1':
                                    {'description': '', 'value': 'value1'},
                                'key2':
                                    {'description': '', 'value': 'value1'},
                                'key3':
                                    {'description': '', 'value': 'value2'},
                                'required-config-key':
                                    {'description': '', 'value': 'value'}
                            },
                            'message': '',
                            'sub-step-implementer-name':
                                'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer',
                            'success': True
                        }
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
                    'name': 'step-runner-config1.yaml',
                    'contents': '''---
                        step-runner-config:
                            required-step-config-test:
                                implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                                config:
                                    required-config-key: "hello world"
                                    bar: 'test'
                    '''
                },
                {
                    'name': 'step-runner-config2.yaml',
                    'contents': '''---
                        step-runner-config:
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
                    'name': 'step-runner-config1.yaml',
                    'contents': '''---
                        step-runner-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    required-config-key: 'value'
                    '''
                },
                {
                    'name': 'foo/a.yaml',
                    'contents': '''---
                        step-runner-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    keya: "a"

                    '''
                },
                {
                    'name': 'foo/b.yaml',
                    'contents': '''---
                        step-runner-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    keyb: "b"
                    '''
                },
                {
                    'name': 'foo/bar/c.yaml',
                    'contents': '''---
                        step-runner-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    keyc: "c"
                    '''
                },
                {
                    'name': 'foo/bar2/c2.yaml',
                    'contents': '''---
                        step-runner-config:
                            write-config-as-results:
                                implementer: 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
                                config:
                                    keyc2: "c2"
                    '''
                },
                {
                    'name': 'foo/bar/meh/d.yaml',
                    'contents': '''---
                        step-runner-config:
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
            args.append(os.path.join(temp_dir.path, 'step-runner-config1.yaml'))
            self._run_main_test(
                args,
                None,
                None,
                {
                    'step-runner-results': {
                        'write-config-as-results': {
                            'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer': {
                                'artifacts': {
                                    'keya':
                                        {'description': '', 'value': 'a'},
                                    'keyb':
                                        {'description': '', 'value': 'b'},
                                    'keyc':
                                        {'description': '', 'value': 'c'},
                                    'keyc2':
                                        {'description': '', 'value': 'c2'},
                                    'keyd':
                                        {'description': '', 'value': 'd'},
                                    'required-config-key':
                                        {'description': '', 'value': 'value'}
                                },
                                'message': '',
                                'sub-step-implementer-name':
                                    'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer',
                                'success': True
                            }
                        }
                    }
                }
            )

    def test_encrypted_value_no_decryptor(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config.yml'
        )

        self._run_main_test(
            argv=[
                '--step', 'required-step-config-test',
                '--environment', 'DEV'
            ],
            config_files=[encrypted_config_file_path, config_file_path],
            expected_results={
                'step-runner-results': {
                    'DEV': {
                        'required-step-config-test': {
                            'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer': {
                                'artifacts': {
                                    'environment-name': {'description': '', 'value': 'DEV'},
                                    'kube-api-token': {
                                        'description': '',
                                        'value': 'ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]'},
                                    'required-config-key': {
                                        'description': '',
                                        'value': 'ENC[AES256_GCM,data:McsZ87srP8gCRNDOysExE/XJ6OaCGyAT3lmNcPXnNvwrucMrBQ==,iv:0cmnMa3tRDaHHdRekzUR57KgGj9fdCLGnWpD+1TUAyM=,tag:svFAjgdBI+mmqopwgKlRFg==,type:str]'}
                                },
                                'message': '',
                                'sub-step-implementer-name':
                                    'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer',
                                'success': True
                            }
                        }
                    }
                }
            }
        )

    @patch('sh.sops', create=True)
    def test_encrypted_value_with_sops_decryptor(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config.yml'
        )

        decryptors_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-decryptors.yml'
        )

        mock_decrypted_value = 'mock decrypted value'
        sops_mock.side_effect = create_sops_side_effect(mock_decrypted_value)
        self._run_main_test(
            argv=[
                '--step', 'required-step-config-test',
                '--environment', 'DEV'
            ],
            config_files=[encrypted_config_file_path, config_file_path, decryptors_config_file_path],
            expected_results={
                'step-runner-results': {
                    'DEV': {
                        'required-step-config-test': {
                            'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer': {
                                'artifacts': {
                                    'environment-name':
                                        {'description': '', 'value': 'DEV'},
                                    'kube-api-token':
                                        {'description': '', 'value': 'mock decrypted value'},
                                    'required-config-key': {
                                        'description': '',
                                        'value': 'mock decrypted value'}
                                },
                                'message': '',
                                'sub-step-implementer-name':
                                    'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer',
                                'success': True}
                        }
                    }
                }
            }
        )

    def test_fail(self):
        self._run_main_test(['--step', 'foo'], 200, [
            {
                'name': 'step-runner-config.yaml',
                'contents': '''---
                step-runner-config:
                    foo:
                        implementer: 'tests.helpers.sample_step_implementers.FailStepImplementer'
                '''
            }]
                            )

