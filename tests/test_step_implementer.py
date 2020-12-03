# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os

from testfixtures import TempDirectory
from tssc.config import Config
from tssc.exceptions import StepRunnerException
from tssc.factory import TSSCFactory
from tssc.workflow_result import WorkflowResult

from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.sample_step_implementers import (
    FailStepImplementer, FooStepImplementer,
    WriteConfigAsResultsStepImplementer)


class TestStepImplementer(BaseStepImplementerTestCase):
    def _run_step_implementer_test(
            self,
            config,
            step,
            expected_step_results,
            test_dir,
            environment=None):
        working_dir_path = os.path.join(test_dir.path, 'tssc-working')
        results_dir_path = os.path.join(test_dir.path, 'tssc-results')
        factory = TSSCFactory(config, results_dir_path, 'tssc-results.yml', working_dir_path)
        factory.run_step(
            step_name=step,
            environment=environment
        )

        pickle = f'{working_dir_path}/tssc-results.pkl'
        workflow_results = WorkflowResult.load_from_pickle_file(pickle)
        step_results = workflow_results.get_step_result(step)
        self.assertEqual(expected_step_results, step_results)

    def test_one_step_writes_to_empty_results_file(self):
        config1 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer':
                        'tests.helpers.sample_step_implementers.'
                        'WriteConfigAsResultsStepImplementer',
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
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'}
                        }
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results,
                test_dir
            )

    def test___merge_results_from_running_same_step_twice_with_different_config(self):
        config1 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': 'config-1',
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }
        config1_expected_step_results = {
            'tssc-results': {
                'write-config-as-results': {
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'}
                        }
                    }
                }
            }
        }
        config2 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
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
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'config-2':
                                {'description': '', 'value': 'config-2'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-2'},
                            'required-config-key':
                                {'description': '', 'value': 'required'},
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                        }
                    }
                }
            }
        }

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

    def test___merge_results_from_two_sub_steps(self):
        config = {
            'tssc-config': {
                'write-config-as-results': [
                    {
                        'name': 'sub-step-1',
                        'implementer': 'tests.helpers.sample_step_implementers.'
                                       'WriteConfigAsResultsStepImplementer',
                        'config': {
                            'config-1': "config-1",
                            'config-overwrite-me': 'config-1',
                            'required-config-key': 'required'
                        }
                    },
                    {
                        'name': 'sub-step-2',
                        'implementer': 'tests.helpers.sample_step_implementers.'
                                       'WriteConfigAsResultsStepImplementer',
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
                    'sub-step-1': {
                        'sub-step-implementer-name': 'tests.helpers.sample_step_implementers.'
                                                     'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'}
                        },
                    },
                    'sub-step-2': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'config-2':
                                {'description': '', 'value': 'config-2'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-2'},
                            'required-config-key':
                                {'description': '', 'value': 'required'}
                        },
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config,
                'write-config-as-results',
                config_expected_step_results,
                test_dir
            )

    def test_one_step_existing_results_file_bad_pickle(self):
        config = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-working')
            results_file_path = os.path.join(results_dir_path, 'tssc-results.pkl')
            test_dir.write(results_file_path, b'''{}bad[yaml}''')

            with self.assertRaisesRegex(
                    StepRunnerException,
                    r'error loading .*'):
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
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'required-config-key': False
                    }
                }
            }
        }
        config_expected_step_results = {
            'tssc-results': {
                'write-config-as-results': {
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'required-config-key':
                                {'description': '', 'value': False}
                        }
                    }
                }
            }
        }

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
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
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
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'}
                        }
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-working')
            results_file_path = os.path.join(results_dir_path, 'tssc-results.pkl')
            test_dir.write(results_file_path, b'''''')
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
                    'implementer':
                        'tests.helpers.sample_step_implementers.'
                        'WriteConfigAsResultsStepImplementer',
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
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'environment-name':
                                {'description': '', 'value': 'SAMPLE-ENV-1'},
                            'sample-config-option-1':
                                {'description': '', 'value': 'sample env 1 value'},
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'},
                        }
                    }
                }
            }
        }
        config1_expected_step_results_env_2 = {
            'tssc-results': {
                'write-config-as-results': {
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'environment-name':
                                {'description': '', 'value': 'SAMPLE-ENV-2'},
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'sample-config-option-1':
                                {'description': '', 'value': 'sample env 2 value'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'}
                        }
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_1,
                test_dir,
                'SAMPLE-ENV-1'
            )

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
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
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
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'},
                            'sample-config-option-1': {
                                'description': '',
                                'value': 'step env config - env 1 value'
                            }
                        }
                    }
                }
            }
        }
        config1_expected_step_results_env_2 = {
            'tssc-results': {
                'write-config-as-results': {
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'},
                            'sample-config-option-1': {
                                'description': '',
                                'value': 'step env config - env 2 value'
                            }
                        }
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_1,
                test_dir,
                'SAMPLE-ENV-1'
            )

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
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
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
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'environment-name':
                                {'description': '', 'value': 'SAMPLE-ENV-1'},
                            'sample-config-option-1': {
                                'description': '',
                                 'value': 'step env config - env 1 value - 1'
                                },
                            'sample-config-option-2': {
                                'description': '',
                                 'value': 'global env config - env 1 value - 2'
                            },
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'},
                        }
                    }
                }
            }
        }
        config1_expected_step_results_env_2 = {
            'tssc-results': {
                'write-config-as-results': {
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'environment-name':
                                {'description': '', 'value': 'SAMPLE-ENV-2'},
                            'sample-config-option-1': {
                                'description': '',
                                 'value': 'step env config - env 2 value - 1'
                            },
                            'sample-config-option-2': {
                                'description': '',
                                'value': 'global env config - env 2 value - 2'
                            },
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'},
                        }
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_1,
                test_dir,
                'SAMPLE-ENV-1'
            )

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_2,
                test_dir,
                'SAMPLE-ENV-2'
            )

    def test_empty_constructor_params(self):
        config = Config({
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer'
                }
            }
        })
        step_config = config.get_step_config('write-config-as-results')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.'
            'WriteConfigAsResultsStepImplementer')

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
                    'implementer':
                        'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer',
                    'config': {}
                }
            }
        }

        expected_results = {
            'tssc-results': {
                'required-step-config-test': {
                    'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'RequiredStepConfigStepImplementer',
                        'success': False,
                        'message':
                            "Missing required step configuration"
                            " or previous step result artifact keys: ['required-config-key']",
                        'artifacts': {},
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config,
                'required-step-config-test',
                expected_results,
                test_dir
            )

    def test_get_step_result(self):
        config = Config({
            'tssc-config': {
                'write-config-as-results': {
                    'implementer':
                        'tests.helpers.sample_step_implementers.'
                        'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'foo': "bar",
                    }
                },
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        write_config_as_results_step_config = config.get_step_config('write-config-as-results')
        write_config_as_results_step_config_sub_step = \
            write_config_as_results_step_config.get_sub_step(
                'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer')

        foo_step_config = config.get_step_config('foo')
        foo_sub_step = foo_step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-working')
            write_config_step = WriteConfigAsResultsStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.pkl',
                work_dir_path='tssc-working',
                config=write_config_as_results_step_config_sub_step
            )

            write_config_step.run_step()

            # verify step can return it's own results
            results_from_same_step = write_config_step.get_step_result()
            expected_results = {
                'tssc-results': {
                    'write-config-as-results': {
                        'tests.helpers.sample_step_implementers.'
                        'WriteConfigAsResultsStepImplementer': {
                            'sub-step-implementer-name':
                                'tests.helpers.sample_step_implementers.'
                                'WriteConfigAsResultsStepImplementer',
                            'success': True,
                            'message': '',
                            'artifacts': {
                                'config-1': {'description': '', 'value': 'config-1'},
                                'foo': {'description': '', 'value': 'bar'}
                            },
                        }
                    }
                }
            }
            self.assertEqual(expected_results, results_from_same_step)

            # # verify step can return results from a previous step
            foo_step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.pkl',
                work_dir_path='tssc-working',
                config=foo_sub_step
            )

            results_from_diff_step = foo_step.get_step_result('write-config-as-results')
            self.assertEqual(results_from_diff_step, expected_results)

            expected_results = foo_step.get_result_value(artifact_name='foo')
            self.assertEqual('bar', expected_results)

    def test_write_working_file(self):
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step
            )

            step.write_working_file('test-working-file', b'hello world')

            with open(os.path.join(working_dir_path, 'foo', 'test-working-file'), 'r') \
                    as working_file:
                self.assertEqual(working_file.read(), 'hello world')

    def test_write_working_file_touch(self):
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step
            )

            step.write_working_file('foo/test.json')

            working_file_path = os.path.join(working_dir_path, 'foo/foo/test.json')
            self.assertTrue(os.path.exists(working_file_path))

            with open(working_file_path, 'r') as working_file:
                self.assertEqual(working_file.read(), '')

    def test_get_config_value(self):
        step_config = {
            'test': 'hello world'
        }

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            step = self.create_given_step_implementer(
                step_implementer=FooStepImplementer,
                step_config=step_config,
                step_name='foo',
                implementer='FooStepImplementer',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )

            self.assertEqual(step.get_config_value('test'), 'hello world')
            self.assertIsNone(step.get_config_value('does-not-exist'))

    def test_get_config_value_with_env(self):
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {
                        'test': 'hello world',
                        'env-config-override-key': 'override-me'
                    },
                    'environment-config': {
                        'SAMPLE-ENV-1': {
                            'env-config-override-key': 'step env config - env 1 value - 1'
                        },
                        'SAMPLE-ENV-2': {
                            'env-config-override-key': 'step env config - env 2 value - 1'
                        }
                    },
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step,
                environment='SAMPLE-ENV-1'
            )

            self.assertEqual(step.get_config_value('test'), 'hello world')
            self.assertIsNone(step.get_config_value('does-not-exist'))
            self.assertEqual(
                step.get_config_value('env-config-override-key'),
                'step env config - env 1 value - 1')

    def test_has_config_value(self):
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {
                        'test': 'hello world',
                        'env-config-override-key': 'override-me',
                        'username': 'foo',
                        'password': 'bar'
                    },
                    'environment-config': {
                        'SAMPLE-ENV-1': {
                            'env-config-override-key': 'step env config - env 1 value - 1'
                        },
                        'SAMPLE-ENV-2': {
                            'env-config-override-key': 'step env config - env 2 value - 1'
                        }
                    },
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step,
                environment='SAMPLE-ENV-1'
            )

            self.assertFalse(step.has_config_value('bar'))
            self.assertFalse(step.has_config_value(['bar']))

            self.assertFalse(step.has_config_value(['username', 'foo'], False))
            self.assertTrue(step.has_config_value(['username', 'foo'], True))

            self.assertTrue(step.has_config_value(['username', 'password'], False))
            self.assertTrue(step.has_config_value(['username', 'password'], True))

    def test_fail(self):
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FailStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FailStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            step = FailStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step
            )
            result = step.run_step()

        self.assertEqual(False, result)

    def test_create_working_dir_sub_dir(self):
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step
            )

            sub = step.create_working_dir_sub_dir('folder1')
            self.assertEqual(sub, f'{working_dir_path}/foo/folder1')
            self.assertEqual(True, os.path.isdir(sub))

            sub = step.create_working_dir_sub_dir('folder1/folder2/folder3')
            self.assertEqual(sub, f'{working_dir_path}/foo/folder1/folder2/folder3')
            self.assertEqual(True, os.path.isdir(sub))

    def test_result_files_and_paths(self):
        # overkill on tests here
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'myresults')
            working_dir_path = os.path.join(test_dir.path, 'mytesting')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='myfile',
                work_dir_path=working_dir_path,
                config=sub_step
            )

            self.assertEqual(
                f'{results_dir_path}/myfile',
                step.results_file_path
            )

            self.assertEqual(
                f'{results_dir_path}',
                step.results_dir_path
            )

            self.assertEqual(
                f'{working_dir_path}',
                step.work_dir_path
            )

            self.assertEqual(
                f'{working_dir_path}/foo',
                step.work_dir_path_step
            )

            self.assertEqual(
                f'{working_dir_path}/myfile.pkl',
                step._StepImplementer__workflow_result_pickle_file_path
            )

    def test_get_value(self):
        step_config = {
            'test': 'hello world'
        }

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            artifact_config = {
                'fake-previous-step-artifact': {
                    'description': '',
                    'value': 'world hello'
                },
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step = self.create_given_step_implementer(
                step_implementer=FooStepImplementer,
                step_config=step_config,
                step_name='foo',
                implementer='FooStepImplementer',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )

            self.assertEqual(step.get_value('test'), 'hello world')
            self.assertEqual(step.get_value('fake-previous-step-artifact'), 'world hello')
            self.assertIsNone(step.get_value('does-not-exist'))
