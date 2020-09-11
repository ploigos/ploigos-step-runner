import unittest
import shutil

from tssc.decryption_utils import DecryptionUtils

class BaseTSSCTestCase(unittest.TestCase):
    def setUp(self):
        try:
            self.maxDiff = None
            shutil.rmtree("./tssc-working")
        except FileNotFoundError:
            pass

    def tearDown(self):
        DecryptionUtils._DecryptionUtils__config_value_decryptors = []
        DecryptionUtils._DecryptionUtils__obfuscation_streams = []

        try:
            shutil.rmtree("./tssc-working")
        except FileNotFoundError:
            pass