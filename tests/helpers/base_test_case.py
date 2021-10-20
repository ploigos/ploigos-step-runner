import unittest
import shutil
from re import escape

from ploigos_step_runner.decryption_utils import DecryptionUtils

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        try:
            self.maxDiff = None
            shutil.rmtree("./step-runner-working")
        except FileNotFoundError:
            pass

    def tearDown(self):
        DecryptionUtils._DecryptionUtils__config_value_decryptors = []
        DecryptionUtils._DecryptionUtils__obfuscation_streams = []

        try:
            shutil.rmtree("./step-runner-working")
        except FileNotFoundError:
            pass

    def assertRaisesMessage(
            self,
            exception,
            message: str
    ):
        """Asserts that the function call wrapped raises an exception with the literal message `message`."""
        return self.assertRaisesRegex(
            exception,
            escape(message)
        )
