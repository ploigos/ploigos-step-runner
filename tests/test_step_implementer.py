import unittest
from testfixtures import TempDirectory

import os
import yaml

from tssc import TSSCFactory, StepImplementer, TSSCException, TSSCConfig

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.sample_step_implementers import *

class dummy_context_mgr():
    def __enter__(self):
        return None
    def __exit__(self, exc_type, exc_value, traceback):
        return False

class TestStepImplementer(BaseTSSCTestCase):
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
                        'name': 'sub-step-1',
                        'implementer': 'WriteConfigAsResultsStepImplementer',
                        'config': {
                            'config-1': "config-1",
                            'config-overwrite-me': 'config-1',
                            'required-config-key': 'required'
                        }
                    },
                    {
                        'name': 'sub-step-2',
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

    def test_boolean_false_config_variable(self):
        config = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                            'required-config-key': False
                    }
                }
            }
        }
        config_expected_step_results = {
            'tssc-results': {
                'write-config-as-results': {
                    'required-config-key': False
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
                    'environment-name': 'SAMPLE-ENV-1',
                    'required-config-key': 'required',
                    'sample-config-option-1': 'sample env 1 value'
                }
            }
        }
        config1_expected_step_results_env_2 = {
            'tssc-results': {
                'write-config-as-results': {
                    'config-1': "config-1",
                    'environment-name': 'SAMPLE-ENV-2',
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
                    'environment-name': 'SAMPLE-ENV-1',
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
                    'environment-name': 'SAMPLE-ENV-2',
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
        config = TSSCConfig({
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer'
                }
            }
        })
        step_config = config.get_step_config('write-config-as-results')
        sub_step = step_config.get_sub_step('WriteConfigAsResultsStepImplementer')

        step = WriteConfigAsResultsStepImplementer(
            results_dir_path='',
            results_file_name='',
            work_dir_path='',
            config=sub_step
        )

        self.assertEqual(step.step_environment_config, {})
        self.assertEqual(step.step_config, {})
        self.assertEqual(step.global_config_defaults, {})
        self.assertEqual(step.global_environment_config_defaults, {})

    def test_missing_required_config_key(self):
        config = {
            'tssc-config': {
                'required-step-config-test': {
                    'implementer': 'RequiredStepConfigStepImplementer',
                    'config': {}
                }
            }
        }

        with self.assertRaisesRegex(
                AssertionError,
                r"The runtime step configuration \({}\) is missing the required configuration keys \(\['required-config-key'\]\)"):

            TSSCFactory.register_step_implementer(RequiredStepConfigStepImplementer)
            with TempDirectory() as test_dir:
                self._run_step_implementer_test(
                    config,
                    'required-step-config-test',
                    {},
                    test_dir
                )

    def test_get_step_results(self):
        config = TSSCConfig({
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'foo': "bar",
                    }
                },
                'foo': {
                    'implementer': 'FooStepImplementer',
                    'config': {}
                }
            }
        })
        write_config_as_results_step_config = config.get_step_config('write-config-as-results')
        write_config_as_results_step_config_sub_step = write_config_as_results_step_config.get_sub_step('WriteConfigAsResultsStepImplementer')

        foo_step_config = config.get_step_config('foo')
        foo_sub_step = foo_step_config.get_sub_step('FooStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            write_config_step = WriteConfigAsResultsStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path='tssc-working',
                config=write_config_as_results_step_config_sub_step
            )

            write_config_step.run_step()

            # verify step can return it's own results
            results_from_same_step = write_config_step.get_step_results('write-config-as-results')
            self.assertEqual(results_from_same_step, {
                'config-1': "config-1",
                'foo': "bar",
            })

            # verify step can return results from a previous step
            foo_step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path='tssc-working',
                config=foo_sub_step
            )

            results_from_diff_step = foo_step.get_step_results('write-config-as-results')
            self.assertEqual(results_from_diff_step, {
                'config-1': "config-1",
                'foo': "bar",
            })

    def test_current_step_results(self):
        config = TSSCConfig({
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'foo': "bar",
                    }
                }
            }
        })
        step_config = config.get_step_config('write-config-as-results')
        sub_step = step_config.get_sub_step('WriteConfigAsResultsStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            step = WriteConfigAsResultsStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path='tssc-working',
                config=sub_step
            )

            step.run_step()
            results = step.current_step_results()

            self.assertEqual(results, {
                'config-1': "config-1",
                'foo': "bar",
            })

    def test_write_temp_file(self):
        config = TSSCConfig({
            'tssc-config': {
                'foo': {
                    'implementer': 'FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step('FooStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step
            )

            step.write_temp_file('test-working-file', b'hello world')

            with open(os.path.join(working_dir_path, 'foo', 'test-working-file'), 'r') as working_file:
                self.assertEqual(working_file.read(), 'hello world')

