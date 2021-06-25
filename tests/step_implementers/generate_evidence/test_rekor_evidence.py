
import os
from ploigos_step_runner.step_implementers.generate_evidence.rekor_sign_evidence import RekorSignEvidence
from testfixtures import TempDirectory
from tests.step_implementers.shared.test_rekor_sign_generic import \
    TestStepImplementerSharedRekorSignGeneric

class TestStepImplementerRekorEvidence(TestStepImplementerSharedRekorSignGeneric):
    def create_step_implementer_rekor_evidence(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path='',
    ):

        step_implementer = self.create_given_step_implementer(
            step_implementer=RekorSignEvidence,
            step_config=step_config,
            step_name='automated-governance',
            implementer='RekorSignEvidence',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
            )
        return step_implementer

    def test__validate_rekor_constructor(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                    'rekor-server-url': self.TEST_REKOR_SERVER_URL,
                    'signer-pgp-private-key': self.TEST_PGP_SIGNER_PRIVATE_KEY
                }
            step_implementer = self.create_step_implementer_rekor_evidence(
                    step_config=step_config,
                    parent_work_dir_path=parent_work_dir_path
                )

            artifact_to_sign_uri_config_key = step_implementer.artifact_to_sign_uri_config_key

            self.assertEqual(artifact_to_sign_uri_config_key, 'evidence-uri')

