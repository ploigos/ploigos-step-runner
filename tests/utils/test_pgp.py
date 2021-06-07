import hashlib
import os
import re
import sys
import sh
from io import IOBase
from tests.helpers.test_utils import Any
from unittest.mock import patch

from ploigos_step_runner.utils.pgp import (detach_sign_with_pgp_key, import_pgp_key)
from tests.helpers.base_test_case import BaseTestCase
from ploigos_step_runner.exceptions import StepRunnerException

class TestImportPGPKey(BaseTestCase):
    TEST_FAKE_PRIVATE_KEY = '''
        -----BEGIN RSA PRIVATE KEY-----
        MIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp
        wmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5
        1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh
        3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2
        pIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX
        GukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il
        AkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF
        L0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k
        X6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl
        U9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ
        37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=
        -----END RSA PRIVATE KEY-----'''

    @staticmethod
    def gpg_side_effect(*_args, **kwargs):
        """Side effect for gpg key load"""
        kwargs['_out']('fpr:::::::::DD7208BA0A6359F65B906B29CF4AC14A3D109637:')

    @patch('sh.gpg', create=True)
    def test_import_pgp_key_success(self, gpg_mock):
        gpg_mock.side_effect = TestImportPGPKey.gpg_side_effect

        pgp_private_key = TestImportPGPKey.TEST_FAKE_PRIVATE_KEY
        import_pgp_key(
            pgp_private_key=pgp_private_key
        )
        gpg_mock.assert_called_once_with(
            '--import',
            '--fingerprint',
            '--with-colons',
            '--import-options=import-show',
            _in=pgp_private_key,
            _out=Any(IOBase),
            _err_to_out=True,
            _tee='out'
        )

    @patch('sh.gpg', create=True)
    def test_import_pgp_key_gpg_import_fail(self, gpg_mock):
        gpg_mock.side_effect = sh.ErrorReturnCode('gpg', b'mock stdout', b'mock error')

        pgp_private_key = TestImportPGPKey.TEST_FAKE_PRIVATE_KEY

        with self.assertRaisesRegex(
            RuntimeError,
            re.compile(
                r"Error importing pgp private key:"
                r".*RAN: gpg"
                r".*STDOUT:"
                r".*mock stdout"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            )
        ):
            import_pgp_key(
                pgp_private_key=pgp_private_key
            )

        gpg_mock.assert_called_once_with(
            '--import',
            '--fingerprint',
            '--with-colons',
            '--import-options=import-show',
            _in=pgp_private_key,
            _out=Any(IOBase),
            _err_to_out=True,
            _tee='out'
        )

    @patch('sh.gpg', create=True)
    def test_import_pgp_key_fail_get_fingerprint(self, gpg_mock):
        pgp_private_key = TestImportPGPKey.TEST_FAKE_PRIVATE_KEY

        with self.assertRaisesRegex(
            RuntimeError,
            re.compile(
                r"Error getting PGP fingerprint for PGP key"
                r" to sign container image\(s\) with. See stdout and stderr for more info.",
                re.DOTALL
            )
        ):
            import_pgp_key(
                pgp_private_key=pgp_private_key
            )

        gpg_mock.assert_called_once_with(
            '--import',
            '--fingerprint',
            '--with-colons',
            '--import-options=import-show',
            _in=pgp_private_key,
            _out=Any(IOBase),
            _err_to_out=True,
            _tee='out'
        )

class TestDetachSignWithPGPKey(BaseTestCase):
    @patch('sh.gpg', create=True)
    def test_detach_sign_with_pgp_key_success(self, gpg_mock):

        detach_sign_with_pgp_key(
            file_to_sign_path='/mock/file-to-detach-sign.txt',
            pgp_private_key_fingerprint='355C137F36628365E42F6D79AF9B11B55E8305E1',
            output_signature_path='/mock/file-to-detach-sign.sig'
        )

        gpg_mock.assert_called_once_with(
            '--armor',
            '--local-user',
            '355C137F36628365E42F6D79AF9B11B55E8305E1',
            '--output',
            '/mock/file-to-detach-sign.sig',
            '--detach-sign',
            '/mock/file-to-detach-sign.txt'
        )

    @patch('sh.gpg', create=True)
    def test_detach_sign_with_pgp_key_failure(self, gpg_mock):
        gpg_mock.side_effect = sh.ErrorReturnCode('gpg', b'mock stdout', b'mock error')

        with self.assertRaisesRegex(
            RuntimeError,
            re.compile(
                r'Error performing detached signature of file \(/mock/file-to-detach-sign.txt\)'
                r' with PGP key \(355C137F36628365E42F6D79AF9B11B55E8305E1\):'
                r".*RAN: gpg"
                r".*STDOUT:"
                r".*mock stdout"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            )
        ):
            detach_sign_with_pgp_key(
                file_to_sign_path='/mock/file-to-detach-sign.txt',
                pgp_private_key_fingerprint='355C137F36628365E42F6D79AF9B11B55E8305E1',
                output_signature_path='/mock/file-to-detach-sign.sig'
            )

        gpg_mock.assert_called_once_with(
            '--armor',
            '--local-user',
            '355C137F36628365E42F6D79AF9B11B55E8305E1',
            '--output',
            '/mock/file-to-detach-sign.sig',
            '--detach-sign',
            '/mock/file-to-detach-sign.txt'
        )
