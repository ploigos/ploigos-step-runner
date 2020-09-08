import unittest
from testfixtures import TempDirectory

import os.path

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

from tssc.config import TSSCConfig, TSSCConfigValue

class TestTSSCConfigValue(BaseTSSCTestCase):
    def test__eq__is_equal_basic(self):
        test1 = TSSCConfigValue('foo1', None, None)
        test2 = TSSCConfigValue('foo1', None, None)

        self.assertEqual(test1, test2)

    def test__eq__is_equal_diff_source(self):
        test1 = TSSCConfigValue('foo1', "does not matter for equality", None)
        test2 = TSSCConfigValue('foo1', "really does not matter for equality", None)

        self.assertEqual(test1, test2)

    def test__eq__is_equal_diff_path_parts(self):
        test1 = TSSCConfigValue('foo1', None, ['a','b'])
        test2 = TSSCConfigValue('foo1', None, ['1', '2'])

        self.assertEqual(test1, test2)

    def test__eq__is_equal_diff_source_and_path_parts(self):
        test1 = TSSCConfigValue('foo1', "does not matter for equality", ['a','b'])
        test2 = TSSCConfigValue('foo1', "really does not matter for equality", ['1', '2'])

        self.assertEqual(test1, test2)

    def test__eq__is_not_equal_both_tssc_config_value_objects(self):
        test1 = TSSCConfigValue('foo1', None, None)
        test2 = TSSCConfigValue('foo2', None, None)

        self.assertNotEqual(test1, test2)

    def test__eq__is_not_equal_different_objects(self):
        test1 = TSSCConfigValue('foo1', None, None)
        test2 = "foo1"

        self.assertNotEqual(test1, test2)

    def test__repr__(self):
        source = {
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

        TSSCConfigValue.convert_leaves_to_config_values(
            values=source[TSSCConfig.TSSC_CONFIG_KEY],
            parent_source=source,
            path_parts=[TSSCConfig.TSSC_CONFIG_KEY]
        )

        self.assertEqual(
            str(source[TSSCConfig.TSSC_CONFIG_KEY]['step-foo'][0]['config']['test1']),
            'TSSCConfigValue(value=foo, value_path=\'["tssc-config"]["step-foo"][0]["config"]["test1"]\')'
        )

    def test_convert_leaves_to_config_values_0(self):
        source = {
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

        TSSCConfigValue.convert_leaves_to_config_values(
            values=source[TSSCConfig.TSSC_CONFIG_KEY],
            parent_source=source,
            path_parts=[TSSCConfig.TSSC_CONFIG_KEY]
        )

        expected = {
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': TSSCConfigValue('foo1', None, None),
                        'config': {
                            'test1': TSSCConfigValue('foo', None, None)
                        }
                    }
                ]
            }
        }

        self.assertEqual(source, expected)

    def test_convert_leaves_to_config_values_existing_TSSCConfigValue_leaf(self):
        source = {
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo',
                            'test2': TSSCConfigValue('foo1')
                        }
                    }
                ]
            }
        }

        TSSCConfigValue.convert_leaves_to_config_values(
            values=source[TSSCConfig.TSSC_CONFIG_KEY],
            parent_source=source,
            path_parts=[TSSCConfig.TSSC_CONFIG_KEY]
        )

        expected = {
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': TSSCConfigValue('foo1', None, None),
                        'config': {
                            'test1': TSSCConfigValue('foo', None, None),
                            'test2': TSSCConfigValue('foo1')
                        }
                    }
                ]
            }
        }

        self.assertEqual(source, expected)

    def test_convert_leaves_to_config_values_none_value_leaf(self):
        source = {
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': None
                        }
                    }
                ]
            }
        }

        TSSCConfigValue.convert_leaves_to_config_values(
            values=source[TSSCConfig.TSSC_CONFIG_KEY],
            parent_source=source,
            path_parts=[TSSCConfig.TSSC_CONFIG_KEY]
        )

        expected = {
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': TSSCConfigValue('foo1', None, None),
                        'config': {
                            'test1': None
                        }
                    }
                ]
            }
        }

        self.assertEqual(source, expected)

    def test_value_path_given_inital_value_path_parts(self):
        source = {
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

        TSSCConfigValue.convert_leaves_to_config_values(
            values=source[TSSCConfig.TSSC_CONFIG_KEY],
            parent_source=source,
            path_parts=[TSSCConfig.TSSC_CONFIG_KEY]
        )

        self.assertEqual(
            source[TSSCConfig.TSSC_CONFIG_KEY]['step-foo'][0]['config']['test1'].path,
            '["tssc-config"]["step-foo"][0]["config"]["test1"]')

    def test_value_path_given_no_inital_value_path_parts(self):
        source = {
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

        TSSCConfigValue.convert_leaves_to_config_values(
            values=source,
            parent_source=source
        )

        self.assertEqual(
            source[TSSCConfig.TSSC_CONFIG_KEY]['step-foo'][0]['config']['test1'].path,
            '["tssc-config"]["step-foo"][0]["config"]["test1"]')

    def test_convert_leaves_to_values_all_config_value_leaves(self):
        source_values = {
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': TSSCConfigValue('foo1', None, None),
                        'config': {
                            'test1': TSSCConfigValue('foo', None, None)
                        }
                    }
                ]
            }
        }

        converted = TSSCConfigValue.convert_leaves_to_values(source_values)

        self.assertEqual(
            converted,
            {
                TSSCConfig.TSSC_CONFIG_KEY: {
                    'step-foo': [
                        {
                            'implementer': 'foo1',
                            'config': {
                                'test1': 'foo',
                            }
                        }
                    ]
                }
            }
        )

    def test_convert_leaves_to_values_mixed_leaves(self):
        source_values = {
            TSSCConfig.TSSC_CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': TSSCConfigValue('foo1', None, None),
                        'config': {
                            'test1': TSSCConfigValue('foo', None, None),
                            'test': 'not a tssc config value object'
                        }
                    }
                ]
            }
        }

        converted = TSSCConfigValue.convert_leaves_to_values(source_values)

        self.assertEqual(
            converted,
            {
                TSSCConfig.TSSC_CONFIG_KEY: {
                    'step-foo': [
                        {
                            'implementer': 'foo1',
                            'config': {
                                'test1': 'foo',
                                'test': 'not a tssc config value object'
                            }
                        }
                    ]
                }
            }
        )
