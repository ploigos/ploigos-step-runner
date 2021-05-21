import json
import os
import re
# import sh
import hashlib
from pathlib import Path

import sh
from testfixtures import TempDirectory
from ploigos_step_runner.step_implementers.automated_governance import Rekor
from ploigos_step_runner.step_result import StepResult
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from unittest.mock import patch


class TestStepImplementerAutomatedGovernanceRekor(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Rekor,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def create_rekor_side_effect(self, rekor_server):
        def rekor_side_effect(*args, **kwargs):
            print('Created entry at: '+rekor_server+'/')
        return rekor_side_effect

    def test_step_implementer_config_defaults(self):
        defaults = Rekor.step_implementer_config_defaults()
        expected_defaults = {
            'rekor-server': 'http://rekor.apps.tssc.rht-set.com',
            'gpg-key': '/var/pgp-private-keys/gpg_public_key',
            'gpg-user': 'tssc-service-account@redhat.com'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Rekor._required_config_or_result_keys()
        expected_required_keys = [
            'rekor-server',
            'gpg-key',
            'gpg-user'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    @patch('sh.rekor', create=True)
    def test_get_all_dicts(self, rekor_mock):
        """
        Testing extra_data in rekor_entry
        """
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            gpg_key = os.path.join(
                os.path.dirname(__file__),
                '../../helpers','files',
                'ploigos-step-runner-tests-public.key'
            )

            gpg_user = 'tssc-service-account@redhat.com'
            try:
                sh.gpg('--import', gpg_key)
            except sh.ErrorReturnCode_2:
                print("Key already imported.")

            step_config = {'rekor-server': 'http://rekor.apps.tssc.rht-set.com',
                           'gpg-key': gpg_key,
                           'gpg-user': gpg_user
                           }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='automated_governance',
                implementer='Rekor',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            expected_step_result = StepResult(
                step_name='automated_governance',
                sub_step_name='Rekor',
                sub_step_implementer_name='Rekor'
            )
            rekor_uuid = "None"
            expected_step_result.add_artifact(name='rekor-uuid', value=rekor_uuid)
            rekor_entry = {
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
                        "content": "eyJzdGVwLXJ1bm5lci1yZXN1bHRzIjoge319",
                        "hash": {
                            "algorithm": "sha256",
                            "value": "b8d466b27b60a1e995b904d917bf997628ced94e3f55512a07ae2982da1a0c19"
                        }
                    },
                    "extraData": "eyJzdGVwLXJ1bm5lci1yZXN1bHRzIjoge319"
                }
            }
            rekor_mock.side_effect = self.create_rekor_side_effect(step_config['rekor-server'])
            expected_step_result.add_artifact(name='rekor-entry', value=rekor_entry)
            result = step_implementer._run_step()

            self.assertEqual(result.get_artifact_value('rekor-entry').get('spec',{}).get('extraData'), 'eyJzdGVwLXJ1bm5lci1yZXN1bHRzIjoge319')
