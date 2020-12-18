import os

import unittest
from testfixtures import TempDirectory

from tests.helpers.base_test_case import BaseTestCase

from ploigos_step_runner.utils.reflection import import_and_get_class

class TestReflectionUtils(BaseTestCase):
    def test_import_and_get_class_module_does_not_exist(self):
        self.assertIsNone(
            import_and_get_class('does.not.exist', 'HelloWorld')
        )

    def test_import_and_get_class_class_does_not_exist(self):
        self.assertIsNone(
            import_and_get_class('ploigos_step_runner.step_implementers.package', 'HelloWorld')
        )

    def test_import_and_get_class_class_exists_in_module(self):
        self.assertIsNotNone(
            import_and_get_class('ploigos_step_runner.step_implementers.container_image_static_compliance_scan', 'OpenSCAP')
        )
