# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os

from testfixtures import TempDirectory
from ploigos_step_runner import StepResult
from ploigos_step_runner.config import Config
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_runner import StepRunner
from ploigos_step_runner.workflow_result import WorkflowResult

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
        working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
        results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
        factory = StepRunner(config, results_dir_path, 'step-runner-results.yml', working_dir_path)
        factory.run_step(
            step_name=step,
            environment=environment
        )

        pickle = f'{working_dir_path}/step-runner-results.pkl'
        workflow_results = WorkflowResult.load_from_pickle_file(pickle)

        step_result = workflow_results.get_step_result(
            step_name=step
        )
        self.assertEqual(expected_step_results, step_result.get_step_result_dict())

    def test_one_step_writes_to_empty_results_file(self):
        config1 = {
            'step-runner-config': {
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

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results,
                test_dir
            )

    def test_one_step_existing_results_file_bad_pickle(self):
        config = {
            'step-runner-config': {
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
            results_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            results_file_path = os.path.join(results_dir_path, 'step-runner-results.pkl')
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
            'step-runner-config': {
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

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config,
                'write-config-as-results',
                config_expected_step_results,
                test_dir
            )

    def test_one_step_existing_results_file_empty(self):
        config = {
            'step-runner-config': {
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

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            results_file_path = os.path.join(results_dir_path, 'step-runner-results.pkl')
            test_dir.write(results_file_path, b'''''')
            self._run_step_implementer_test(
                config,
                'write-config-as-results',
                config_expected_step_results,
                test_dir
            )

    def test_global_environment_default_config(self):
        config1 = {
            'step-runner-config': {
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
            'SAMPLE-ENV-1': {
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
            'SAMPLE-ENV-2': {
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
            'step-runner-config': {
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
            'SAMPLE-ENV-1': {
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
            'SAMPLE-ENV-2': {
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
            'step-runner-config': {
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
            'SAMPLE-ENV-1': {
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
            'SAMPLE-ENV-2': {
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
            'step-runner-config': {
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
            'step-runner-config': {
                'required-step-config-test': {
                    'implementer':
                        'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer',
                    'config': {}
                }
            }
        }

        expected_results = {
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

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config,
                'required-step-config-test',
                expected_results,
                test_dir
            )

    def test_write_working_file(self):
        config = Config({
            'step-runner-config': {
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
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='step-runner-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step
            )

            step.write_working_file('test-working-file', b'hello world')

            with open(os.path.join(working_dir_path, 'foo', 'test-working-file'), 'r') \
                    as working_file:
                self.assertEqual(working_file.read(), 'hello world')

    def test_write_working_file_touch(self):
        config = Config({
            'step-runner-config': {
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
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='step-runner-results.yml',
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
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
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
            'step-runner-config': {
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
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='step-runner-results.yml',
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
            'step-runner-config': {
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
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='step-runner-results.yml',
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
            'step-runner-config': {
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
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FailStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='step-runner-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step
            )
            result = step.run_step()

        self.assertEqual(False, result)

    def test_create_working_dir_sub_dir(self):
        config = Config({
            'step-runner-config': {
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
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='step-runner-results.yml',
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
            'step-runner-config': {
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

    def test_get_value_no_env(self):
        step_config = {
            'test': 'hello world'
        }

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
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

    def __setup_get_value_with_env_test(self, test_dir, environment):
        step_config = {
            'test': 'hello world'
        }

        results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
        results_file_name = 'step-runner-results.yml'
        work_dir_path = os.path.join(test_dir.path, 'working')

        workflow_result = WorkflowResult()

        step_result_deploy_test = StepResult(
            step_name='deploy',
            sub_step_name='ArgoCD',
            sub_step_implementer_name='ArgoCD',
            environment='TEST'
        )
        step_result_deploy_test.add_artifact(
            name='deployed-host-urls',
            value='https://awesome-app.test.ploigos.xyz'
        )
        workflow_result.add_step_result(step_result=step_result_deploy_test)

        step_result_deploy_prod = StepResult(
            step_name='deploy',
            sub_step_name='ArgoCD',
            sub_step_implementer_name='ArgoCD',
            environment='PROD'
        )
        step_result_deploy_prod.add_artifact(
            name='deployed-host-urls',
            value='https://awesome-app.prod.ploigos.xyz'
        )
        workflow_result.add_step_result(step_result=step_result_deploy_prod)
        pickle_filename = os.path.join(work_dir_path, 'step-runner-results.pkl')
        workflow_result.write_to_pickle_file(pickle_filename=pickle_filename)

        return self.create_given_step_implementer(
            step_implementer=FooStepImplementer,
            step_config=step_config,
            step_name='foo',
            implementer='FooStepImplementer',
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path,
            environment=environment
        )

    def test_get_value_from_step_not_run_against_specific_environment(self):
        with TempDirectory() as test_dir:
            step = self.__setup_get_value_with_env_test(test_dir=test_dir, environment=None)
            self.assertEqual(
                step.get_value('deployed-host-urls'),
                'https://awesome-app.test.ploigos.xyz'
            )

    def test_get_value_from_step_run_in_environment_that_has_result_value_for_that_environment_1(self):
        with TempDirectory() as test_dir:
            step = self.__setup_get_value_with_env_test(test_dir=test_dir, environment='TEST')
            self.assertEqual(
                step.get_value('deployed-host-urls'),
                'https://awesome-app.test.ploigos.xyz'
            )

    def test_get_value_from_step_run_in_environment_that_has_result_value_for_that_environment_2(self):
        with TempDirectory() as test_dir:
            step = self.__setup_get_value_with_env_test(test_dir=test_dir, environment='PROD')
            self.assertEqual(
                step.get_value('deployed-host-urls'),
                'https://awesome-app.prod.ploigos.xyz'
            )

    def test_get_value_from_step_run_in_environment_that_nodes_not_have_result_value_for_that_environment(self):
        with TempDirectory() as test_dir:
            step = self.__setup_get_value_with_env_test(test_dir=test_dir, environment='RANDOM')
            self.assertEqual(
                step.get_value('deployed-host-urls'),
                'https://awesome-app.test.ploigos.xyz'
            )
