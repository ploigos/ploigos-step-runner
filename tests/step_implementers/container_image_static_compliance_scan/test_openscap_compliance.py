import os
import re

import tests.step_implementers.shared.test_openscap_generic
from ploigos_step_runner.step_implementers.container_image_static_compliance_scan import \
    OpenSCAP
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class BaseTestStepImplementerContainerImageStaticComplianceScanOpenSCAP(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='test',
            implementer='OpenSCAP',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=OpenSCAP,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

class TestStepImplementerContainerImageStaticComplianceScanOpenSCAP_step_implementer_config_defaults(
    BaseTestStepImplementerContainerImageStaticComplianceScanOpenSCAP,
    tests.step_implementers.shared.test_openscap_generic.TestStepImplementerSharedOpenSCAPGeneric_step_implementer_config_defaults
):
    pass

class TestStepImplementerContainerImageStaticComplianceScanOpenSCAP__required_config_or_result_keys(
    BaseTestStepImplementerContainerImageStaticComplianceScanOpenSCAP
):
    def test_result(self):
        required_keys = OpenSCAP._required_config_or_result_keys()
        expected_required_keys = [
            'oscap-profile',
            'oscap-input-definitions-uri',
            'container-image-tag',
            'container-image-pull-repository-type',
            ['container-image-pull-repository-type', 'container-image-repository-type']
        ]
        self.assertEqual(required_keys, expected_required_keys)

class TestStepImplementerContainerImageStaticVulnerabilityScanOpenSCAP__validate_required_config_or_previous_step_result_artifact_keys(
    BaseTestStepImplementerContainerImageStaticComplianceScanOpenSCAP,
    tests.step_implementers.shared.test_openscap_generic.TestStepImplementerSharedOpenSCAPGeneric__validate_required_config_or_previous_step_result_artifact_keys
):
    pass

class TestStepImplementerContainerImageStaticComplianceScanOpenSCAP___get_oscap_document_type(
    BaseTestStepImplementerContainerImageStaticComplianceScanOpenSCAP,
    tests.step_implementers.shared.test_openscap_generic.TestStepImplementerSharedOpenSCAPGeneric___get_oscap_document_type
):
    pass

class TestStepImplementerContainerImageStaticComplianceScanOpenSCAP___get_oscap_eval_type_based_on_document_type(
    BaseTestStepImplementerContainerImageStaticComplianceScanOpenSCAP,
    tests.step_implementers.shared.test_openscap_generic.TestStepImplementerSharedOpenSCAPGeneric___get_oscap_eval_type_based_on_document_type
):
    pass

class TestStepImplementerContainerImageStaticComplianceScanOpenSCAP___run_oscap_scan(
    BaseTestStepImplementerContainerImageStaticComplianceScanOpenSCAP,
    tests.step_implementers.shared.test_openscap_generic.TestStepImplementerSharedOpenSCAPGeneric___run_oscap_scan
):
    pass

class TestStepImplementerContainerImageStaticComplianceScanOpenSCAP__run_step(
    BaseTestStepImplementerContainerImageStaticComplianceScanOpenSCAP,
    tests.step_implementers.shared.test_openscap_generic.TestStepImplementerSharedOpenSCAPGeneric__run_step
):
    pass
