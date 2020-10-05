"""Test Step Implementer

Tests the step implementer.
"""
import os
from testfixtures import TempDirectory

import yaml

from tssc import TSSCFactory, TSSCException
from tssc.config import Config

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.sample_step_implementers import FooStepImplementer, \
    WriteConfigAsResultsStepImplementer

class TestStepImplementer(BaseTSSCTestCase):
    """Test step implementer"""

    # pylint: disable=too-many-arguments
    def _run_step_implementer_test(
            self,
            config,
            step,
            expected_step_results,
            test_dir,
            environment=None):
        """Run the step implementer test"""

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
        """Test step write to empty results file"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config1 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer,
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

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results,
                test_dir
            )

    def test_merge_results_from_running_same_step_twice_with_different_config(self):
        """Test merge results from running same step twice with different configs"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config1 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer,
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
                    'implementer': implementer,
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
        """Test merge results from two sub steps"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config = {
            'tssc-config': {
                'write-config-as-results': [
                    {
                        'name': 'sub-step-1',
                        'implementer': implementer,
                        'config': {
                            'config-1': "config-1",
                            'config-overwrite-me': 'config-1',
                            'required-config-key': 'required'
                        }
                    },
                    {
                        'name': 'sub-step-2',
                        'implementer': implementer,
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

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config,
                'write-config-as-results',
                config_expected_step_results,
                test_dir
            )

    def test_one_step_existing_results_file_bad_yaml(self):
        """Test step existing results with bad yaml file"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer,
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }

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
        """Test step existing results with missing key"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer,
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            results_file_path = os.path.join(results_dir_path, 'tssc-results.yml')
            test_dir.write(results_file_path,b'''not-expected-root-key-for-results: {}''')

            with self.assertRaisesRegex(
                    TSSCException,
                    r"Existing results file \(.*\) does not have expected top level element " \
                    r"\(tssc-results\): \{'not-expected-root-key-for-results': \{\}\}"
            ):
                self._run_step_implementer_test(
                    config,
                    'write-config-as-results',
                    None,
                    test_dir
                )

    def test_boolean_false_config_variable(self):
        """Test false config variable"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer,
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

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config,
                'write-config-as-results',
                config_expected_step_results,
                test_dir
            )

    def test_one_step_existing_results_file_empty(self):
        """Test step existing results with empty file"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer,
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
        """Test global env default config"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
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
                    'implementer': implementer,
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
        """Test step env config"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config1 = {
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer,
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
        """Test global env default and step env config"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
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
                    'implementer': implementer,
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
        """Test empty constructor params"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config = Config({
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer
                }
            }
        })
        step_config = config.get_step_config('write-config-as-results')
        sub_step = step_config.get_sub_step(implementer)

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
        """Test missing required config key"""
        implementer = 'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
        config = {
            'tssc-config': {
                'required-step-config-test': {
                    'implementer': implementer,
                    'config': {}
                }
            }
        }

        with self.assertRaisesRegex(
            AssertionError,
            r"The runtime step configuration \({}\) is missing the required configuration keys "
            r"\(\['required-config-key'\]\)"
        ):
            with TempDirectory() as test_dir:
                self._run_step_implementer_test(
                    config,
                    'required-step-config-test',
                    {},
                    test_dir
                )

    def test_get_step_results(self):
        """Test get step results"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config = Config({
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer,
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
        write_config_as_results_step_config_sub_step = (
            config.get_step_config('write-config-as-results').get_sub_step(implementer)
        )

        foo_step_config = config.get_step_config('foo')
        foo_sub_step = (
            foo_step_config
            .get_sub_step('tests.helpers.sample_step_implementers.FooStepImplementer')
        )

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
        """Test current step results"""
        implementer = 'tests.helpers.sample_step_implementers.WriteConfigAsResultsStepImplementer'
        config = Config({
            'tssc-config': {
                'write-config-as-results': {
                    'implementer': implementer,
                    'config': {
                        'config-1': "config-1",
                        'foo': "bar",
                    }
                }
            }
        })
        step_config = config.get_step_config('write-config-as-results')
        sub_step = step_config.get_sub_step(implementer)

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

    def test_write_working_file(self):
        """Test write working file"""
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = (
            step_config.get_sub_step('tests.helpers.sample_step_implementers.FooStepImplementer')
        )

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
            working_file_path = os.path.join(working_dir_path, 'foo', 'test-working-file')

            with open(working_file_path, 'r') as working_file:
                self.assertEqual(working_file.read(), 'hello world')

    def test_write_working_file_touch(self):
        """Test write working file touch"""
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = (
            step_config.get_sub_step('tests.helpers.sample_step_implementers.FooStepImplementer')
        )

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step
            )

            step.write_working_file('test.json')

            working_file_path = os.path.join(working_dir_path, 'foo/test.json')
            self.assertTrue(os.path.exists(working_file_path))

            with open(working_file_path, 'r') as working_file:
                self.assertEqual(working_file.read(), '')

    def test_get_config_value(self):
        """Test get config value"""
        config = Config({
            'tssc-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {
                        'test': 'hello world'
                    }
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = (
            step_config.get_sub_step('tests.helpers.sample_step_implementers.FooStepImplementer')
        )

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step
            )

            self.assertEqual(step.get_config_value('test'), 'hello world')
            self.assertIsNone(step.get_config_value('does-not-exist'))

    def test_get_config_value_with_env(self):
        """Test get config value with env"""
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
        sub_step = (
            step_config.get_sub_step('tests.helpers.sample_step_implementers.FooStepImplementer')
        )

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
        """Test has config value"""
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
        sub_step = (
            step_config.get_sub_step('tests.helpers.sample_step_implementers.FooStepImplementer')
        )

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

    def test_create_working_dir_sub_dir(self):
        """Test create sub directory in working directory"""
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
        sub_step = (
            step_config.get_sub_step('tests.helpers.sample_step_implementers.FooStepImplementer')
        )

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'tssc-results')
            working_dir_path = os.path.join(test_dir.path, 'tssc-working')
            new_dir_path = os.path.join(working_dir_path, 'foo', 'test')
            step = FooStepImplementer(
                results_dir_path=results_dir_path,
                results_file_name='tssc-results.yml',
                work_dir_path=working_dir_path,
                config=sub_step,
                environment='SAMPLE-ENV-1'
            )

            self.assertFalse(
                os.path.isdir(new_dir_path),
                msg='Sub directory in working directory should not exist yet'
            )
            new_dir_created_path = step.create_working_dir_sub_dir('test')
            self.assertTrue(
                new_dir_created_path == new_dir_path,
                msg='Sub directory created in the wrong place'
            )
            self.assertTrue(
                os.path.isdir(new_dir_path),
                msg='Sub directory in working directory should exist'
            )
