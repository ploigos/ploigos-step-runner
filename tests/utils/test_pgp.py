import hashlib
import os
import re
import sys
import sh
from io import IOBase
from tests.helpers.test_utils import Any
from unittest.mock import patch

from ploigos_step_runner.utils.pgp import (detach_sign_with_pgp_key, import_pgp_key, export_pgp_public_key)
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

class TestExportPGPKey(BaseTestCase):

    TEST_FAKE_FINGERPRINT = 'DEB72DAF711EF3586266C98D9D65E8ECADD724B4'

    TEST_FAKE_PUBLIC_KEY = '''\
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQENBGDKRgEBCACyVB9ZZodlYBf5Fw5iWCohDyjFkypQjRFVaQz8XbvOzrU0reNy
fQpXFzEiNcGxhUHDM538Zv/adIOWMj3EvFTEuCY9I5DSfi4A8AfjSxLMUVSJ85f9
rmHWKoCKoadF7FduKWnGEUk4woVNmhoVqpNMbV6IczNX2vmr7omx4/KgLu4k8WeW
3C0ItJES1fTz9epfynpndXZ9+Iiqiyx8d2cWcVtodv60bJkVIGdLhvyn3/vfSFvf
iSkw4FcKjpXt0k7Kd0e2mv5PHqEYWtkN41p6hDClu3i4EgnFwRjJK9H7lUPcttIJ
hS44e5HhLrihPVK91HZ5Eh0k5jpgQpkNV+ntABEBAAG0O0pvaG4gVGhvbXBraW5z
IChSZWQgSGF0KSAoTm8gY29tbWVudCkgPGp0aG9tcGtpQHJlZGhhdC5jb20+iQFO
BBMBCAA4FiEE3rctr3Ee81hiZsmNnWXo7K3XJLQFAmDKRgECGwMFCwkIBwIGFQoJ
CAsCBBYCAwECHgECF4AACgkQnWXo7K3XJLQANAgAjp5GQALhmhaxLXQJs9tmLzgB
VLOTn6r3z6emlIjjxZYlwLCV+xXZ12Igg+1L5IJo0Nrk2xmcAgp+3WScx29xtkbW
j44jt7eghH4clkSau8RTJWQlyMyzmLVGEDgqBr+YICcnV85NS31ILigvMorKgszP
RVJpG9G+GQRNm7L17sQUSYItX/4ZAbzBr/RhD4IRkgwFxlgrsVujcGN4UMQ2f+uy
b7jY7Gx4o3lKZc+2rFAp6Z9xkChdl69UzJA9Cb7MGNPDE2rFItqXQRUX+4bVOWjy
ffPOuPFqVZJ4989lAfNFh5zitVs2aYGMuWbrRp/AMqBY+2AWw+78/Gv2b6iPfbkB
DQRgykYBAQgAxYk3SS3wk3vGjGF8qAQ6AnMnU2XpqlGt9uTJnChDyzhb964Yxx6+
vN3EqChoAROjyaUQN2GzmUezm1kNDa9sw4KE+a50d5nJqEniz4UvUUTzi9FluTb5
EkRGr1zP0rd1PPWvMB9gil2lie4d7O9iwYT5KUDhiEB+LH8GvI0YENcYDN46CBvG
Qb89qhttXYp22DIll3mQPoabdmWFYD1xYRGoEwP/Zjkx+9MPOASStD4oaULkHoDn
qNMQNrVEY9YQ6JrG55a2XTLEcBaWmLyGnytRjVSs0xp8fzZCwTDgCkcoyAnNrQ7k
wiJJV3fvHP5i6meEdPdRSR4Bwc173ZzUdQARAQABiQE2BBgBCAAgFiEE3rctr3Ee
81hiZsmNnWXo7K3XJLQFAmDKRgECGwwACgkQnWXo7K3XJLS24AgAoGke/g08/FEz
Fml1e81zYEB6+GyggQS365JA16Ev+nvOQbjEk55PvZFfNMbsI0T7IamweX3BzlPf
Sb8HZsjJp0SNlhu7I1P4X3nMa2OofSEE8qd3ptEmAWqewhW+DqGDA23ccAO+VDSj
UvF+nhrYFM/BJY/SE5QyDcDRuJUG3hEAN0FPGSEbWZoAgPpQKdmwLwHeTtdadvAH
NNqw3gdbZjlF+RQbggHc4sXtK/H7wk3SU501BgP10GkfsFUekGiAlkAmYAO6gUnQ
1cfRMdTTzuGVc6j/8VshK1aYRR5A3g5rP4ZbNReqQddZmB20qe4ekkFKbRvHX/Em
B8pBNt1QOA==
=u6VF
-----END PGP PUBLIC KEY BLOCK-----
'''


    @staticmethod
    def gpg_side_effect(*_args, **kwargs):
        """Side effect for gpg key load"""
        kwargs['_out']('gpg: WARNING: nothing exported')

    @patch('sh.gpg', create=True)
    def test_export_pgp_public_key_success(self, gpg_mock):
        gpg_mock.side_effect = TestExportPGPKey.TEST_FAKE_PUBLIC_KEY

        pgp_private_key_fingerprint = TestExportPGPKey.TEST_FAKE_FINGERPRINT
        
        export_pgp_public_key(
            pgp_private_key_fingerprint=pgp_private_key_fingerprint
        )
        gpg_mock.assert_called_once_with(
            '--armor',
            '--export',
            pgp_private_key_fingerprint,
            _out=Any(IOBase),
            _err_to_out=False,
            _tee='out'
        )
        

    @patch('sh.gpg', create=True)
    def test_export_pgp_public_key_failure(self, gpg_mock):
        gpg_mock.side_effect = sh.ErrorReturnCode('gpg', b'mock stdout', b'mock error')
        with self.assertRaisesRegex(
            RuntimeError,
            re.compile(
                r'Error exporting pgp public key:'
                r".*RAN: gpg"
                r".*STDOUT:"
                r".*mock stdout"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            )
        ):
            pgp_private_key_fingerprint = TestExportPGPKey.TEST_FAKE_FINGERPRINT
            export_pgp_public_key(
                pgp_private_key_fingerprint=pgp_private_key_fingerprint
            )

        gpg_mock.assert_called_once_with(
            '--armor',
            '--export',
            pgp_private_key_fingerprint,
            _out=Any(IOBase),
            _err_to_out=False,
            _tee='out'
        )