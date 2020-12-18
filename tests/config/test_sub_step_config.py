import unittest
from testfixtures import TempDirectory

import os.path

from tests.helpers.base_test_case import BaseTestCase

from ploigos_step_runner.config import Config, StepConfig, SubStepConfig, ConfigValue

class TestSubStepConfig(BaseTestCase):
    def test_constructor_no_sub_step_config_or_step_env_config(self):
        sub_step_config = SubStepConfig(
            parent_step_config=None,
            sub_step_name='sub-step-foo',
            sub_step_implementer_name='foo'
        )

        self.assertEqual(sub_step_config.sub_step_config, {})
        self.assertEqual(sub_step_config.sub_step_config, {})

    def test_parent_config(self):
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
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(sub_step.parent_config, config)

    def test_step_name(self):
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
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(sub_step.step_name, 'step-foo')

    def test_global_defaults(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        step_config = config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(sub_step.global_defaults, {
            'test1': ConfigValue(
                'global-default-1',
                None,
                ["step-runner-config", "global-defaults", "test1"]
            ),
            'test2': ConfigValue(
                'global-default-2',
                None,
                ["step-runner-config", "global-defaults", "test2"]
            )
        })

    def test_global_environment_defaults(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        step_config = config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                sub_step.get_global_environment_defaults('env1')
            ),
            {
                'environment-name': 'env1',
                'test1': 'global-env1-default-1',
                'test2': 'global-env1-default-2'
            }
        )
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                sub_step.get_global_environment_defaults('env2')
            ),
            {
                'environment-name': 'env2',
                'test1': 'global-env2-default-1',
                'test2': 'global-env2-default-2'
            }
        )

    def test_get_sub_step_env_config(self):
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
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                sub_step.get_sub_step_env_config('env1')
            ),
            {
                'test2': 'bar'
            }
        )

    def test_merge_sub_step_config_duplicate_sub_step_keys(self):
        with self.assertRaisesRegex(
                ValueError,
                r"Error merging new sub step configuration into existing sub step configuration for sub step \(foo1\) of step \(step-foo\): Conflict at test1"
        ):
            Config([
                {
                    Config.CONFIG_KEY: {
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
                    Config.CONFIG_KEY: {
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
            Config([
                {
                    Config.CONFIG_KEY: {
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
                    Config.CONFIG_KEY: {
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

    def test_get_copy_of_runtime_step_config_global_defaults_global_env_defaults_sub_step_config_sub_step_env_config_step_config_overrides(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        config.set_step_config_overrides('step-foo', {
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique'
        })

        step_config = config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        runtime_step_config_no_given_env = sub_step.get_copy_of_runtime_step_config()
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(runtime_step_config_no_given_env),
            {
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
            }
        )

        runtime_step_config_env1 = sub_step.get_copy_of_runtime_step_config('env1')
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(runtime_step_config_env1),
            {
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
            }
        )

        runtime_step_config_env2 = sub_step.get_copy_of_runtime_step_config('env2')
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(runtime_step_config_env2),
            {
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
            }
        )

    def test_get_copy_of_runtime_step_config_default_global_defaults_global_env_defaults_sub_step_config_sub_step_env_config_step_config_overrides(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        config.set_step_config_overrides('step-foo', {
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique',
            'default-overriden-by-step-config-overrides': 'step-foo-step-config-override'
        })

        step_config = config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        defaults = {
            'default-unique': 'not-overriden-default',
            'default-overriden-by-global-default': 'override-me',
            'default-overriden-by-global-env-default': 'override-me',
            'default-overriden-by-step-config': 'override-me',
            'default-overriden-by-step-env-config': 'override-me',
            'default-overriden-by-step-config-overrides': 'override-me'
        }

        runtime_step_config_no_given_env = sub_step.get_copy_of_runtime_step_config(None, defaults)
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(runtime_step_config_no_given_env),
            {
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
            }
        )

        runtime_step_config_env1 = sub_step.get_copy_of_runtime_step_config('env1', defaults)
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(runtime_step_config_env1),
            {
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
            }
        )

        runtime_step_config_env2 = sub_step.get_copy_of_runtime_step_config('env2', defaults)
        self.assertEqual(
            ConfigValue.convert_leaves_to_values(runtime_step_config_env2),
            {
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
            }
        )

    def test_get_config_value(self):
        config = Config({
            Config.CONFIG_KEY: {
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

        config.set_step_config_overrides('step-foo', {
            'global-default-override-by-step-config-override-0': 'step-foo-step-config-override',
            'step-foo-foo1-override-by-step-override' : 'step-foo-step-config-override',
            'step-config-override-unique-0': 'step-config-override-unique'
        })

        step_config = config.get_step_config('step-foo')
        sub_step = step_config.get_sub_step('foo1')

        self.assertEqual(
            sub_step.get_config_value('global-default-unique-0'),
            "global-default")

        self.assertEqual(
            sub_step.get_config_value('global-default-override-by-global-env-default-0'),
            "global-default-override-me")

        self.assertEqual(
            sub_step.get_config_value('global-default-override-by-global-env-default-0', 'env1'),
            "global-environment-defaults-1")
        self.assertEqual(
            sub_step.get_config_value('global-default-override-by-global-env-default-0', 'env2'),
            "global-environment-defaults-2")

        self.assertEqual(
            sub_step.get_config_value('global-default-override-by-step-config-0'),
            "step-foo-foo1")
        self.assertEqual(
            sub_step.get_config_value('global-default-override-by-step-config-0', 'env1'),
            "step-foo-foo1")

        self.assertEqual(
            sub_step.get_config_value('step-foo-foo1-unique-0',),
            "step-foo-foo1")
        self.assertEqual(
            sub_step.get_config_value('step-foo-foo1-unique-0', 'env1'),
            "step-foo-foo1")

        self.assertEqual(
            sub_step.get_config_value('step-foo-foo1-override-by-step-env-config',),
            "step-foo-foo-override-me")
        self.assertEqual(
            sub_step.get_config_value('step-foo-foo1-override-by-step-env-config', 'env1'),
            "step-foo-foo-env1")
        self.assertEqual(
            sub_step.get_config_value('step-foo-foo1-override-by-step-env-config', 'env2'),
            "step-foo-foo-env2")

        self.assertIsNone(sub_step.get_config_value('does-not-exist'))
