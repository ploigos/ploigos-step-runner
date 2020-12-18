

from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.config.config_value_decryptor import ConfigValueDecryptor
from ploigos_step_runner.decryption_utils import DecryptionUtils
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import TextIOSelectiveObfuscator
from ploigos_step_runner.config.decryptors.sops import SOPS

from contextlib import redirect_stdout
import io
import unittest
import re
import sys

from tests.helpers.base_test_case import BaseTestCase

class SampleConfigValueDecryptor(ConfigValueDecryptor):
    ENCRYPTED_VALUE_REGEX = r'^TEST_ENC\[(.*)\]$'

    def can_decrypt(self, config_value):
        return re.match(
            SampleConfigValueDecryptor.ENCRYPTED_VALUE_REGEX,
            config_value.raw_value
        ) is not None

    def decrypt(self, config_value):
        return re.match(
            SampleConfigValueDecryptor.ENCRYPTED_VALUE_REGEX,
            config_value.raw_value
        ).group(1)

class RequiredConstructorParamsConfigValueDecryptor(ConfigValueDecryptor):
    ENCRYPTED_VALUE_REGEX = r'^TEST_ENC\[(.*)\]$'

    def __init__(self, required_arg):
        assert required_arg is not None

    def can_decrypt(self, config_value):
        return re.match(
            SampleConfigValueDecryptor.ENCRYPTED_VALUE_REGEX,
            config_value.raw_value
        ) is not None

    def decrypt(self, config_value):
        return re.match(
            SampleConfigValueDecryptor.ENCRYPTED_VALUE_REGEX,
            config_value.raw_value
        ).group(1)

class BadConfigValueDecryptor:
    pass

class TestDecryptionUtils(BaseTestCase):
    def test_decrypt_no_decryptors(self):
        config_value = ConfigValue(
            'attempt to decrypt me'
        )
        decrypted_value = DecryptionUtils.decrypt(
            config_value
        )
        self.assertIsNone(decrypted_value)

    def test_decrypt_sample_decryptor_does_not_match(self):
        config_value = ConfigValue(
            'attempt to decrypt me'
        )

        DecryptionUtils.register_config_value_decryptor(
            SampleConfigValueDecryptor()
        )

        decrypted_value = DecryptionUtils.decrypt(
            config_value
        )
        self.assertIsNone(decrypted_value)

    def test_decrypt_sample_decryptor(self):
        secret_value = "decrypt me"
        config_value = ConfigValue(
            f'TEST_ENC[{secret_value}]'
        )

        DecryptionUtils.register_config_value_decryptor(
            SampleConfigValueDecryptor()
        )

        decrypted_value = DecryptionUtils.decrypt(
            config_value
        )
        self.assertEqual(
            decrypted_value,
            secret_value
        )

    def test_register_obfuscation_stream(self):
        secret_value = "decrypt me"
        config_value = ConfigValue(
            f'TEST_ENC[{secret_value}]'
        )

        DecryptionUtils.register_config_value_decryptor(
            SampleConfigValueDecryptor()
        )

        out = io.StringIO()
        with redirect_stdout(out):
            old_stdout = sys.stdout
            new_stdout = TextIOSelectiveObfuscator(old_stdout)
            DecryptionUtils.register_obfuscation_stream(new_stdout)

            try:
                sys.stdout = new_stdout
                DecryptionUtils.decrypt(config_value)

                print(f"ensure that I can't actually leak secret value ({secret_value})")
                self.assertRegex(
                    out.getvalue(),
                    r"ensure that I can't actually leak secret value \(\*+\)"
                )
            finally:
                new_stdout.close()
                sys.stdout = old_stdout

    def test__get_decryption_class_sops_short_name(self):
        decryptor_class = DecryptionUtils._DecryptionUtils__get_decryption_class('SOPS')
        self.assertEqual(
            decryptor_class,
            SOPS
        )

    def test__get_decryption_class_sops_full_name(self):
        decryptor_class = DecryptionUtils._DecryptionUtils__get_decryption_class(
            'ploigos_step_runner.config.decryptors.sops.SOPS'
        )
        self.assertEqual(
            decryptor_class,
            SOPS
        )

    def test__get_decryption_class_does_not_exist_short_name(self):
        with self.assertRaisesRegex(
            StepRunnerException,
            r"Could not dynamically load decryptor implementer \(DoesNotExist\) " \
            r"from module \(ploigos_step_runner.config.decryptors\) with class name \(DoesNotExist\)"
        ):
            DecryptionUtils._DecryptionUtils__get_decryption_class('DoesNotExist')

    def test__get_decryption_class_does_not_exist_with_module_name(self):
        with self.assertRaisesRegex(
            StepRunnerException,
            r"Could not dynamically load decryptor implementer \(foo.bar.hello.DoesNotExist\) " \
            r"from module \(foo.bar.hello\) with class name \(DoesNotExist\)"
        ):
            DecryptionUtils._DecryptionUtils__get_decryption_class('foo.bar.hello.DoesNotExist')

    def test__get_decryption_class_not_correct_type(self):
        with self.assertRaisesRegex(
            StepRunnerException,
            r"For decryptor implementer \(tests.test_decryption_utils.BadConfigValueDecryptor\) " \
            r"dynamically loaded class \(<class 'tests.test_decryption_utils." \
            r"BadConfigValueDecryptor'>\) which is not sub class of " \
            r"\(<class 'ploigos_step_runner.config.config_value_decryptor.ConfigValueDecryptor'>\) and should be."
        ):
            DecryptionUtils._DecryptionUtils__get_decryption_class(
                'tests.test_decryption_utils.BadConfigValueDecryptor'
            )

    def test_create_and_register_config_value_decryptor_no_constructor_args(self):
        DecryptionUtils.create_and_register_config_value_decryptor(
            'tests.test_decryption_utils.SampleConfigValueDecryptor'
        )

        secret_value = "decrypt me"
        config_value = ConfigValue(
            f'TEST_ENC[{secret_value}]'
        )
        decrypted_value = DecryptionUtils.decrypt(
            config_value
        )
        self.assertEqual(
            decrypted_value,
            secret_value
        )

    def test_create_and_register_config_value_decryptor_required_constructor_args_missing_arg(self):
        with self.assertRaisesRegex(
            ValueError,
            r"Loaded decryptor class \(<class 'tests.test_decryption_utils." +
            r"RequiredConstructorParamsConfigValueDecryptor'>\) failed to construct with " +
            r"given constructor arguments \({}\): __init__\(\) missing 1 " +
            r"required positional argument: 'required_arg'"
        ):
            DecryptionUtils.create_and_register_config_value_decryptor(
                'tests.test_decryption_utils.RequiredConstructorParamsConfigValueDecryptor'
            )

    def test_create_and_register_config_value_decryptor_required_constructor_args(self):
        DecryptionUtils.create_and_register_config_value_decryptor(
            'tests.test_decryption_utils.RequiredConstructorParamsConfigValueDecryptor',
            {
                'required_arg': 'hello world'
            }
        )

        secret_value = "decrypt me"
        config_value = ConfigValue(
            f'TEST_ENC[{secret_value}]'
        )
        decrypted_value = DecryptionUtils.decrypt(
            config_value
        )
        self.assertEqual(
            decrypted_value,
            secret_value
        )
