import os
import re

from testfixtures import TempDirectory
from tests.step_implementers.shared.test_openscap_generic import \
    TestStepImplementerSharedOpenSCAPGeneric
from ploigos_step_runner.step_implementers.container_image_static_compliance_scan import \
    OpenSCAP


class TestStepImplementerContainerImageStaticComplianceScanOpenSCAP(TestStepImplementerSharedOpenSCAPGeneric):
    def create_step_implementer(
            self,
            step_config={},
            step_name='test',
            implementer='OpenSCAP',
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=OpenSCAP,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        step_config = {
            'oscap-input-definitions-uri': 'https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml',
            'oscap-profile': 'foo',
            'image-tar-file': 'does-not-matter'
        }

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_extension(self):
        oscap_input_definitions_uri = 'https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml.foo'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo',
            'image-tar-file': 'does-not-matter'
        }

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )

            with self.assertRaisesRegex(
                    AssertionError,
                    re.compile(
                        r'Open SCAP input definitions source '
                        rf'\({oscap_input_definitions_uri}\) must be of known type \(xml\|bz2\), got: \.foo'
                    )
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_protocal(self):
        oscap_input_definitions_uri = 'foo://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo',
            'image-tar-file': 'does-not-matter'
        }

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )

            with self.assertRaisesRegex(
                    AssertionError,
                    re.compile(
                        r'Open SCAP input definitions source '
                        rf'\({oscap_input_definitions_uri}\) must start with known protocol '
                        r'\(file://\|http://\|https://\)\.'
                    )
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_missing_oscap_profile(self):
        oscap_input_definitions_uri = 'https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'image-tar-file': 'does-not-matter'
        }

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )

            with self.assertRaisesRegex(
                    AssertionError,
                    re.compile(
                        r"Missing required step configuration or previous step result"
                        r" artifact keys: \['oscap-profile'\]"
                    )
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_missing_required_keys(self):
        step_config = {}
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )

            with self.assertRaisesRegex(
                    AssertionError,
                    re.compile(
                        r"Missing required step configuration or previous step result"
                        r" artifact keys: \['oscap-profile', 'oscap-input-definitions-uri', 'image-tar-file'\]"
                    )
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()