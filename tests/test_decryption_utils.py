
from tssc.decription_utils import DecryptionUtils
from tssc.config.config_value import TSSCConfigValue
from tssc.config.config_value_decryptor import ConfigValueDecryptor
from tssc.utils.io import TextIOSelectiveObfuscator

from contextlib import redirect_stdout
import io
import unittest
import re
import sys

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

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

class TestDecryptionUtils(BaseTSSCTestCase):
    def test_decrypt_no_decryptors(self):
        config_value = TSSCConfigValue(
            'attempt to decrypt me'
        )
        decrypted_value = DecryptionUtils.decrypt(
            config_value
        )
        self.assertIsNone(decrypted_value)

    def test_decrypt_sample_decryptor_does_not_match(self):
        config_value = TSSCConfigValue(
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
        config_value = TSSCConfigValue(
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
        config_value = TSSCConfigValue(
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
