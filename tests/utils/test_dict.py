import os

import unittest
from testfixtures import TempDirectory

from tests.helpers.base_test_case import BaseTestCase

from ploigos_step_runner.utils.dict import deep_merge

class TestDictUtils(BaseTestCase):
    def test_deep_merge_no_conflict(self):
        dict1 = {
            'step-runner-config': {
                'step-foo': {
                    'implementer': 'foo1',
                    'config': {
                        'test0': 'foo',
                        'test1': 'foo'
                    }
                }
            }
        }

        dict2 = {
            'step-runner-config': {
                'step-foo': {
                    'implementer': 'foo1',
                    'config': {
                        'test2': 'bar'
                    }
                }
            }
        }

        result = deep_merge(dict1, dict2)

        # assert that it is in an inplace deep merge of the first param
        self.assertEqual(result, dict1)

        # assert expected merge result
        self.assertEqual(result, {
            'step-runner-config': {
                'step-foo': {
                    'implementer': 'foo1',
                    'config': {
                        'test0': 'foo',
                        'test1': 'foo',
                        'test2': 'bar'
                    }
                }
            }
        })

    def test_deep_merge_conflict_no_overwrite(self):
        dict1 = {
            'step-runner-config': {
                'step-foo': {
                    'implementer': 'foo1',
                    'config': {
                        'test0': 'foo',
                        'test1': 'foo'
                    }
                }
            }
        }

        dict2 = {
            'step-runner-config': {
                'step-foo': {
                    'implementer': 'foo1',
                    'config': {
                        'test1': 'bar',
                        'test2': 'bar'
                    }
                }
            }
        }

        with self.assertRaisesRegex(
                ValueError,
                r"Conflict at step-runner-config.step-foo.config.test1"):

            deep_merge(dict1, dict2)

    def test_deep_merge_conflict_overwrite_duplicate_keys(self):
        dict1 = {
            'step-runner-config': {
                'step-foo': {
                    'implementer': 'foo1',
                    'config': {
                        'test0': 'foo',
                        'test1': 'foo'
                    }
                }
            }
        }

        dict2 = {
            'step-runner-config': {
                'step-foo': {
                    'implementer': 'foo1',
                    'config': {
                        'test1': 'bar',
                        'test2': 'bar'
                    }
                }
            }
        }

        result = deep_merge(
            dest=dict1,
            source=dict2,
            overwrite_duplicate_keys=True
        )

        # assert expected merge result
        self.assertEqual(result, {
            'step-runner-config': {
                'step-foo': {
                    'implementer': 'foo1',
                    'config': {
                        'test0': 'foo',
                        'test1': 'bar',
                        'test2': 'bar'
                    }
                }
            }
        })
