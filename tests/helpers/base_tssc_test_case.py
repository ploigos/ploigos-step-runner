import unittest
import shutil

class BaseTSSCTestCase(unittest.TestCase):
    def setUp(self):
        try:
            self.maxDiff = None
            shutil.rmtree("./tssc-working")
        except FileNotFoundError:
            pass

    def tearDown(self):
        try:
            shutil.rmtree("./tssc-working")
        except FileNotFoundError:
            pass