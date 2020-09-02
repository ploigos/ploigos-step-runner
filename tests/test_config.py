import unittest
from testfixtures import TempDirectory

import os.path

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

from tssc.config import TSSCConfig, TSSCStepConfig, TSSCSubStepConfig

class TestTSSCConfig(BaseTSSCTestCase):
    def test_add_config_invalid_type(self):
        tssc_config = TSSCConfig()
        with self.assertRaisesRegex(
            ValueError,
            r"Given config \(True\) is unexpected type \(<class 'bool'>\) not a dictionary, string, or list of former."
        ):
            tssc_config.add_config(True)

    def test_add_config_dict_missing_config_key(self):
        tssc_config = TSSCConfig()
        with self.assertRaisesRegex(
            AssertionError,
            r"Failed to add invalid TSSC config. Missing expected top level key \(tssc-config\):"
        ):
            tssc_config.add_config({
                'foo': 'foo'
            })

    def test_add_config_dict_valid_basic(self):
        tssc_config = TSSCConfig()
        tssc_config.add_config({
            TSSCConfig.TSSC_CONFIG_KEY: {}
        })

        self.assertEqual(tssc_config.global_defaults, {})
        self.assertEqual(tssc_config.global_environment_defaults, {})

    def test_initial_config_dict_valid_basic(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {}
        })

        self.assertEqual(tssc_config.global_defaults, {})
        self.assertEqual(tssc_config.global_environment_defaults, {})

    def test_initial_config_dict_missing_config_key(self):
        with self.assertRaisesRegex(
            AssertionError,
            r"Failed to add invalid TSSC config. Missing expected top level key \(tssc-config\):"
        ):
            TSSCConfig({
                'foo': 'foo'
            })

    def test_add_config_file_missing_file(self):
        with TempDirectory() as temp_dir:
            tssc_config = TSSCConfig()
            with self.assertRaisesRegex(
                ValueError,
                r"Given config string \(.*\) is not a valid path."
            ):
                tssc_config.add_config(os.path.join(temp_dir.path, 'does-not-exist.yml'))

    def test_add_config_file_invalid_json_or_yaml(self):
        with TempDirectory() as temp_dir:
            config_file_name = "bad"
            config_file_contents = ": blarg this: is {} bad syntax"
            temp_dir.write(config_file_name, bytes(f"{config_file_contents}", 'utf-8'))

            tssc_config = TSSCConfig()
            with self.assertRaisesRegex(
                ValueError,
                r"Error parsing config file \(.*\) as json or yaml"
            ):
                tssc_config.add_config(os.path.join(temp_dir.path, config_file_name))

    def test_add_config_file_missing_config_key(self):
        with TempDirectory() as temp_dir:
            config_file_name = "foo.json"
            config_file_contents = {
                'foo': 'foo'
            }
            temp_dir.write(config_file_name, bytes(f"{config_file_contents}", 'utf-8'))

            tssc_config = TSSCConfig()
            with self.assertRaisesRegex(
                AssertionError,
                r"Failed to add parsed configuration file \(.*\): Failed to add invalid TSSC config. Missing expected top level key \(tssc-config\):"
            ):
                tssc_config.add_config(os.path.join(temp_dir.path, config_file_name))

    def test_add_config_file_valid_basic(self):
        with TempDirectory() as temp_dir:
            config_file_name = "foo.json"
            config_file_contents = {
                TSSCConfig.TSSC_CONFIG_KEY: {}
            }
            temp_dir.write(config_file_name, bytes(f"{config_file_contents}", 'utf-8'))

            tssc_config = TSSCConfig()
            tssc_config.add_config(os.path.join(temp_dir.path, config_file_name))

            self.assertEqual(tssc_config.global_defaults, {})
            self.assertEqual(tssc_config.global_environment_defaults, {})

    def test_add_config_dir_no_files(self):
        with TempDirectory() as temp_dir:
            tssc_config = TSSCConfig()
            with self.assertRaisesRegex(
                ValueError,
                r"Given config string \(.*\) is a directory with no recursive children files."
            ):
                tssc_config.add_config(temp_dir.path)

    def test_add_config_dir_one_valid_file(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {}
                    }
                }
            ]

            for config_file in config_files:
                config_file_name = config_file['name']
                config_file_contents = config_file['contents']
                temp_dir.write(
                    config_file_name,
                    bytes(f"{config_file_contents}", 'utf-8')
                )

            tssc_config = TSSCConfig()
            tssc_config.add_config(os.path.join(temp_dir.path, config_dir))

            self.assertEqual(tssc_config.global_defaults, {})
            self.assertEqual(tssc_config.global_environment_defaults, {})

    def test_add_config_dir_two_valid_file(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'step-test-foo' : {
                                'implementer': 'foo'
                            }
                        }
                    }
                },
                {
                    'name': os.path.join(config_dir,'bar.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'step-test-bar' : {
                                'implementer': 'bar'
                            }
                        }
                    }
                },
            ]

            for config_file in config_files:
                config_file_name = config_file['name']
                config_file_contents = config_file['contents']
                temp_dir.write(
                    config_file_name,
                    bytes(f"{config_file_contents}", 'utf-8')
                )

            tssc_config = TSSCConfig()
            tssc_config.add_config(os.path.join(temp_dir.path, config_dir))

            self.assertEqual(tssc_config.global_defaults, {})
            self.assertEqual(tssc_config.global_environment_defaults, {})

    def test_add_two_valid_files(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'step-test-foo' : {
                                'implementer': 'foo'
                            }
                        }
                    }
                },
                {
                    'name': os.path.join(config_dir,'bar.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'step-test-bar' : {
                                'implementer': 'bar'
                            }
                        }
                    }
                },
            ]

            for config_file in config_files:
                config_file_name = config_file['name']
                config_file_contents = config_file['contents']
                temp_dir.write(
                    config_file_name,
                    bytes(f"{config_file_contents}", 'utf-8')
                )

            tssc_config = TSSCConfig()
            tssc_config.add_config(
                [
                    os.path.join(temp_dir.path, config_dir, 'foo.yml'),
                    os.path.join(temp_dir.path, config_dir, 'bar.yml')
                ]
            )

            self.assertEqual(tssc_config.global_defaults, {})
            self.assertEqual(tssc_config.global_environment_defaults, {})

    def test_add_config_dir_one_valid_file_one_invalid_file(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {}
                    }
                },
                {
                    'name': os.path.join(config_dir,'bad.yml'),
                    'contents' : {
                        'bad': {
                            'implementer': 'bar'
                        }
                    }
                }
            ]

            for config_file in config_files:
                config_file_name = config_file['name']
                config_file_contents = config_file['contents']
                temp_dir.write(
                    config_file_name,
                    bytes(f"{config_file_contents}", 'utf-8')
                )

            tssc_config = TSSCConfig()
            with self.assertRaisesRegex(
                AssertionError,
                r"Failed to add parsed configuration file \(.*\): Failed to add invalid TSSC config. Missing expected top level key \(tssc-config\):"
            ):
                tssc_config.add_config(os.path.join(temp_dir.path, config_dir))

    def test_add_config_dir_one_valid_file_and_one_valid_dict(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'step-foo': {
                                'implementer': 'foo'
                            }
                        }
                    }
                }
            ]

            for config_file in config_files:
                config_file_name = config_file['name']
                config_file_contents = config_file['contents']
                temp_dir.write(
                    config_file_name,
                    bytes(f"{config_file_contents}", 'utf-8')
                )

            tssc_config = TSSCConfig()
            tssc_config.add_config(
                [
                    os.path.join(temp_dir.path, config_dir),
                    {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'step-bar': {
                                'implementer': 'bar'
                            }
                        }
                    }
                ]

            )

            self.assertEqual(tssc_config.global_defaults, {})
            self.assertEqual(tssc_config.global_environment_defaults, {})

    def test_initial_config_dict_step_missing_implementer(self):
        with self.assertRaisesRegex(
            AssertionError,
            r"Step \(invalid-step\) defines a single sub step with values \({}\) but is missing value for key: implementer"
        ):
            TSSCConfig({
                TSSCConfig.TSSC_CONFIG_KEY: {
                    'invalid-step' : {}
                }
            })

    def test_global_defaults(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'global-defaults' : {
                    'test1' : 'foo1'
                }
            }
        })

        self.assertEqual(tssc_config.global_defaults, {
            'test1' : 'foo1'
        })
        self.assertEqual(tssc_config.global_environment_defaults, {})

    def test_global_environment_defaults(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'global-environment-defaults' : {
                    'env1': {
                        'test1': 'env1',
                        'test2': 'test2'
                    },
                    'env2': {
                        'test1': 'env2',
                        'test3': 'test3'
                    }
                }
            }
        })

        self.assertEqual(tssc_config.global_defaults, {})
        self.assertEqual(tssc_config.global_environment_defaults, {
            'env1': {
                'environment-name' : 'env1',
                'test1' : 'env1',
                'test2' : 'test2'
            },
            'env2': {
                'environment-name' : 'env2',
                'test1' : 'env2',
                'test3' : 'test3'
            }
        })
        self.assertEqual(tssc_config.get_global_environment_defaults_for_environment('env1'), {
            'environment-name' : 'env1',
            'test1' : 'env1',
            'test2' : 'test2'
        })
        self.assertEqual(tssc_config.get_global_environment_defaults_for_environment('env2'), {
            'environment-name' : 'env2',
            'test1' : 'env2',
            'test3' : 'test3'
        })
        self.assertEqual(tssc_config.get_global_environment_defaults_for_environment('does-not-exist'), {})
        self.assertEqual(tssc_config.get_global_environment_defaults_for_environment(None), {})

    def test_get_sub_step_configs_for_non_existent_step(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo'
                }
            }
        })

        self.assertEqual(tssc_config.get_sub_step_configs('does-not-exist'), [])

    def test_get_sub_step_configs_single_sub_step_no_config(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo',
                }
            }
        })

        sub_step_configs = tssc_config.get_sub_step_configs('step-foo')
        self.assertEqual(len(sub_step_configs), 1)
        sub_step_config = sub_step_configs[0]
        self.assertEqual(sub_step_config.sub_step_config, {})

    def test_set_step_config_overrides_existing_step(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo',
                }
            }
        })
        sub_step_configs = tssc_config.get_sub_step_configs('step-foo')
        self.assertEqual(len(sub_step_configs), 1)
        sub_step_config = sub_step_configs[0]
        self.assertEqual(sub_step_config.step_config_overrides, {})

        tssc_config.set_step_config_overrides('step-foo', {
            'test1': 'test2'
        })

        self.assertEqual(sub_step_config.step_config_overrides, {
            'test1': 'test2'
        })

    def test_set_step_config_override_overrides_existing_step(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo',
                }
            }
        })
        sub_step_configs = tssc_config.get_sub_step_configs('step-foo')
        self.assertEqual(len(sub_step_configs), 1)
        sub_step_config = sub_step_configs[0]
        self.assertEqual(sub_step_config.step_config_overrides, {})

        tssc_config.set_step_config_overrides('step-foo', {
            'test1': 'test2'
        })
        self.assertEqual(sub_step_config.step_config_overrides, {
            'test1': 'test2'
        })

        tssc_config.set_step_config_overrides('step-foo', {
            'test2': 'test3'
        })
        self.assertEqual(sub_step_config.step_config_overrides, {
            'test2': 'test3'
        })

    def test_set_step_config_overrides_not_existing_step(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
            }
        })
        self.assertIsNone(tssc_config.get_step_config('step-bar'))

        tssc_config.set_step_config_overrides('step-bar', {
            'test1': 'test2'
        })

        step_config = tssc_config.get_step_config('step-bar')
        self.assertIsNotNone(step_config)
        self.assertEqual(step_config.step_config_overrides, {
            'test1': 'test2'
        })

    def test_duplicate_global_default_keys(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'global-defaults' : {
                                'dup-key': 'foo'
                            }
                        }
                    }
                },
                {
                    'name': os.path.join(config_dir,'bar.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'global-defaults' : {
                                'dup-key': 'bar'
                            }
                        }
                    }
                },
            ]

            for config_file in config_files:
                config_file_name = config_file['name']
                config_file_contents = config_file['contents']
                temp_dir.write(
                    config_file_name,
                    bytes(f"{config_file_contents}", 'utf-8')
                )

            with self.assertRaisesRegex(
                ValueError,
                r"Error merging global defaults: Conflict at dup-key"
            ):
                tssc_config = TSSCConfig()
                tssc_config.add_config(os.path.join(temp_dir.path, config_dir))

    def test_duplicate_global_environment_default_keys(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'global-environment-defaults' : {
                                'env1' : {
                                    'dup-key': 'foo'
                                }
                            }
                        }
                    }
                },
                {
                    'name': os.path.join(config_dir,'bar.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'global-environment-defaults' : {
                                'env1' : {
                                    'dup-key': 'bar'
                                }
                            }
                        }
                    }
                },
            ]

            for config_file in config_files:
                config_file_name = config_file['name']
                config_file_contents = config_file['contents']
                temp_dir.write(
                    config_file_name,
                    bytes(f"{config_file_contents}", 'utf-8')
                )

            with self.assertRaisesRegex(
                ValueError,
                r"Error merging global environment \(env1\) defaults: Conflict at dup-key"
            ):
                tssc_config = TSSCConfig()
                tssc_config.add_config(os.path.join(temp_dir.path, config_dir))

    def test_merge_valid_global_environment_defaults_same_env_diff_keys(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'global-environment-defaults' : {
                                'env1' : {
                                    'foo-key': 'foo'
                                }
                            }
                        }
                    }
                },
                {
                    'name': os.path.join(config_dir,'bar.yml'),
                    'contents' : {
                        TSSCConfig.TSSC_CONFIG_KEY: {
                            'global-environment-defaults' : {
                                'env1' : {
                                    'bar-key': 'bar'
                                }
                            }
                        }
                    }
                },
            ]

            for config_file in config_files:
                config_file_name = config_file['name']
                config_file_contents = config_file['contents']
                temp_dir.write(
                    config_file_name,
                    bytes(f"{config_file_contents}", 'utf-8')
                )

            tssc_config = TSSCConfig()
            tssc_config.add_config(os.path.join(temp_dir.path, config_dir))
            self.assertEqual(tssc_config.get_global_environment_defaults_for_environment('env1'), {
                'environment-name': 'env1',
                'foo-key': 'foo',
                'bar-key': 'bar'
            })
    def test_invalid_sub_steps(self):
        with self.assertRaisesRegex(
            ValueError,
            r"Expected step \(step-foo\) to have have step config \(bad-step-config\) of type dict or list but got: <class 'str'>"
        ):
            TSSCConfig({
                TSSCConfig.TSSC_CONFIG_KEY: {
                    'step-foo': "bad-step-config"
                }
            })

    def test_multiple_sub_steps(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        }
                    },
                    {
                        'implementer': 'foo2',
                        'config': {
                            'test2': 'foo'
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 2)

        self.assertEqual(step_config.get_sub_step('foo1').sub_step_config, {
            'test1': 'foo'
        })
        self.assertEqual(step_config.get_sub_step('foo2').sub_step_config, {
            'test2': 'foo'
        })

    def test_sub_step_with_name(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'name': 'sub-step-name-test',
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 1)

        self.assertEqual(step_config.get_sub_step('sub-step-name-test').sub_step_config, {
            'test1': 'foo'
        })

    def test_sub_step_with_environment_config(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        },
                        'environment-config': {
                            'env1': {
                                'test2': 'bar'
                            }
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 1)

        self.assertEqual(step_config.get_sub_step('foo1').sub_step_config, {
            'test1': 'foo'
        })
        self.assertEqual(step_config.get_sub_step('foo1').get_sub_step_env_config('env1'), {
            'test2': 'bar'
        })

    def test_sub_step_with_no_environment_config(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 1)

        self.assertEqual(step_config.get_sub_step('foo1').sub_step_config, {
            'test1': 'foo'
        })
        self.assertEqual(step_config.get_sub_step('foo1').get_sub_step_env_config('env1'), {})

class TestTSSCStepConfig(BaseTSSCTestCase):
    def test_parent_config(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        self.assertEqual(step_config.parent_config, tssc_config)

    def test_step_name(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        self.assertEqual(step_config.step_name, 'step-foo')

    def test_add_or_update_sub_step_config_exising_sub_step(self):
        tssc_config = TSSCConfig([
            {
                TSSCConfig.TSSC_CONFIG_KEY: {
                    'step-foo': [
                        {
                            'implementer': 'foo1',
                            'config': {
                                'test1': 'foo'
                            }
                        }
                    ]

                }
            },
            {
                TSSCConfig.TSSC_CONFIG_KEY: {
                    'step-foo': [
                        {
                            'implementer': 'foo1',
                            'config': {
                                'test2': 'foo'
                            }
                        }
                    ]

                }
            },
        ])

        step_config = tssc_config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 1)

        self.assertEqual(step_config.get_sub_step('foo1').sub_step_config, {
            'test1': 'foo',
            'test2': 'foo'
        })

    def test_get_sub_step_non_existing_sub_step_name(self):
        tssc_config = TSSCConfig([
            {
                TSSCConfig.TSSC_CONFIG_KEY: {
                    'step-foo': [
                        {
                            'implementer': 'foo1',
                            'config': {
                                'test1': 'foo'
                            }
                        }
                    ]
                }
            }
        ])

        step_config = tssc_config.get_step_config('step-foo')

        self.assertIsNone(step_config.get_sub_step('does-not-exist'))

class TestTSSCSubStepConfig(BaseTSSCTestCase):
    def test_constructor_no_sub_step_config_or_step_env_config(self):
        sub_step_config = TSSCSubStepConfig(
            parent_step_config=None,
            sub_step_name='sub-step-foo',
            sub_step_implementer_name='foo'
        )

        self.assertEqual(sub_step_config.sub_step_config, {})
        self.assertEqual(sub_step_config.sub_step_config, {})

    def test_parent_config(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(sub_step.parent_config, tssc_config)

    def test_step_name(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(sub_step.step_name, 'step-foo')

    def test_global_defaults(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'global-defaults': {
                    'test1': 'global-default-1',
                    'test2': 'global-default-2'
                },
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(sub_step.global_defaults, {
            'test1': 'global-default-1',
            'test2': 'global-default-2'
        })

    def test_global_environment_defaults(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'global-environment-defaults': {
                    'env1': {
                        'test1': 'global-env1-default-1',
                        'test2': 'global-env1-default-2'
                    },
                    'env2': {
                        'test1': 'global-env2-default-1',
                        'test2': 'global-env2-default-2'
                    }
                },
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(sub_step.get_global_environment_defaults('env1'), {
            'environment-name': 'env1',
            'test1': 'global-env1-default-1',
            'test2': 'global-env1-default-2'
        })
        self.assertEqual(sub_step.get_global_environment_defaults('env2'), {
            'environment-name': 'env2',
            'test1': 'global-env2-default-1',
            'test2': 'global-env2-default-2'
        })

    def test_get_sub_step_env_config(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo'
                        },
                        'environment-config': {
                            'env1': {
                                'test2': 'bar'
                            }
                        }
                    }
                ]

            }
        })

        step_config = tssc_config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(sub_step.get_sub_step_env_config('env1'), {
            'test2': 'bar'
        })

    def test_merge_sub_step_config_duplicate_sub_step_keys(self):
        with self.assertRaisesRegex(
                ValueError,
                r"Error merging new sub step configuration into existing sub step configuration for sub step \(foo1\) of step \(step-foo\): Conflict at test1"
        ):
            TSSCConfig([
                {
                    TSSCConfig.TSSC_CONFIG_KEY: {
                        'step-foo': [
                            {
                                'implementer': 'foo1',
                                'config': {
                                    'test1': 'foo'
                                }
                            },
                        ]

                    }
                },
                {
                    TSSCConfig.TSSC_CONFIG_KEY: {
                        'step-foo': [
                            {
                                'implementer': 'foo1',
                                'config': {
                                    'test1': 'bar'
                                }
                            },
                        ]

                    }
                }
            ])

    def test_merge_sub_step_config_duplicate_sub_step_environment_config_keys(self):
        with self.assertRaisesRegex(
                ValueError,
                r"Error merging new sub step environment configuration into existing sub step environment configuration for sub step \(foo1\) of step \(step-foo\): Conflict at env1.dup-key"
        ):
            TSSCConfig([
                {
                    TSSCConfig.TSSC_CONFIG_KEY: {
                        'step-foo': [
                            {
                                'implementer': 'foo1',
                                'config': {
                                    'test1': 'foo'
                                },
                                'environment-config': {
                                    'env1': {
                                        'dup-key': 'value1'
                                    }
                                }
                            }
                        ]

                    }
                },
                {
                    TSSCConfig.TSSC_CONFIG_KEY: {
                        'step-foo': [
                            {
                                'implementer': 'foo1',
                                'config': {
                                    'test2': 'bar'
                                },
                                'environment-config': {
                                    'env1': {
                                        'dup-key': 'value2'
                                    }
                                }
                            }
                        ]
                    }
                }
            ])

    def test_get_runtime_step_config_global_defaults_global_env_defaults_sub_step_config_sub_step_env_config_step_config_overrides(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'global-defaults': {
                    'global-default-unique-0': 'global-default',
                    'global-default-override-by-global-env-default-0': 'global-default-override-me',
                    'global-default-override-by-step-config-0': 'global-default-override-me',
                    'global-default-override-by-step-env-config-0': 'global-default-override-me',
                    'global-default-override-by-step-config-override-0': 'global-default-override-me'
                },
                'global-environment-defaults' : {
                    'env1': {
                        'global-default-override-by-global-env-default-0': 'global-environment-defaults-1',
                        'global-env-default-env1-unique-0': 'global-environment-defaults-1',
                        'global-env-default-override-by-step-config': 'global-environment-defaults-1'
                    },
                    'env2': {
                        'global-default-override-by-global-env-default-0': 'global-environment-defaults-2',
                        'global-env-default-env2-unique-0': 'global-environment-defaults-2',
                        'global-env-default-override-by-step-config': 'global-environment-defaults-1'
                    }
                },
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'step-foo-foo1-unique-0': 'step-foo-foo1',
                            'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-override-me',
                            'step-foo-foo1-override-by-step-override': 'step-foo-foo-override-me',
                            'global-default-override-by-step-config-0': 'step-foo-foo1',
                            'global-env-default-override-by-step-config': 'step-foo-foo1'
                        },
                        'environment-config': {
                            'env1': {
                                'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-env1',
                                'global-default-override-by-step-env-config-0': 'step-foo-foo-env1',
                                'step-foo-foo1-env1-unique-0': 'step-foo-foo-env1',
                                'step-foo-foo1-env-specific': 'step-foo-foo-env1'
                            },
                            'env2': {
                                'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-env2',
                                'global-default-override-by-step-env-config-0': 'step-foo-foo-env2',
                                'step-foo-foo1-env2-unique-0': 'step-foo-foo-env2',
                                'step-foo-foo1-env-specific': 'step-foo-foo-env2'
                            }
                        }
                    }
                ]

            }
        })

        tssc_config.set_step_config_overrides('step-foo', {
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique'
        })

        step_config = tssc_config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        runtime_step_config_no_given_env = sub_step.get_runtime_step_config()
        self.assertEqual(runtime_step_config_no_given_env, {
            'global-default-unique-0': 'global-default',
            'global-default-override-by-global-env-default-0': 'global-default-override-me',
            'global-default-override-by-step-config-0': 'step-foo-foo1',
            'global-default-override-by-step-env-config-0': 'global-default-override-me',
            'step-foo-foo1-unique-0': 'step-foo-foo1',
            'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-override-me',
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique',
            'global-env-default-override-by-step-config': 'step-foo-foo1'
        })

        runtime_step_config_env1 = sub_step.get_runtime_step_config('env1')
        self.assertEqual(runtime_step_config_env1, {
            'environment-name': 'env1',
            'global-default-unique-0': 'global-default',
            'global-default-override-by-global-env-default-0': 'global-environment-defaults-1',
            'global-default-override-by-step-config-0': 'step-foo-foo1',
            'global-default-override-by-step-env-config-0': 'step-foo-foo-env1',
            'step-foo-foo1-unique-0': 'step-foo-foo1',
            'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-env1',
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique',
            'global-env-default-override-by-step-config': 'step-foo-foo1',
            'global-env-default-env1-unique-0': 'global-environment-defaults-1',
            'step-foo-foo1-env1-unique-0': 'step-foo-foo-env1',
            'step-foo-foo1-env-specific': 'step-foo-foo-env1'
        })

        runtime_step_config_env2 = sub_step.get_runtime_step_config('env2')
        self.assertEqual(runtime_step_config_env2, {
            'environment-name': 'env2',
            'global-default-unique-0': 'global-default',
            'global-default-override-by-global-env-default-0': 'global-environment-defaults-2',
            'global-default-override-by-step-config-0': 'step-foo-foo1',
            'global-default-override-by-step-env-config-0': 'step-foo-foo-env2',
            'step-foo-foo1-unique-0': 'step-foo-foo1',
            'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-env2',
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique',
            'global-env-default-override-by-step-config': 'step-foo-foo1',
            'global-env-default-env2-unique-0': 'global-environment-defaults-2',
            'step-foo-foo1-env2-unique-0': 'step-foo-foo-env2',
            'step-foo-foo1-env-specific': 'step-foo-foo-env2'
        })

    def test_get_runtime_step_config_default_global_defaults_global_env_defaults_sub_step_config_sub_step_env_config_step_config_overrides(self):
        tssc_config = TSSCConfig({
            TSSCConfig.TSSC_CONFIG_KEY: {
                'global-defaults': {
                    'global-default-unique-0': 'global-default',
                    'global-default-override-by-global-env-default-0': 'global-default-override-me',
                    'global-default-override-by-step-config-0': 'global-default-override-me',
                    'global-default-override-by-step-env-config-0': 'global-default-override-me',
                    'global-default-override-by-step-config-override-0': 'global-default-override-me',
                    'default-overriden-by-global-default': 'global-default',
                },
                'global-environment-defaults' : {
                    'env1': {
                        'global-default-override-by-global-env-default-0': 'global-environment-defaults-1',
                        'global-env-default-env1-unique-0': 'global-environment-defaults-1',
                        'global-env-default-override-by-step-config': 'global-environment-defaults-1',
                        'default-overriden-by-global-env-default': 'global-environment-defaults-1'
                    },
                    'env2': {
                        'global-default-override-by-global-env-default-0': 'global-environment-defaults-2',
                        'global-env-default-env2-unique-0': 'global-environment-defaults-2',
                        'global-env-default-override-by-step-config': 'global-environment-defaults-2',
                        'default-overriden-by-global-env-default': 'global-environment-defaults-2'
                    }
                },
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'step-foo-foo1-unique-0': 'step-foo-foo1',
                            'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-override-me',
                            'step-foo-foo1-override-by-step-override': 'step-foo-foo-override-me',
                            'global-default-override-by-step-config-0': 'step-foo-foo1',
                            'global-env-default-override-by-step-config': 'step-foo-foo1',
                            'default-overriden-by-step-config': 'step-foo-foo1'
                        },
                        'environment-config': {
                            'env1': {
                                'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-env1',
                                'global-default-override-by-step-env-config-0': 'step-foo-foo-env1',
                                'step-foo-foo1-env1-unique-0': 'step-foo-foo-env1',
                                'step-foo-foo1-env-specific': 'step-foo-foo-env1',
                                'default-overriden-by-step-env-config': 'step-foo-foo-env1',
                            },
                            'env2': {
                                'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-env2',
                                'global-default-override-by-step-env-config-0': 'step-foo-foo-env2',
                                'step-foo-foo1-env2-unique-0': 'step-foo-foo-env2',
                                'step-foo-foo1-env-specific': 'step-foo-foo-env2',
                                'default-overriden-by-step-env-config': 'step-foo-foo-env2',
                            }
                        }
                    }
                ]

            }
        })

        tssc_config.set_step_config_overrides('step-foo', {
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique',
            'default-overriden-by-step-config-overrides': 'step-foo-step-config-override'
        })

        step_config = tssc_config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        defaults = {
            'default-unique': 'not-overriden-default',
            'default-overriden-by-global-default': 'override-me',
            'default-overriden-by-global-env-default': 'override-me',
            'default-overriden-by-step-config': 'override-me',
            'default-overriden-by-step-env-config': 'override-me',
            'default-overriden-by-step-config-overrides': 'override-me'
        }

        runtime_step_config_no_given_env = sub_step.get_runtime_step_config(None, defaults)
        self.assertEqual(runtime_step_config_no_given_env, {
            'global-default-unique-0': 'global-default',
            'global-default-override-by-global-env-default-0': 'global-default-override-me',
            'global-default-override-by-step-config-0': 'step-foo-foo1',
            'global-default-override-by-step-env-config-0': 'global-default-override-me',
            'step-foo-foo1-unique-0': 'step-foo-foo1',
            'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-override-me',
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique',
            'global-env-default-override-by-step-config': 'step-foo-foo1',
            'default-unique': 'not-overriden-default',
            'default-overriden-by-global-default': 'global-default',
            'default-overriden-by-global-env-default': 'override-me',
            'default-overriden-by-step-config': 'step-foo-foo1',
            'default-overriden-by-step-env-config': 'override-me',
            'default-overriden-by-step-config-overrides': 'step-foo-step-config-override'
        })

        runtime_step_config_env1 = sub_step.get_runtime_step_config('env1', defaults)
        self.assertEqual(runtime_step_config_env1, {
            'environment-name': 'env1',
            'global-default-unique-0': 'global-default',
            'global-default-override-by-global-env-default-0': 'global-environment-defaults-1',
            'global-default-override-by-step-config-0': 'step-foo-foo1',
            'global-default-override-by-step-env-config-0': 'step-foo-foo-env1',
            'step-foo-foo1-unique-0': 'step-foo-foo1',
            'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-env1',
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique',
            'global-env-default-override-by-step-config': 'step-foo-foo1',
            'global-env-default-env1-unique-0': 'global-environment-defaults-1',
            'step-foo-foo1-env1-unique-0': 'step-foo-foo-env1',
            'step-foo-foo1-env-specific': 'step-foo-foo-env1',
            'default-unique': 'not-overriden-default',
            'default-overriden-by-global-default': 'global-default',
            'default-overriden-by-global-env-default': 'global-environment-defaults-1',
            'default-overriden-by-step-config': 'step-foo-foo1',
            'default-overriden-by-step-env-config': 'step-foo-foo-env1',
            'default-overriden-by-step-config-overrides': 'step-foo-step-config-override'
        })

        runtime_step_config_env2 = sub_step.get_runtime_step_config('env2', defaults)
        self.assertEqual(runtime_step_config_env2, {
            'environment-name': 'env2',
            'global-default-unique-0': 'global-default',
            'global-default-override-by-global-env-default-0': 'global-environment-defaults-2',
            'global-default-override-by-step-config-0': 'step-foo-foo1',
            'global-default-override-by-step-env-config-0': 'step-foo-foo-env2',
            'step-foo-foo1-unique-0': 'step-foo-foo1',
            'step-foo-foo1-override-by-step-env-config': 'step-foo-foo-env2',
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique',
            'global-env-default-override-by-step-config': 'step-foo-foo1',
            'global-env-default-env2-unique-0': 'global-environment-defaults-2',
            'step-foo-foo1-env2-unique-0': 'step-foo-foo-env2',
            'step-foo-foo1-env-specific': 'step-foo-foo-env2',
            'default-unique': 'not-overriden-default',
            'default-overriden-by-global-default': 'global-default',
            'default-overriden-by-global-env-default': 'global-environment-defaults-2',
            'default-overriden-by-step-config': 'step-foo-foo1',
            'default-overriden-by-step-env-config': 'step-foo-foo-env2',
            'default-overriden-by-step-config-overrides': 'step-foo-step-config-override'
        })
