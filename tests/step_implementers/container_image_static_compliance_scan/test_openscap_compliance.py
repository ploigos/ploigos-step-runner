import re

from tests.step_implementers.shared.test_openscap_generic import \
    TestStepImplementeSharedOpenSCAPGeneric
from tssc.config.config import Config
from tssc.step_implementers.container_image_static_compliance_scan import \
    OpenSCAP


class TestStepImplementeContainerImageStaticVulnerabilityScanOpenSCAP(TestStepImplementeSharedOpenSCAPGeneric):
    def create_step_implementer(
        self,
        step_config={},
        results_dir_path='',
        results_file_name='',
        work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=OpenSCAP,
            step_config=step_config,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test__validate_runtime_step_config_valid(self):
        step_config = {
            'oscap-input-definitions-uri': 'https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml',
            'oscap-profile': 'foo'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        step_implementer._validate_runtime_step_config(step_config)

    def test__validate_runtime_step_config_invalid_extension(self):
        oscap_input_definitions_uri = 'https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml.foo'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        with self.assertRaisesRegex(
            AssertionError,
            re.compile(
                r'Open SCAP input definitions source '
                rf'\({oscap_input_definitions_uri}\) must be of known type \(xml\|bz2\), got: \.foo'
            )
        ):
            step_implementer._validate_runtime_step_config(step_config)

    def test__validate_runtime_step_config_invalid_protocal(self):
        oscap_input_definitions_uri = 'foo://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        with self.assertRaisesRegex(
            AssertionError,
            re.compile(
                r'Open SCAP input definitions source '
                rf'\({oscap_input_definitions_uri}\) must start with known protocol '
                r'\(file://\|http://\|https://\)\.'
            )
        ):
            step_implementer._validate_runtime_step_config(step_config)

    def test__validate_runtime_step_config_missing_oscap_profile(self):
        oscap_input_definitions_uri = 'https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        with self.assertRaisesRegex(
            AssertionError,
            re.compile(
                r"The runtime step configuration \(.*\) is missing the "
                r"required configuration keys \(\['oscap-profile'\]\)"
            )
        ):
            step_implementer._validate_runtime_step_config(step_config)
