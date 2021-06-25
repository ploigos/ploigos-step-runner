import os
from io import IOBase
from pathlib import Path
from unittest.mock import patch

import sh
from shutil import copy
from ploigos_step_runner import StepResult, WorkflowResult
from ploigos_step_runner.config.config import Config
from ploigos_step_runner.step_implementers.shared import RekorSignGeneric
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any
from ploigos_step_runner.utils.pgp import detach_sign_with_pgp_key
from ploigos_step_runner.utils.pgp import import_pgp_key
from ploigos_step_runner.utils.pgp import export_pgp_public_key


class TestStepImplementerSharedRekorSignGeneric(BaseStepImplementerTestCase):
    TEST_REKOR_ENTRY = {
        "kind": "rekord",
        "apiVersion": "0.0.1",
        "spec": {
            "signature": {
                "format": "pgp",
                "content": "",
                "publicKey": {
                    "content": ""
                }
            },
            "data": {
                "content": "ewogICAgInN0ZXAtcnVubmVyLXJlc3VsdHMiOiB7fQp9",
                "hash": {
                    "algorithm": "sha256",
                    "value": "7e9bb92be27b8897c4be4e2b5a185a0823bd4b1f566ef81312a96bbc278cf716"
                }
            },
            "extraData": {
                    "signed-artifact-uri": "http://foo.bar/artifact_to_sign"
            }
        }
    }

    TEST_REKOR_UUID = 'b08416d417acdb0610d4a030d8f697f9d0a718024681a00fa0b9ba67072a38b5'
    TEST_REKOR_SERVER_URL = 'http://rekor.apps.tssc.rht-set.com'
    TEST_ARTIFACT_TO_SIGN_URI_CONFIG_KEY = 'test-key'
    TEST_ARTIFACT_TO_SIGN_URI = 'http://foo.bar/artifact_to_sign'
    TEST_PGP_SIGNER_PRIVATE_KEY = ""
    TEST_REKOR_ENTRY_URI='http://rekor.apps.tssc.rht-set.com/api/v1/log/entries/' + TEST_REKOR_UUID

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

    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path='',
            artifact_to_sign_uri_config_key=None
    ):

        step_implementer = self.create_given_step_implementer_rekor_sign_generic(
            step_implementer=RekorSignGeneric,
            step_config=step_config,
            step_name='automated-governance',
            implementer='RekorSignGeneric',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            artifact_to_sign_uri_config_key=artifact_to_sign_uri_config_key
            )
        return step_implementer

    def create_given_step_implementer_rekor_sign_generic(
        self,
        step_implementer,
        step_config={},
        step_name='',
        environment=None,
        implementer='',
        workflow_result=None,
        parent_work_dir_path='',
        artifact_to_sign_uri_config_key=None
    ):
        config = Config({
            Config.CONFIG_KEY: {
                step_name: [
                    {
                        'implementer': implementer,
                        'config': step_config
                    }
                ]

            }
        })
        step_config = config.get_step_config(step_name)
        sub_step_config = step_config.get_sub_step(implementer)

        if not workflow_result:
            workflow_result = WorkflowResult()

        step_implementer = step_implementer(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=sub_step_config,
            artifact_to_sign_uri_config_key=artifact_to_sign_uri_config_key,
            environment=environment
        )
        return step_implementer

    def test__required_config_or_result_keys(self):
        required_keys = RekorSignGeneric._required_config_or_result_keys()
        expected_required_keys = [
            'rekor-server-url',
            'signer-pgp-private-key'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    @patch('ploigos_step_runner.step_implementers.shared.rekor_sign_generic.detach_sign_with_pgp_key')
    @patch('ploigos_step_runner.step_implementers.shared.rekor_sign_generic.base64_encode')
    def test_create_rekor_entry(self,
        base64_encode_mock,
        detach_sign_with_pgp_key_mock):
        with TempDirectory() as temp_dir:
            signer_pgp_public_key_path = os.path.join(
                os.path.dirname(__file__),
                '../../helpers','files',
                'ploigos-step-runner-tests-public.key'
            )

            #Copy key file to temp directory since _create_rekor_entry outputs a detached
            #signature to a new file.
            tmp_key_path = os.path.join(temp_dir.path, 'public.key')
            copy(signer_pgp_public_key_path, tmp_key_path)

            signer_pgp_private_key_fingerprint = self.TEST_FAKE_FINGERPRINT

            signer_pgp_public_key = self.TEST_FAKE_PUBLIC_KEY

            base64_encode_mock.return_value = "mock64"

            result = RekorSignGeneric._create_rekor_entry(self,
                signer_pgp_public_key,
                signer_pgp_private_key_fingerprint,
                path_to_file=tmp_key_path,
                artifact_to_sign_uri=self.TEST_ARTIFACT_TO_SIGN_URI
            )

            self.assertEqual(result['spec']['data']['hash']['value'], self.TEST_REKOR_ENTRY['spec']['data']['hash']['value'])
            self.assertEqual(result['spec']['extraData'], self.TEST_REKOR_ENTRY['spec']['extraData'])

            detach_sign_with_pgp_key_mock.assert_called_once_with(
                output_signature_path = tmp_key_path + '.asc',
                file_to_sign_path = tmp_key_path,
                pgp_private_key_fingerprint=signer_pgp_private_key_fingerprint
            )

            base64_encode_mock.assert_any_call(
                tmp_key_path + '.asc',
            )


    @patch.object(RekorSignGeneric, '_create_rekor_entry')
    @patch('sh.rekor', create=True)
    def test_upload_to_rekor(self, rekor_mock, create_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            signer_pgp_public_key_path = os.path.join(
                os.path.dirname(__file__),
                '../../helpers','files',
                'ploigos-step-runner-tests-public.key'
            )

            step_config = {
                'rekor-server-url': self.TEST_REKOR_SERVER_URL,
                'signer-pgp-private-key': self.TEST_PGP_SIGNER_PRIVATE_KEY
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                artifact_to_sign_uri_config_key=self.TEST_ARTIFACT_TO_SIGN_URI
            )

            artifact_data_file = os.path.join(parent_work_dir_path, 'automated-governance', 'automated-governance.json')
            artifact_data_file_path = Path(artifact_data_file)
            WorkflowResult().write_results_to_json_file(artifact_data_file_path)
            rekor_entry_path_name = os.path.join(parent_work_dir_path, 'automated-governance', 'entry.json')

            def create_mock_side_effect(signer_pgp_public_key_path, signer_pgp_private_key_user, extra_data_file):
                return self.TEST_REKOR_ENTRY

            def rekor_mock_side_effect(*args, **kwargs):
                return 'Created entry at: ' + args[2]+ '/api/v1/log/entries/' + self.TEST_REKOR_UUID

            create_mock.side_effect = create_mock_side_effect
            rekor_mock.side_effect = rekor_mock_side_effect

            rekor_entry_path = Path(rekor_entry_path_name)
            rekor_entry_path.touch()

            result_uuid = step_implementer._upload_to_rekor(
                rekor_server=self.TEST_REKOR_SERVER_URL,
                rekor_entry=self.TEST_REKOR_ENTRY
            )

            rekor_mock.assert_called_once_with(
                'upload',
                '--rekor_server',
                self.TEST_REKOR_SERVER_URL,
                '--entry',
                rekor_entry_path_name,
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )
            self.assertEqual(result_uuid, self.TEST_REKOR_UUID)
    @patch('ploigos_step_runner.step_implementers.shared.rekor_sign_generic.export_pgp_public_key')
    @patch('ploigos_step_runner.step_implementers.shared.rekor_sign_generic.import_pgp_key')
    @patch('ploigos_step_runner.step_implementers.shared.rekor_sign_generic.download_source_to_destination')
    @patch.object(RekorSignGeneric, '_upload_to_rekor')
    @patch.object(RekorSignGeneric, '_create_rekor_entry')
    def test__run_step(self, create_mock,
        upload_mock,
        download_source_to_destination_mock,
        import_pgp_key_mock,
        export_pgp_public_key_mock):

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            signer_pgp_public_key_path = os.path.join(
                os.path.dirname(__file__),
                '../../helpers','files',
                'ploigos-step-runner-tests-public.key'
            )

            step_config = {
                'rekor-server-url': self.TEST_REKOR_SERVER_URL,
                'signer-pgp-private-key': self.TEST_FAKE_PRIVATE_KEY,
                self.TEST_ARTIFACT_TO_SIGN_URI_CONFIG_KEY: self.TEST_ARTIFACT_TO_SIGN_URI
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                artifact_to_sign_uri_config_key=self.TEST_ARTIFACT_TO_SIGN_URI_CONFIG_KEY
            )

            expected_step_result = StepResult(
                step_name='automated-governance',
                sub_step_name='RekorSignGeneric',
                sub_step_implementer_name='RekorSignGeneric'
            )

            expected_step_result.add_artifact(
                name='rekor-entry',
                value=self.TEST_REKOR_ENTRY
            )
            expected_step_result.add_artifact(
                name='rekor-uuid',
                value=self.TEST_REKOR_UUID
            )
            rekor_uri = self.TEST_REKOR_ENTRY_URI
            expected_step_result.add_artifact(
                name='rekor-entry-uri',
                value=rekor_uri

            )

            download_source_to_destination_mock.return_value = signer_pgp_public_key_path
            import_pgp_key_mock.return_value = self.TEST_FAKE_FINGERPRINT
            export_pgp_public_key_mock.return_value = self.TEST_FAKE_PUBLIC_KEY

            create_mock.return_value = self.TEST_REKOR_ENTRY
            upload_mock.return_value = self.TEST_REKOR_UUID

            result = step_implementer._run_step()

            self.assertEqual(result, expected_step_result)
