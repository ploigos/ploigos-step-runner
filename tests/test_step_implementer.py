import unittest
from testfixtures import TempDirectory

import os
import yaml

from tssc import TSSCFactory, StepImplementer, TSSCException

class dummy_context_mgr():
    def __enter__(self):
        return None
    def __exit__(self, exc_type, exc_value, traceback):
        return False

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

class WriteTempFileStepImplementer(StepImplementer):
    @staticmethod
    def step_name():
        return 'write-temp-file'
    
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
        self.write_temp_file('test', b'hello world')
        return {}

class TestStepImplementer(unittest.TestCase):
    def _run_step_implementer_test(
            self,
            config,
            step,
            expected_step_results,
            test_dir,
            environment=None):
        
        results_dir_path = os.path.join(test_dir.path, 'tssc-results')
        factory = TSSCFactory(config, results_dir_path)
        factory.run_step(
            step_name=step,
            environment=environment
        )
    
        with open(os.path.join(results_dir_path, "tssc-results.yml"), 'r') as step_results_file:
            step_results = yaml.safe_load(step_results_file.read())
            self.assertEqual(step_results, expected_step_results)
    
    def test_one_step_writes_to_empty_results_file(self):
        config1 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }
        config1_expected_step_results = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1',
                    'required-config-key': 'required'
                }
            }
        }
    
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results,
                test_dir
            )
    
    def test_merge_results_from_running_same_step_twice_with_different_config(self):
        config1 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }
        config1_expected_step_results = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1',
                    'required-config-key': 'required'
                }
            }
        }
        config2 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-2': 'config-2',
                        'config-overwrite-me': 'config-2',
                        'required-config-key': 'required'
                    }
                }
            }
        }
        config2_expected_step_results = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-2': 'config-2',
                    'config-overwrite-me': 'config-2',
                    'required-config-key': 'required'
                }
            }
        }
    
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
    
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results,
                test_dir
            )
            self._run_step_implementer_test(
                config2,
                'write-config-as-results',
                config2_expected_step_results,
                test_dir
            )
    
    def test_merge_results_from_two_sub_steps(self):
        config = {
            'tssc-config': {
                'write-config-as-results': [
                    {
                        'implementer': 'WriteConfigAsResultsStepImplementer',
                        'config': {
                            'config-1': "config-1",
                            'config-overwrite-me': 'config-1',
                            'required-config-key': 'required'
                        }
                    },
                    {
                        'implementer': 'WriteConfigAsResultsStepImplementer',
                        'config': {
                            'config-2': 'config-2',
                            'config-overwrite-me': 'config-2',
                            'required-config-key': 'required'
                        }
                    }
                ]
            }
        }
        config_expected_step_results = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-2': 'config-2',
                    'config-overwrite-me': 'config-2',
                    'required-config-key': 'required'
                }
            }
        }
    
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
    
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config,
                'write-config-as-results',
                config_expected_step_results,
                test_dir
            )
    
    def test_one_step_existing_results_file_bad_yaml(self):
        config = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }
    
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            results_file_path = os.path.join(results_dir_path, 'tssc-results.yml')
            test_dir.write(results_file_path,b'''{}bad[yaml}''')

            with self.assertRaisesRegex(
                    TSSCException,
                    r"Existing results file \(.*\) has invalid yaml:"):
                self._run_step_implementer_test(
                    config,
                    'write-config-as-results',
                    None,
                    test_dir
                )
    
    def test_one_step_existing_results_file_missing_key(self):
        config = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }
    
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            results_file_path = os.path.join(results_dir_path, 'tssc-results.yml')
            test_dir.write(results_file_path,b'''not-expected-root-key-for-results: {}''')
    
            with self.assertRaisesRegex(
                    TSSCException,
                    r"Existing results file \(.*\) does not have expected top level element \(tssc-results\): \{'not-expected-root-key-for-results': \{\}\}"):
                self._run_step_implementer_test(
                    config,
                    'write-config-as-results',
                    None,
                    test_dir
                )
    
    def test_one_step_existing_results_file_empty(self):
        config = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }
    
        config_expected_step_results = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1',
                    'required-config-key': 'required'
                },
            }
        }
    
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            results_file_path = os.path.join(results_dir_path, 'tssc-results.yml')
            test_dir.write(results_file_path,b'''''')
            self._run_step_implementer_test(
                config,
                'write-config-as-results',
                config_expected_step_results,
                test_dir
            )

    def test_global_environment_default_config(self):
        config1 = {
            'tssc-config': {
                'global-environment-defaults': {
                    'SAMPLE-ENV-1': {
                        'sample-config-option-1': 'sample env 1 value'
                    },
                    'SAMPLE-ENV-2': {
                        'sample-config-option-1': 'sample env 2 value'
                    }
                },
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }
        config1_expected_step_results_env_1 = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1',
                    'required-config-key': 'required',
                    'sample-config-option-1': 'sample env 1 value'
                }
            }
        }
        config1_expected_step_results_env_2 = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1',
                    'required-config-key': 'required',
                    'sample-config-option-1': 'sample env 2 value'
                }
            }
        }
    
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_1,
                test_dir,
                'SAMPLE-ENV-1'
            )
        
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_2,
                test_dir,
                'SAMPLE-ENV-2'
            )

    def test_step_environment_config(self):
        config1 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    },
                    'environment-config': {
                        'SAMPLE-ENV-1': {
                            'sample-config-option-1': 'step env config - env 1 value'
                        },
                        'SAMPLE-ENV-2': {
                            'sample-config-option-1': 'step env config - env 2 value'
                        }
                    }
                }
            }
        }
        config1_expected_step_results_env_1 = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1',
                    'required-config-key': 'required',
                    'sample-config-option-1': 'step env config - env 1 value'
                }
            }
        }
        config1_expected_step_results_env_2 = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1',
                    'required-config-key': 'required',
                    'sample-config-option-1': 'step env config - env 2 value'
                }
            }
        }
    
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_1,
                test_dir,
                'SAMPLE-ENV-1'
            )
        
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_2,
                test_dir,
                'SAMPLE-ENV-2'
            )

    def test_global_environment_default_and_step_environment_config(self):
        config1 = {
            'tssc-config': {
                'global-environment-defaults': {
                    'SAMPLE-ENV-1': {
                        'sample-config-option-1': 'global env config - env 1 value - 1',
                        'sample-config-option-2': 'global env config - env 1 value - 2'
                    },
                    'SAMPLE-ENV-2': {
                        'sample-config-option-1': 'global env config - env 2 value - 1',
                        'sample-config-option-2': 'global env config - env 2 value - 2'
                    }
                },
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    },
                    'environment-config': {
                        'SAMPLE-ENV-1': {
                            'sample-config-option-1': 'step env config - env 1 value - 1'
                        },
                        'SAMPLE-ENV-2': {
                            'sample-config-option-1': 'step env config - env 2 value - 1'
                        }
                    },
                }
            }
        }
        config1_expected_step_results_env_1 = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1',
                    'required-config-key': 'required',
                    'sample-config-option-1': 'step env config - env 1 value - 1',
                    'sample-config-option-2': 'global env config - env 1 value - 2'
                }
            }
        }
        config1_expected_step_results_env_2 = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1',
                    'required-config-key': 'required',
                    'sample-config-option-1': 'step env config - env 2 value - 1',
                    'sample-config-option-2': 'global env config - env 2 value - 2'
                }
            }
        }
    
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_1,
                test_dir,
                'SAMPLE-ENV-1'
            )
        
        TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_2,
                test_dir,
                'SAMPLE-ENV-2'
            )

    def test_empty_constructor_params(self):
        step = WriteConfigAsResultsStepImplementer(
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
        )
        
        self.assertEqual(step.step_environment_config, {})
        self.assertEqual(step.step_config, {})
        self.assertEqual(step.global_config_defaults, {})
        self.assertEqual(step.global_environment_config_defaults, {})
