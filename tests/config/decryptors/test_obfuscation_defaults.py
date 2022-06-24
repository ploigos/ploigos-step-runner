from unittest import TestCase
from ploigos_step_runner.config.decryptors.obfuscation_defaults import ObfuscationDefaults
from ploigos_step_runner.config.config_value import ConfigValue

import os

class TestObfuscationDefaults(TestCase):

    def test_can_decrypt_password(self):
        # GIVEN an ObfuscationDefaults
        obfuscation_defaults = ObfuscationDefaults()

        # GIVEN a ConfigValue that is a password
        config_value = self.config_value_like("admin-password-for-tool", "abc123")

        # WHEN I test if a password should be obfuscated
        actual_result = obfuscation_defaults.can_decrypt(config_value)

        # THEN it should be obfuscated
        self.assertTrue(actual_result)

    def test_can_decrypt_username(self):
        # GIVEN an ObfuscationDefaults
        obfuscation_defaults = ObfuscationDefaults()

        # GIVEN a ConfigValue that is a username
        config_value = self.config_value_like("username", "my-username")

        # WHEN I test if a username should be obfuscated
        actual_result = obfuscation_defaults.can_decrypt(config_value)

        # THEN it should be obfuscated
        self.assertTrue(actual_result)

    def test_decrypt(self):
        # GIVEN ObfuscationDefaults
        obfuscation_defaults = ObfuscationDefaults()

        # GIVEN a ConfigValue that is not really encrypted
        config_value = self.config_value_like("my-key", "plain-text-value")

        # WHEN I "decrypt" a value
        decrypted_value = obfuscation_defaults.decrypt(config_value)

        # THEN I should get the same exact value (because this class does not actually decrypt things)
        self.assertEqual(decrypted_value, "plain-text-value", "Expected the (not really) decrypted value to be the same as the plain text input, but it was not")

    # Create a ConfigValue to test with
    def config_value_like(self, key, value):
        encrypted_config_file_path = os.path.join('config', 'psr.yml')
        return ConfigValue(
            value=value,
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-defaults', key] # We do not care about the YAML path, just the key of the final key/value pair
        )
