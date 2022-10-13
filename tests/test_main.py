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


class TestMain(BaseTestCase):
    def _run_main_test(
        self,
        argv,
        expected_exit_code=None,
        config_files=None,
        expected_results=None
    ):
        cwd = os.getcwd()

        if argv is None:
            argv = []

        try:
            with TempDirectory() as temp_dir:
                os.chdir(temp_dir.path)

                if config_files:
                    for config_file in config_files:
                        if isinstance(config_file, dict):
                            config_file_name = config_file['name']
                            config_file_contents = config_file['contents']

                            temp_dir.write(config_file_name, bytes(config_file_contents, 'utf-8'))
                            config_file_path = os.path.join(temp_dir.path, config_file_name)

                if expected_exit_code is not None:
                    with self.assertRaisesRegex(SystemExit, f"{expected_exit_code}") as cm:
                        main(argv)
                else:
                    main(argv)

                    if expected_results:
                        work_dir_path = os.path.join(temp_dir.path, 'step-runner-working')
                        with open(os.path.join(work_dir_path, "step-runner-results.yml"), 'r') as step_results_file:
                            results = yaml.safe_load(step_results_file.read())
                            self.assertCountEqual(results, expected_results)
        finally:
            os.chdir(cwd)

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
        self._run_main_test(None, expected_exit_code=2)

    def test_help(self):
        self._run_main_test(['--help'], expected_exit_code=0)

    def test_bad_arg(self):
        self._run_main_test(['--bad-arg'], expected_exit_code=2)

    def test_config_file_does_not_exist(self):
        self._run_main_test(
            ['--step', 'generate-metadata', '--config', 'does-not-exist.yml'],
            expected_exit_code=101
        )

    def test_config_file_not_json_or_yaml(self):
        config_files = [
            {
                'name': 'psr.yaml',
                'contents': ": blarg this: is {} bad syntax"
            }
        ]
        self._run_main_test(
            ['--step', 'generate-metadata'],
            expected_exit_code=102,
            config_files=config_files
        )

    def test_config_file_no_root_config_key(self):
        config_files = [
                {
                    'name': 'psr.yaml',
                    'contents': '{}'
                }
            ]
        self._run_main_test(
            ['--step', 'generate-metadata'],
            expected_exit_code=102,
            config_files=config_files
        )

    def test_config_file_valid_yaml(self):
        config_files = [
            {
                'name': 'psr.yaml',
                'contents': '''---
                step-runner-config:
                    foo:
                        implementer: 'tests.helpers.sample_step_implementers.FooStepImplementer'
                '''
            }
        ]
        self._run_main_test(
            ['--step', 'foo'],
            config_files=config_files
        )

    def test_config_file_valid_json(self):
        config_files = [
            {
                'name': 'psr.json',
                'contents': '''
                {
                    "step-runner-config": {
                        "foo": {
                        "implementer": 'tests.helpers.sample_step_implementers.FooStepImplementer'
                        }
                    }
                }
                '''
            }
        ]
        self._run_main_test(
            ['--step', 'foo', '--config', 'psr.json'],
            config_files=config_files
        )

    def test_required_step_config_missing(self):
        config_files = [
            {
                'name': 'psr.yaml',
                'contents': '''---
                step-runner-config: {}
                '''
            }
        ]
        self._run_main_test(
            ['--step', 'required-step-config-test'],
            expected_exit_code=300,
            config_files=config_files
        )

    def test_required_step_config_pass_via_config_file(self):
        config_files = [
            {
                'name': 'psr.yaml',
                'contents': '''---
                    step-runner-config:
                        required-step-config-test:
                            implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                            config:
                                required-config-key: "hello world"
                '''
            }
        ]
        self._run_main_test(
            ['--step', 'required-step-config-test'],
            config_files=config_files
        )

    def test_required_step_config_pass_via_runtime_arg_missing(self):
        args = [
            '--step', 'required-runtime-step-config-test',
            '--step-config', 'wrong-config="hello world"'
        ]
        config_files = [
            {
                'name': 'psr.yaml',
                'contents': '''---
                step-runner-config:
                    'required-runtime-step-config-test':
                         implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                         config: {}
                '''
            }
        ]
        self._run_main_test(
            args,
            expected_exit_code=200,
            config_files=config_files
        )

    def test_required_step_config_pass_via_runtime_arg_valid(self):
        args = [
            '--step', 'required-step-config-test',
            '--step-config', 'required-config-key="hello world"'
        ]
        config_files = [
            {
                'name': 'psr.yaml',
                'contents': '''---
                step-runner-config:
                    'required-step-config-test':
                         implementer: 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
                         config: {}
                '''
            }
        ]
        self._run_main_test(args, config_files=config_files)

    def test_multiple_config_files_verify_required_key_not_overwritten(self):
        config_files = [
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
        self._run_main_test(
            ['--step', 'required-step-config-test',
             '--config', 'step-runner-config1.yaml', 'step-runner-config2.yaml'],
            config_files=config_files
        )

    def test_multiple_config_files_verify_expected_merge(self):
        config_files = [
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
        ]
        expected_results = {
            'step-runner-results': {
                'write-config-as-results': {
                    'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer': {
                        'artifacts': [
                            {'name': 'key1', 'description': '', 'value': 'value1'},
                            {'name': 'key2', 'description': '', 'value': 'value1'},
                            {'name': 'key3', 'description': '', 'value': 'value2'},
                            {'name': 'required-config-key', 'description': '', 'value': 'value'}
                        ],
                        'message': '',
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer',
                        'success': True
                    }
                }
            }
        }
        self._run_main_test(
            ['--step', 'write-config-as-results',
             '--config', 'step-runner-config1.yaml', 'step-runner-config2.yaml'],
            config_files=config_files,
            expected_results=expected_results
        )

    def test_multiple_config_files_dup_keys_error(self):
        config_files = [
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
        self._run_main_test(
            ['--step', 'required-step-config-test',
             '--config', 'step-runner-config1.yaml', 'step-runner-config2.yaml'],
            expected_exit_code=102,
            config_files=config_files
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

            expected_results = {
                'step-runner-results': {
                    'write-config-as-results': {
                        'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer': {
                            'artifacts': [
                                {'name': 'keyc2', 'description': '', 'value': 'c2'},
                                {'name': 'keya', 'description': '', 'value': 'a'},
                                {'name': 'keyd', 'description': '', 'value': 'd'},
                                {'name': 'keyc', 'description': '', 'value': 'c'},
                                {'name': 'keyb', 'description': '', 'value': 'b'},
                                {'name': 'required-config-key', 'description': '', 'value': 'value'}
                            ],
                            'message': '',
                            'sub-step-implementer-name':
                                'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer',
                            'success': True
                        }
                    }
                }
            }

            self._run_main_test(
                args,
                expected_results=expected_results
            )

    def test_encrypted_value_no_decryptor(self):
        config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config.yml'
        )
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )
        args = [
            '--step', 'required-step-config-test',
            '--config', config_file_path, encrypted_config_file_path,
            '--environment', 'DEV'
        ]
        expected_results = {
            'step-runner-results': {
                'DEV': {
                    'required-step-config-test': {
                        'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer': {
                            'artifacts':[
                                {'name': 'environment-name', 'description': '', 'value': 'DEV'},
                                {
                                    'name': 'kube-api-token',
                                    'description': '',
                                    'value': 'ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]'
                                },
                                {
                                    'name': 'required-config-key',
                                    'description': '',
                                    'value': 'ENC[AES256_GCM,data:McsZ87srP8gCRNDOysExE/XJ6OaCGyAT3lmNcPXnNvwrucMrBQ==,iv:0cmnMa3tRDaHHdRekzUR57KgGj9fdCLGnWpD+1TUAyM=,tag:svFAjgdBI+mmqopwgKlRFg==,type:str]'
                                }
                            ],
                            'message': '',
                            'sub-step-implementer-name':
                                'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer',
                            'success': True
                        }
                    }
                }
            }
        }
        self._run_main_test(
            args,
            config_files=[encrypted_config_file_path, config_file_path],
            expected_results=expected_results
        )

    @patch('sh.sops', create=True)
    def test_encrypted_value_with_sops_decryptor(self, sops_mock):
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
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )
        args = [
            '--step', 'required-step-config-test',
            '--config', config_file_path,
                        decryptors_config_file_path,
                        encrypted_config_file_path,
            '--environment', 'DEV'
        ]
        expected_results = {
            'step-runner-results': {
                'DEV': {
                    'required-step-config-test': {
                        'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer': {
                            'artifacts': [
                                {'name': 'environment-name', 'description': '', 'value': 'DEV'},
                                {'name': 'kube-api-token', 'description': '', 'value': 'mock decrypted value'},
                                {'name': 'required-config-key', 'description': '', 'value': 'mock decrypted value'}
                            ],
                            'message': '',
                            'sub-step-implementer-name':
                                'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer',
                            'success': True}
                    }
                }
            }
        }

        mock_decrypted_value = 'mock decrypted value'
        sops_mock.side_effect = create_sops_side_effect(mock_decrypted_value)

        self._run_main_test(
            args,
            config_files=[encrypted_config_file_path, config_file_path, decryptors_config_file_path],
            expected_results=expected_results
        )

    def test_fail(self):
        config_files = [
            {
                'name': 'psr.yaml',
                'contents': '''---
                step-runner-config:
                    foo:
                        implementer: 'tests.helpers.sample_step_implementers.FailStepImplementer'
                '''
            }
        ]
        self._run_main_test(
            ['--step', 'foo'],
            expected_exit_code=200,
            config_files=config_files
        )
