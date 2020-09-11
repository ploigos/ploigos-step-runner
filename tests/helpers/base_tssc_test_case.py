import unittest
import shutil

from tssc.decription_utils import DecryptionUtils

class BaseTSSCTestCase(unittest.TestCase):
    def setUp(self):
        try:
            self.maxDiff = None
            shutil.rmtree("./tssc-working")
        except FileNotFoundError:
            pass

    def tearDown(self):
        DecryptionUtils._DecryptionUtils__config_value_decryptors = []

        try:
            shutil.rmtree("./tssc-working")
        except FileNotFoundError:
            pass