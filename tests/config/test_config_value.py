from io import StringIO
import os.path

import unittest
from testfixtures import TempDirectory
from unittest.mock import patch

from tests.helpers.base_test_case import BaseTestCase
from tests.helpers.test_utils import Any, create_sops_side_effect

from ploigos_step_runner.config import Config, ConfigValue
from ploigos_step_runner.decryption_utils import DecryptionUtils
from ploigos_step_runner.config.decryptors.sops import SOPS

class TestConfigValue(BaseTestCase):
    def test__eq__is_equal_basic(self):
        test1 = ConfigValue('foo1', None, None)
        test2 = ConfigValue('foo1', None, None)

        self.assertEqual(test1, test2)

    def test__eq__is_equal_diff_source(self):
        test1 = ConfigValue('foo1', "does not matter for equality", None)
        test2 = ConfigValue('foo1', "really does not matter for equality", None)

        self.assertEqual(test1, test2)

    def test__eq__is_equal_diff_path_parts(self):
        test1 = ConfigValue('foo1', None, ['a','b'])
        test2 = ConfigValue('foo1', None, ['1', '2'])

        self.assertEqual(test1, test2)

    def test__eq__is_equal_diff_source_and_path_parts(self):
        test1 = ConfigValue('foo1', "does not matter for equality", ['a','b'])
        test2 = ConfigValue('foo1', "really does not matter for equality", ['1', '2'])

        self.assertEqual(test1, test2)

    def test__eq__is_not_equal_both_config_value_objects(self):
        test1 = ConfigValue('foo1', None, None)
        test2 = ConfigValue('foo2', None, None)

        self.assertNotEqual(test1, test2)

    def test__eq__is_not_equal_different_objects(self):
        test1 = ConfigValue('foo1', None, None)
        test2 = "foo1"

        self.assertNotEqual(test1, test2)

    def test__repr__(self):
        source = {
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

        ConfigValue.convert_leaves_to_config_values(
            values=source[Config.CONFIG_KEY],
            parent_source=source,
            path_parts=[Config.CONFIG_KEY]
        )

        self.assertEqual(
            str(source[Config.CONFIG_KEY]['step-foo'][0]['config']['test1']),
            "ConfigValue(value=foo, value_path='['step-runner-config', 'step-foo', 0, 'config', 'test1']')"
        )

    def test_convert_leaves_to_config_values_0(self):
        source = {
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

        ConfigValue.convert_leaves_to_config_values(
            values=source[Config.CONFIG_KEY],
            parent_source=source,
            path_parts=[Config.CONFIG_KEY]
        )

        expected = {
            Config.CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': ConfigValue('foo1', None, None),
                        'config': {
                            'test1': ConfigValue('foo', None, None)
                        }
                    }
                ]
            }
        }

        self.assertEqual(source, expected)

    def test_convert_leaves_to_config_values_existing_ConfigValue_leaf(self):
        source = {
            Config.CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': 'foo1',
                        'config': {
                            'test1': 'foo',
                            'test2': ConfigValue('foo1')
                        }
                    }
                ]
            }
        }

        ConfigValue.convert_leaves_to_config_values(
            values=source[Config.CONFIG_KEY],
            parent_source=source,
            path_parts=[Config.CONFIG_KEY]
        )

        expected = {
            Config.CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': ConfigValue('foo1', None, None),
                        'config': {
                            'test1': ConfigValue('foo', None, None),
                            'test2': ConfigValue('foo1')
                        }
                    }
                ]
            }
        }

        self.assertEqual(source, expected)

    def test_convert_leaves_to_config_values_none_value_leaf(self):
        source = {
            Config.CONFIG_KEY: {
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

        ConfigValue.convert_leaves_to_config_values(
            values=source[Config.CONFIG_KEY],
            parent_source=source,
            path_parts=[Config.CONFIG_KEY]
        )

        expected = {
            Config.CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': ConfigValue('foo1', None, None),
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

        ConfigValue.convert_leaves_to_config_values(
            values=source[Config.CONFIG_KEY],
            parent_source=source,
            path_parts=[Config.CONFIG_KEY]
        )

        self.assertEqual(
            source[Config.CONFIG_KEY]['step-foo'][0]['config']['test1'].path_parts,
            ['step-runner-config', 'step-foo', 0, 'config', 'test1'])

    def test_value_path_given_no_inital_value_path_parts(self):
        source = {
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

        ConfigValue.convert_leaves_to_config_values(
            values=source,
            parent_source=source
        )

        self.assertEqual(
            source[Config.CONFIG_KEY]['step-foo'][0]['config']['test1'].path_parts,
            ['step-runner-config', 'step-foo', 0, 'config', 'test1'])

    def test_convert_leaves_to_values_all_config_value_leaves(self):
        source_values = {
            Config.CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': ConfigValue('foo1', None, None),
                        'config': {
                            'test1': ConfigValue('foo', None, None)
                        }
                    }
                ]
            }
        }

        converted = ConfigValue.convert_leaves_to_values(source_values)

        self.assertEqual(
            converted,
            {
                Config.CONFIG_KEY: {
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
            Config.CONFIG_KEY: {
                'step-foo': [
                    {
                        'implementer': ConfigValue('foo1', None, None),
                        'config': {
                            'test1': ConfigValue('foo', None, None),
                            'test': 'not a config value object'
                        }
                    }
                ]
            }
        }

        converted = ConfigValue.convert_leaves_to_values(source_values)

        self.assertEqual(
            converted,
            {
                Config.CONFIG_KEY: {
                    'step-foo': [
                        {
                            'implementer': 'foo1',
                            'config': {
                                'test1': 'foo',
                                'test': 'not a config value object'
                            }
                        }
                    ]
                }
            }
        )

    @patch('sh.sops', create=True)
    def test_value_decyrpt(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'decryptors',
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        DecryptionUtils.register_config_value_decryptor(SOPS())

        sops_mock.side_effect=create_sops_side_effect('mock decrypted value')
        decrypted_value = config_value.value
        sops_mock.assert_called_once_with(
            '--decrypt',
            '--extract=["step-runner-config"]["global-environment-defaults"]["DEV"]["kube-api-token"]',
            None,
            encrypted_config_file_path,
            _in=None,
            _out=Any(StringIO),
            _err=Any(StringIO)
        )
        self.assertEqual(
            decrypted_value,
            'mock decrypted value'
        )
