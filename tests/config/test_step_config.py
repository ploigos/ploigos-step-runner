import os.path

from testfixtures import TempDirectory

from tests.helpers.base_test_case import BaseTestCase

from ploigos_step_runner.config import Config, ConfigValue

class TestStepConfig(BaseTestCase):
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
        self.assertEqual(step_config.parent_config, config)

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
        self.assertEqual(step_config.step_name, 'step-foo')

    def test_add_or_update_sub_step_config_exising_sub_step(self):
        config = Config([
            {
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
            },
            {
                Config.CONFIG_KEY: {
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

        step_config = config.get_step_config('step-foo')
        self.assertEqual(len(step_config.sub_steps), 1)

        self.assertEqual(
            ConfigValue.convert_leaves_to_values(
                step_config.get_sub_step('foo1').sub_step_config
            ),
            {
                'test1': 'foo',
                'test2': 'foo'
            }
        )

    def test_get_sub_step_non_existing_sub_step_name(self):
        config = Config([
            {
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
            }
        ])

        step_config = config.get_step_config('step-foo')

        self.assertIsNone(step_config.get_sub_step('does-not-exist'))
