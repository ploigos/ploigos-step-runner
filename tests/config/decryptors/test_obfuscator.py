from io import StringIO
import json
import os.path
import sh

import unittest
from testfixtures import TempDirectory
from unittest.mock import patch

from tests.helpers.base_test_case import BaseTestCase
from tests.helpers.test_utils import Any

from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.config.decryptors.obfuscation_defaults import ObfuscationDefaults
from ploigos_step_runner.utils.file import parse_yaml_or_json_file


class TestObfuscatorConfigValueDecryptor(BaseTestCase):
    def test_can_decrypt_true(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-obfuscate-stuff.yml'
        )

        config_value = ConfigValue(
            value='FUQQW2PERIU3ZXCMNVAOIS7UERLKJLAJDFJ3ZVE2ZVQCD',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-defaults', 'container-registries', 'quay.io', 'password']
        )

        obfuscation_defaults = ObfuscationDefaults()
        self.assertTrue(
            obfuscation_defaults.can_decrypt(config_value)
        )

    def test_can_decrypt_false(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-obfuscate-stuff.yml'
        )

        config_value = ConfigValue(
            value='not an obfuscated value',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        obfuscation_defaults = ObfuscationDefaults()
        self.assertFalse(
            obfuscation_defaults.can_decrypt(config_value)
        )

    def test_can_can_decrypt_not_string(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-obfuscate-stuff.yml'
        )

        config_value = ConfigValue(
            value=True,
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        obfuscation_defaults = ObfuscationDefaults()
        self.assertFalse(
            obfuscation_defaults.can_decrypt(config_value)
        )

    def test_get_decrypt_value(self):
        config_value = ConfigValue(
            value='raw_value',
            parent_source=None,
            path_parts=["step-runner-config", "step-foo", 0, "config", "test1"]
        )
        obfuscation_defaults = ObfuscationDefaults()
        self.assertEqual(
            obfuscation_defaults.decrypt(config_value),
            'raw_value')
