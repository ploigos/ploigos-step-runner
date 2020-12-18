import os.path

from testfixtures import TempDirectory

from tests.helpers.base_test_case import BaseTestCase

from ploigos_step_runner.decryption_utils import DecryptionUtils
from ploigos_step_runner.config import Config, ConfigValue
from ploigos_step_runner.config.decryptors.sops import SOPS

class TestConfig(BaseTestCase):
    def test_add_config_invalid_type(self):
        config = Config()
        with self.assertRaisesRegex(
            ValueError,
            r"Given config \(True\) is unexpected type \(<class 'bool'>\) not a dictionary, string, or list of former."
        ):
            config.add_config(True)

    def test_add_config_dict_missing_config_key(self):
        config = Config()
        with self.assertRaisesRegex(
            AssertionError,
            r"Failed to add invalid config. Missing expected top level key \(step-runner-config\):"
        ):
            config.add_config({
                'foo': 'foo'
            })

    def test_add_config_dict_valid_basic(self):
        config = Config()
        config.add_config({
            Config.CONFIG_KEY: {}
        })

        self.assertEqual(config.global_defaults, {})
        self.assertEqual(config.global_environment_defaults, {})

    def test_initial_config_dict_valid_basic(self):
        config = Config({
            Config.CONFIG_KEY: {}
        })

        self.assertEqual(config.global_defaults, {})
        self.assertEqual(config.global_environment_defaults, {})

    def test_initial_config_dict_missing_config_key(self):
        with self.assertRaisesRegex(
            AssertionError,
            r"Failed to add invalid config. Missing expected top level key \(step-runner-config\):"
        ):
            Config({
                'foo': 'foo'
            })

    def test_add_config_file_missing_file(self):
        with TempDirectory() as temp_dir:
            config = Config()
            with self.assertRaisesRegex(
                ValueError,
                r"Given config string \(.*\) is not a valid path."
            ):
                config.add_config(os.path.join(temp_dir.path, 'does-not-exist.yml'))

    def test_add_config_file_invalid_json_or_yaml(self):
        with TempDirectory() as temp_dir:
            config_file_name = "bad"
            config_file_contents = ": blarg this: is {} bad syntax"
            temp_dir.write(config_file_name, bytes(f"{config_file_contents}", 'utf-8'))

            config = Config()
            with self.assertRaisesRegex(
                ValueError,
                r"Error parsing config file \(.*\) as json or yaml"
            ):
                config.add_config(os.path.join(temp_dir.path, config_file_name))

    def test_add_config_file_missing_config_key(self):
        with TempDirectory() as temp_dir:
            config_file_name = "foo.json"
            config_file_contents = {
                'foo': 'foo'
            }
            temp_dir.write(config_file_name, bytes(f"{config_file_contents}", 'utf-8'))

            config = Config()
            with self.assertRaisesRegex(
                AssertionError,
                r"Failed to add parsed configuration file \(.*\): Failed to add invalid config. Missing expected top level key \(step-runner-config\):"
            ):
                config.add_config(os.path.join(temp_dir.path, config_file_name))

    def test_add_config_file_valid_basic(self):
        with TempDirectory() as temp_dir:
            config_file_name = "foo.json"
            config_file_contents = {
                Config.CONFIG_KEY: {}
            }
            temp_dir.write(config_file_name, bytes(f"{config_file_contents}", 'utf-8'))

            config = Config()
            config.add_config(os.path.join(temp_dir.path, config_file_name))

            self.assertEqual(config.global_defaults, {})
            self.assertEqual(config.global_environment_defaults, {})

    def test_add_config_dir_no_files(self):
        with TempDirectory() as temp_dir:
            config = Config()
            with self.assertRaisesRegex(
                ValueError,
                r"Given config string \(.*\) is a directory with no recursive children files."
            ):
                config.add_config(temp_dir.path)

    def test_add_config_dir_one_valid_file(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {}
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

            config = Config()
            config.add_config(os.path.join(temp_dir.path, config_dir))

            self.assertEqual(config.global_defaults, {})
            self.assertEqual(config.global_environment_defaults, {})

    def test_add_config_dir_two_valid_file(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {
                            'step-test-foo' : {
                                'implementer': 'foo'
                            }
                        }
                    }
                },
                {
                    'name': os.path.join(config_dir,'bar.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {
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

            config = Config()
            config.add_config(os.path.join(temp_dir.path, config_dir))

            self.assertEqual(config.global_defaults, {})
            self.assertEqual(config.global_environment_defaults, {})

    def test_add_two_valid_files(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {
                            'step-test-foo' : {
                                'implementer': 'foo'
                            }
                        }
                    }
                },
                {
                    'name': os.path.join(config_dir,'bar.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {
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

            config = Config()
            config.add_config(
                [
                    os.path.join(temp_dir.path, config_dir, 'foo.yml'),
                    os.path.join(temp_dir.path, config_dir, 'bar.yml')
                ]
            )

            self.assertEqual(config.global_defaults, {})
            self.assertEqual(config.global_environment_defaults, {})

    def test_add_config_dir_one_valid_file_one_invalid_file(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {}
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

            config = Config()
            with self.assertRaisesRegex(
                AssertionError,
                r"Failed to add parsed configuration file \(.*\): Failed to add invalid config. Missing expected top level key \(step-runner-config\):"
            ):
                config.add_config(os.path.join(temp_dir.path, config_dir))

    def test_add_config_dir_one_valid_file_and_one_valid_dict(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {
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

            config = Config()
            config.add_config(
                [
                    os.path.join(temp_dir.path, config_dir),
                    {
                        Config.CONFIG_KEY: {
                            'step-bar': {
                                'implementer': 'bar'
                            }
                        }
                    }
                ]

            )

            self.assertEqual(config.global_defaults, {})
            self.assertEqual(config.global_environment_defaults, {})

    def test_initial_config_dict_step_missing_implementer(self):
        with self.assertRaisesRegex(
            AssertionError,
            r"Step \(invalid-step\) defines a single sub step with values \({}\) but is missing value for key: implementer"
        ):
            Config({
                Config.CONFIG_KEY: {
                    'invalid-step' : {}
                }
            })

    def test_global_defaults(self):
        config = Config({
            Config.CONFIG_KEY: {
                'global-defaults' : {
                    'test1' : 'foo1'
                }
            }
        })

        self.assertEqual(
            ConfigValue.convert_leaves_to_values(config.global_defaults),
            {
                'test1' : 'foo1'
            }
        )
        self.assertEqual(config.global_environment_defaults, {})

    def test_global_environment_defaults(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        self.assertEqual(config.global_defaults, {})
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(config.global_environment_defaults),
            {
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
            }
        )
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                config.get_global_environment_defaults_for_environment('env1')
            ),
            {
                'environment-name' : 'env1',
                'test1' : 'env1',
                'test2' : 'test2'
            }
        )
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                config.get_global_environment_defaults_for_environment('env2')
            ), {
                'environment-name' : 'env2',
                'test1' : 'env2',
                'test3' : 'test3'
            }
        )
        self.assertEqual(config.get_global_environment_defaults_for_environment('does-not-exist'), {})
        self.assertEqual(config.get_global_environment_defaults_for_environment(None), {})

    def test_get_sub_step_configs_for_non_existent_step(self):
        config = Config({
            Config.CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo'
                }
            }
        })

        self.assertEqual(config.get_sub_step_configs('does-not-exist'), [])

    def test_get_sub_step_configs_single_sub_step_no_config(self):
        config = Config({
            Config.CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo',
                }
            }
        })

        sub_step_configs = config.get_sub_step_configs('step-foo')
        self.assertEqual(len(sub_step_configs), 1)
        sub_step_config = sub_step_configs[0]
        self.assertEqual(sub_step_config.sub_step_config, {})

    def test_set_step_config_overrides_existing_step(self):
        config = Config({
            Config.CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo',
                }
            }
        })
        sub_step_configs = config.get_sub_step_configs('step-foo')
        self.assertEqual(len(sub_step_configs), 1)
        sub_step_config = sub_step_configs[0]
        self.assertEqual(sub_step_config.step_config_overrides, {})

        config.set_step_config_overrides('step-foo', {
            'test1': 'test2'
        })

        self.assertEqual(sub_step_config.step_config_overrides, {
            'test1': 'test2'
        })

    def test_set_step_config_override_overrides_existing_step(self):
        config = Config({
            Config.CONFIG_KEY: {
                'step-foo': {
                    'implementer': 'foo',
                }
            }
        })
        sub_step_configs = config.get_sub_step_configs('step-foo')
        self.assertEqual(len(sub_step_configs), 1)
        sub_step_config = sub_step_configs[0]
        self.assertEqual(sub_step_config.step_config_overrides, {})

        config.set_step_config_overrides('step-foo', {
            'test1': 'test2'
        })
        self.assertEqual(sub_step_config.step_config_overrides, {
            'test1': 'test2'
        })

        config.set_step_config_overrides('step-foo', {
            'test2': 'test3'
        })
        self.assertEqual(sub_step_config.step_config_overrides, {
            'test2': 'test3'
        })

    def test_set_step_config_overrides_not_existing_step(self):
        config = Config({
            Config.CONFIG_KEY: {
            }
        })
        self.assertIsNone(config.get_step_config('step-bar'))

        config.set_step_config_overrides('step-bar', {
            'test1': 'test2'
        })

        step_config = config.get_step_config('step-bar')
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
                        Config.CONFIG_KEY: {
                            'global-defaults' : {
                                'dup-key': 'foo'
                            }
                        }
                    }
                },
                {
                    'name': os.path.join(config_dir,'bar.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {
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
                config = Config()
                config.add_config(os.path.join(temp_dir.path, config_dir))

    def test_duplicate_global_environment_default_keys(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {
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
                        Config.CONFIG_KEY: {
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
                config = Config()
                config.add_config(os.path.join(temp_dir.path, config_dir))

    def test_merge_valid_global_environment_defaults_same_env_diff_keys(self):
        with TempDirectory() as temp_dir:
            config_dir = "test"

            config_files = [
                {
                    'name': os.path.join(config_dir,'foo.yml'),
                    'contents' : {
                        Config.CONFIG_KEY: {
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
                        Config.CONFIG_KEY: {
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

            config = Config()
            config.add_config(os.path.join(temp_dir.path, config_dir))
            self.assertEqual(
                ConfigValue.convert_leaves_to_values(
                    config.get_global_environment_defaults_for_environment('env1')
                ),
                {
                    'environment-name': 'env1',
                    'foo-key': 'foo',
                    'bar-key': 'bar'
                }
            )
    def test_invalid_sub_steps(self):
        with self.assertRaisesRegex(
            ValueError,
            r"Expected step \(step-foo\) to have have step config " \
            r"\(ConfigValue\(value=bad-step-config, " \
            r"value_path='\['step-runner-config', 'step-foo'\]\'\)\) of " \
            r"type dict or list but got: <class 'ploigos_step_runner.config.config_value.ConfigValue'>"
        ):
            Config({
                Config.CONFIG_KEY: {
                    'step-foo': "bad-step-config"
                }
            })

    def test_multiple_sub_steps(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        step_config = config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 2)

        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                step_config.get_sub_step('foo1').sub_step_config,
            ),
            {
                'test1': 'foo'
            }
        )
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                step_config.get_sub_step('foo2').sub_step_config
            ),
            {
                'test2': 'foo'
            }
        )

    def test_sub_step_with_name(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        step_config = config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 1)

        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                step_config.get_sub_step('sub-step-name-test').sub_step_config
            ),
            {
                'test1': 'foo'
            }
        )

    def test_sub_step_with_environment_config(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        step_config = config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 1)

        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                step_config.get_sub_step('foo1').sub_step_config
            ),
            {
                'test1': 'foo'
            }
        )
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                step_config.get_sub_step('foo1').get_sub_step_env_config('env1')
            ),
            {
                'test2': 'bar'
            }
        )

    def test_sub_step_with_no_environment_config(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        step_config = config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 1)

        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                step_config.get_sub_step('foo1').sub_step_config
            ),
            {
                'test1': 'foo'
            }
        )
        self.assertEqual(step_config.get_sub_step('foo1').get_sub_step_env_config('env1'), {})

    def test_parse_and_register_decryptors_definitions_one_definition(self):
        Config.parse_and_register_decryptors_definitions(
            [
                {
                    'implementer': 'SOPS'
                }
            ]
        )

        sops_decryptor = DecryptionUtils._DecryptionUtils__config_value_decryptors[0]
        self.assertEqual(
            type(sops_decryptor),
            SOPS
        )

    def test_parse_and_register_decryptors_definitions_one_definition_with_config(self):
        Config.parse_and_register_decryptors_definitions(
            [
                {
                    'implementer': 'SOPS',
                    'config': {
                        'additional_sops_args': [
                            '--aws-profile=foo'
                        ]
                    }
                }
            ]
        )

        sops_decryptor = DecryptionUtils._DecryptionUtils__config_value_decryptors[0]
        self.assertEqual(
            sops_decryptor._SOPS__additional_sops_args,
            ['--aws-profile=foo']
        )

    def test_initial_config_dict_valid_with_decryptor_definition(self):
        config = Config({
            'step-runner-config': {
                'config-decryptors': [
                    {
                        'implementer': 'SOPS',
                        'config': {
                            'additional_sops_args': [
                                '--aws-profile=foo'
                            ]
                        }
                    }
                ]
            }
        })

        self.assertEqual(config.global_defaults, {})
        self.assertEqual(config.global_environment_defaults, {})
        sops_decryptor = DecryptionUtils._DecryptionUtils__config_value_decryptors[0]
        self.assertEqual(
            type(sops_decryptor),
            SOPS
        )
        self.assertEqual(
            sops_decryptor._SOPS__additional_sops_args,
            ['--aws-profile=foo']
        )
