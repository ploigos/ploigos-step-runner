import os
import unittest
import re

from ploigos_step_runner.utils.strutils import strtobool

from tests.helpers.base_test_case import BaseTestCase

class TestStringUtils(BaseTestCase):
    def test_strtobool_true(self):
        self.assertEqual(
            1,
            strtobool(val="True")
        )

    def test_strtobool_false(self):
        self.assertEqual(
            0,
            strtobool(val="False")
        )

    def test_strtobool_error(self):
        bad_value = "Maybe"

        with self.assertRaisesRegex(
            ValueError,
            re.compile(
                rf"invalid truth value {bad_value}",
                re.DOTALL
            )
        ):
            strtobool(val=bad_value)

