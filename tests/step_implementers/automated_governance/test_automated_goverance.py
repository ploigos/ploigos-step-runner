import json
import os
import re
from io import IOBase
import hashlib
from pathlib import Path

import sh
from testfixtures import TempDirectory
from ploigos_step_runner.step_implementers.automated_governance import Rekor
from ploigos_step_runner import WorkflowResult, StepResult
from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from unittest.mock import patch
from tests.helpers.test_utils import Any


class TestStepImplementerAutomatedGovernanceRekor(BaseStepImplementerTestCase):
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
                    "value": "e2162714a1c0e2f6a362f0596514a8d37458db058cc82a728c3717c9275b1d81"
                }
            },
            "extraData": "ewogICAgInN0ZXAtcnVubmVyLXJlc3VsdHMiOiB7fQp9"
        }
    }

    TEST_REKOR_UUID = 'b08416d417acdb0610d4a030d8f697f9d0a718024681a00fa0b9ba67072a38b5'
    TEST_REKOR_SERVER = 'http://rekor.apps.tssc.rht-set.com'
    TEST_GPG_USER = 'tssc-python-package-tests'

    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Rekor,
            step_config=step_config,
            step_name='automated_governance',
            implementer='Rekor',
            workflow_result=workflow_result,
            work_dir_path=work_dir_path
        )

    def test__required_config_or_result_keys(self):
        required_keys = Rekor._required_config_or_result_keys()
        expected_required_keys = [
            'rekor-server',
            'gpg-key',
            'gpg-user'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def test_create_rekor_entry(self):
        with TempDirectory() as temp_dir:
            work_dir_path = os.path.join(temp_dir.path, 'working')
            gpg_key = os.path.join(
                os.path.dirname(__file__),
                '../../helpers','files',
                'ploigos-step-runner-tests-public.key'
            )

            try:
                sh.gpg('--import', gpg_key)
            except sh.ErrorReturnCode_2:
                print("Key already imported.")

            # Write empty WorkflowResult to json file to use as Rekor extra data
            extra_data_file = os.path.join(work_dir_path, 'automated_governance.json')
            extra_data_file_path = Path(extra_data_file)
            WorkflowResult().write_results_to_json_file(extra_data_file_path)

            sig_file = extra_data_file + '.asc'
            sig_file_path = Path(sig_file)
            sig_file_path.touch()

            result = Rekor.create_rekor_entry(
                public_key_path=gpg_key,
                gpg_user=TestStepImplementerAutomatedGovernanceRekor.TEST_GPG_USER,
                extra_data_file=extra_data_file
            )
            self.assertEqual(result['spec']['data']['hash']['value'], TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_ENTRY['spec']['data']['hash']['value'])
            self.assertEqual(result['spec']['extraData'], TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_ENTRY['spec']['extraData'])

    @patch.object(Rekor, 'create_rekor_entry')
    @patch('sh.rekor', create=True)
    def test_upload_to_rekor(self, rekor_mock, create_mock):
        with TempDirectory() as temp_dir:
            work_dir_path = os.path.join(temp_dir.path, 'working')
            gpg_key = os.path.join(
                os.path.dirname(__file__),
                '../../helpers','files',
                'ploigos-step-runner-tests-public.key'
            )

            extra_data_file = os.path.join(work_dir_path, 'automated_governance.json')
            extra_data_file_path = Path(extra_data_file)
            WorkflowResult().write_results_to_json_file(extra_data_file_path)
            rekor_entry_path_name = os.path.join(work_dir_path, 'entry.json')

            def create_mock_side_effect(public_key_path, gpg_user, extra_data_file):
                return TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_ENTRY

            def rekor_mock_side_effect(*args, **kwargs):
                return 'Created entry at: ' + args[2]+ '/api/v1/log/entries/' + TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_UUID

            create_mock.side_effect = create_mock_side_effect
            rekor_mock.side_effect = rekor_mock_side_effect

            rekor_entry_path = Path(rekor_entry_path_name)
            rekor_entry_path.touch()

            result_entry, result_uuid = Rekor.upload_to_rekor(
                rekor_server=TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_SERVER,
                extra_data_file=extra_data_file,
                gpg_key=gpg_key,
                gpg_user=TestStepImplementerAutomatedGovernanceRekor.TEST_GPG_USER,
                work_dir_path=work_dir_path
            )

            rekor_mock.assert_called_once_with(
                'upload',
                '--rekor_server',
                TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_SERVER,
                '--entry',
                rekor_entry_path_name,
                _out=Any(IOBase),
                _err_to_out=True,
                _tee='out'
            )
            self.assertEqual(result_entry, TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_ENTRY)
            self.assertEqual(result_uuid, TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_UUID)

    @patch.object(Rekor, 'upload_to_rekor')
    def test__run_step(self, upload_mock):
        """
        Testing extra_data in rekor_entry
        """
        with TempDirectory() as temp_dir:
            work_dir_path = os.path.join(temp_dir.path, 'working')
            gpg_key = os.path.join(
                os.path.dirname(__file__),
                '../../helpers','files',
                'ploigos-step-runner-tests-public.key'
            )

            step_config = {'rekor-server': TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_SERVER,
                           'gpg-key': gpg_key,
                           'gpg-user': TestStepImplementerAutomatedGovernanceRekor.TEST_GPG_USER
                           }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                work_dir_path=work_dir_path,
            )

            expected_step_result = StepResult(
                step_name='automated_governance',
                sub_step_name='Rekor',
                sub_step_implementer_name='Rekor'
            )

            expected_step_result.add_artifact(name='rekor-entry', value=TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_ENTRY)
            expected_step_result.add_artifact(name='rekor-uuid', value=TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_UUID)

            def upload_mock_side_effect(rekor_server, extra_data_file, gpg_key, gpg_user, work_dir_path):
                return TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_ENTRY, TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_UUID

            upload_mock.side_effect = upload_mock_side_effect

            extra_data_file = os.path.join(work_dir_path, 'automated_governance.json')
            extra_data_file_path = Path(extra_data_file)
            WorkflowResult().write_results_to_json_file(extra_data_file_path)

            result = step_implementer._run_step()
            upload_mock.assert_called_once_with(
                TestStepImplementerAutomatedGovernanceRekor.TEST_REKOR_SERVER,
                extra_data_file,
                gpg_key,
                TestStepImplementerAutomatedGovernanceRekor.TEST_GPG_USER,
                work_dir_path
            )

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())
