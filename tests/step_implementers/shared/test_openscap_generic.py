# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
from contextlib import redirect_stdout
from io import IOBase, StringIO
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any, create_sh_side_effect
from ploigos_step_runner import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared.openscap_generic import OpenSCAPGeneric


class TestStepImplementerSharedOpenSCAPGeneric(BaseStepImplementerTestCase):
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
            step_implementer=OpenSCAPGeneric,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = OpenSCAPGeneric.step_implementer_config_defaults()
        expected_defaults = {
            'oscap-fetch-remote-resources': True
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = OpenSCAPGeneric._required_config_or_result_keys()
        expected_required_keys = [
            'oscap-input-definitions-uri',
            'image-tar-file'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        step_config = {
            'oscap-input-definitions-uri': 'https://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.bz2',
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

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_protocal(self):
        oscap_input_definitions_uri = 'foo://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.bz2'
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
                        r'Open SCAP input definitions source '
                        rf'\({oscap_input_definitions_uri}\) must start with known protocol '
                        r'\(file://\|http://\|https://\)\.'
                    )
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_extension(self):
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.foo'
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
                work_dir_path=work_dir_path,
            )

            with self.assertRaisesRegex(
                AssertionError,
                re.compile(
                    r'Open SCAP input definitions source '
                    rf'\({oscap_input_definitions_uri}\) must be of known type \(xml\|bz2\), got: \.foo'
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
                        r" artifact keys: \['oscap-input-definitions-uri', 'image-tar-file'\]"
                    )
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    @patch('sh.buildah', create=True)
    def test___buildah_import_image_from_tar_success(self, buildah_mock):
        image_tar_file = "/does/not/matter.tar"
        container_name = "test"

        OpenSCAPGeneric._OpenSCAPGeneric__buildah_import_image_from_tar(
            image_tar_file=image_tar_file,
            container_name=container_name
        )

        buildah_mock.assert_called_once_with(
            'from',
            '--storage-driver', 'vfs',
            '--name', container_name,
            f"docker-archive:{image_tar_file}",
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    def test___buildah_import_image_from_tar_error(self, buildah_mock):
        image_tar_file = "/does/not/matter.tar"
        container_name = "test"

        buildah_mock.side_effect = sh.ErrorReturnCode('buildah', b'mock out', b'mock error')

        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    rf"Error importing the image \({image_tar_file}\):"
                    r".*RAN: buildah"
                    r".*STDOUT:"
                    r".*mock out"
                    r".*STDERR:"
                    r".*mock error",
                    re.DOTALL
                )
        ):
            OpenSCAPGeneric._OpenSCAPGeneric__buildah_import_image_from_tar(
                image_tar_file=image_tar_file,
                container_name=container_name
            )

        buildah_mock.assert_called_once_with(
            'from',
            '--storage-driver', 'vfs',
            '--name', container_name,
            f"docker-archive:{image_tar_file}",
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    def test___buildah_mount_container_success(self, buildah_mock):
        buildah_unshare_command = sh.buildah.bake('unshare')
        container_name = "test"

        expected_mount_path = '/this/is/a/path'
        buildah_mock.bake('unshare').bake('buildah', 'mount').side_effect = create_sh_side_effect(
            mock_stdout=f"{expected_mount_path}",
        )

        container_mount_path = OpenSCAPGeneric._OpenSCAPGeneric__buildah_mount_container(
            buildah_unshare_command=buildah_unshare_command,
            container_id=container_name
        )

        self.assertEqual(container_mount_path, expected_mount_path)

        buildah_mock.bake('unshare').bake('buildah', 'mount').assert_called_once_with(
            '--storage-driver', 'vfs',
            container_name,
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    def test___buildah_mount_container_error(self, buildah_mock):
        buildah_unshare_command = sh.buildah.bake('unshare')
        container_name = "test"

        buildah_mock.bake('unshare').bake('buildah', 'mount').side_effect = sh.ErrorReturnCode(
            'buildah mount',
            b'mock out',
            b'mock error'
        )

        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    rf"Error mounting container \({container_name}\):"
                    r".*RAN: buildah"
                    r".*STDOUT:"
                    r".*mock out"
                    r".*STDERR:"
                    r".*mock error",
                    re.DOTALL
                )
        ):
            OpenSCAPGeneric._OpenSCAPGeneric__buildah_mount_container(
                buildah_unshare_command=buildah_unshare_command,
                container_id=container_name
            )

        buildah_mock.bake('unshare').bake('buildah', 'mount').assert_called_once_with(
            '--storage-driver', 'vfs',
            container_name,
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.oscap', create=True)
    def test___get_oscap_document_type_sds(self, oscap_mock):
        oscap_input_file = '/does/not/matter.xml'

        sh.oscap.info.side_effect = create_sh_side_effect(
            mock_stdout="""
Document type: Source Data Stream
Imported: 2020-10-07T05:34:29

Stream: scap_org.open-scap_datastream_from_xccdf_com.redhat.rhsa-all.xml-xccdf12
Generated: (null)
Version: 1.2
Checklists:
	Ref-Id: scap_org.open-scap_cref_com.redhat.rhsa-all.xml-xccdf12
		Status: incomplete
		Resolved: true
		Profiles:
		Referenced check files:
			com.redhat.rhsa-all.xml
				system: http://oval.mitre.org/XMLSchema/oval-definitions-5
Checks:
	Ref-Id: scap_org.open-scap_cref_com.redhat.rhsa-all.xml
No dictionaries."""
        )

        oscap_document_type = OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
            oscap_input_file=oscap_input_file
        )

        sh.oscap.info.assert_called_once_with(
            oscap_input_file,
            _out=Any(IOBase)
        )

        self.assertEqual(oscap_document_type, 'Source Data Stream')

    @patch('sh.oscap', create=True)
    def test___get_oscap_document_type_oval(self, oscap_mock):
        oscap_input_file = '/does/not/matter.xml'

        sh.oscap.info.side_effect = create_sh_side_effect(
            mock_stdout="""
Document type: OVAL Definitions
OVAL version: 5.10
Generated: 2020-10-06T23:36:01
Imported: 2020-10-06T23:36:04"""
        )

        oscap_document_type = OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
            oscap_input_file=oscap_input_file
        )

        oscap_document_type = OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
            oscap_input_file=oscap_input_file
        )

        self.assertEqual(oscap_document_type, 'OVAL Definitions')

    @patch('sh.oscap', create=True)
    def test___get_oscap_document_type_xccdf(self, oscap_mock):
        oscap_input_file = '/does/not/matter.xml'

        sh.oscap.info.side_effect = create_sh_side_effect(
            mock_stdout="""
Document type: XCCDF Checklist
Checklist version: 1.1
Imported: 2020-02-11T13:41:07
Status: draft
Generated: 2020-02-11
Resolved: true
Profiles:
	Title: Protection Profile for General Purpose Operating Systems
		Id: ospp
	Title: PCI-DSS v3.2.1 Control Baseline for Red Hat Enterprise Linux 8
		Id: pci-dss
	Title: [DRAFT] DISA STIG for Red Hat Enterprise Linux 8
		Id: stig
	Title: Australian Cyber Security Centre (ACSC) Essential Eight
		Id: e8
Referenced check files:
	ssg-rhel8-oval.xml
		system: http://oval.mitre.org/XMLSchema/oval-definitions-5
	ssg-rhel8-ocil.xml
		system: http://scap.nist.gov/schema/ocil/2
	https://www.redhat.com/security/data/oval/com.redhat.rhsa-RHEL8.xml
		system: http://oval.mitre.org/XMLSchema/oval-definitions-5"""
        )

        oscap_document_type = OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
            oscap_input_file=oscap_input_file
        )

        sh.oscap.info.assert_called_once_with(
            oscap_input_file,
            _out=Any(IOBase)
        )

        self.assertEqual(oscap_document_type, 'XCCDF Checklist')

    @patch('sh.oscap', create=True)
    def test___get_oscap_document_type_error(self, oscap_mock):
        oscap_input_file = '/does/not/matter.xml'

        sh.oscap.info.side_effect = sh.ErrorReturnCode(
            'oscap info',
            b'mock out',
            b'mock error'
        )

        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error getting document type of oscap"
                    rf" input file \({oscap_input_file}\):"
                    r".*RAN: oscap info"
                    r".*STDOUT:"
                    r".*mock out"
                    r".*STDERR:"
                    r".*mock error",
                    re.DOTALL
                )
        ):
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
                oscap_input_file=oscap_input_file
            )

        sh.oscap.info.assert_called_once_with(
            oscap_input_file,
            _out=Any(IOBase)
        )

    def test___get_oscap_eval_type_based_on_document_type_sds(self):
        oscap_document_type = 'Source Data Stream'

        oscap_eval_type = \
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_eval_type_based_on_document_type(
                oscap_document_type=oscap_document_type
            )

        self.assertEqual(oscap_eval_type, 'xccdf')

    def test___get_oscap_eval_type_based_on_document_type_xccdf(self):
        oscap_document_type = 'XCCDF Checklist'

        oscap_eval_type = \
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_eval_type_based_on_document_type(
                oscap_document_type=oscap_document_type
            )

        self.assertEqual(oscap_eval_type, 'xccdf')

    def test___get_oscap_eval_type_based_on_document_type_oval(self):
        oscap_document_type = 'OVAL Definitions'

        oscap_eval_type = \
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_eval_type_based_on_document_type(
                oscap_document_type=oscap_document_type
            )

        self.assertEqual(oscap_eval_type, 'oval')

    def test___get_oscap_eval_type_based_on_document_type_unknown(self):
        oscap_document_type = 'What is this nonsense?'

        oscap_eval_type = \
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_eval_type_based_on_document_type(
                oscap_document_type=oscap_document_type
            )

        self.assertEqual(oscap_eval_type, None)

    def __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock,
            oscap_eval_type,
            oscap_fetch_remote_resources,
            oscap_stdout,
            oscap_stdout_expected,
            oscap_profile=None,
            oscap_tailoring_file=None,
            oscap_eval_success_expected=True,
            exit_code=0,
            oscap_eval_fails_expected=None
    ):
        with TempDirectory() as temp_dir:
            buildah_unshare_command = sh.buildah.bake('unshare')
            oscap_input_file = '/does/not/matter/input.xml'
            oscap_out_file_path = os.path.join(temp_dir.path, 'out')
            oscap_xml_results_file_path = '/does/not/matter/results.xml'
            oscap_html_report_path = '/does/not/matter/results.html'
            container_mount_path = '/does/not/matter/coutainer_mount'

            exception = None
            if exit_code == 2:
                exception = sh.ErrorReturnCode_2(
                    'oscap-chroot eval',
                    bytes(oscap_stdout, 'utf-8'),
                    bytes(f'mock error - exit code {exit_code}', 'utf-8')
                )
            elif exit_code == 1:
                exception = sh.ErrorReturnCode_1(
                    'oscap-chroot eval',
                    bytes(oscap_stdout, 'utf-8'),
                    bytes(f'mock error - exit code {exit_code}', 'utf-8')
                )
            elif exit_code:
                exception = sh.ErrorReturnCode(
                    'oscap-chroot eval',
                    bytes(oscap_stdout, 'utf-8'),
                    bytes(f'mock error - exit code {exit_code}', 'utf-8')
                )

            buildah_mock.bake('unshare').bake('oscap-chroot').side_effect = create_sh_side_effect(
                mock_stdout=oscap_stdout,
                exception=exception
            )

            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                oscap_eval_success, oscap_eval_fails = OpenSCAPGeneric._OpenSCAPGeneric__run_oscap_scan(
                    buildah_unshare_command=buildah_unshare_command,
                    oscap_eval_type=oscap_eval_type,
                    oscap_input_file=oscap_input_file,
                    oscap_out_file_path=oscap_out_file_path,
                    oscap_xml_results_file_path=oscap_xml_results_file_path,
                    oscap_html_report_path=oscap_html_report_path,
                    container_mount_path=container_mount_path,
                    oscap_profile=oscap_profile,
                    oscap_tailoring_file=oscap_tailoring_file,
                    oscap_fetch_remote_resources=oscap_fetch_remote_resources
                )

            if oscap_profile:
                oscap_profile_flag = f"--profile={oscap_profile}"
            else:
                oscap_profile_flag = None

            if oscap_fetch_remote_resources:
                oscap_fetch_remote_resources_flag = "--fetch-remote-resources"
            else:
                oscap_fetch_remote_resources_flag = None

            if oscap_tailoring_file:
                oscap_tailoring_file_flag = f"--tailoring-file={oscap_tailoring_file}"
            else:
                oscap_tailoring_file_flag = None

            buildah_mock.bake('unshare').bake.assert_called_with('oscap-chroot')
            buildah_mock.bake('unshare').bake('oscap-chroot').assert_called_once_with(
                container_mount_path,
                oscap_eval_type,
                'eval',
                oscap_profile_flag,
                oscap_fetch_remote_resources_flag,
                oscap_tailoring_file_flag,
                f'--results={oscap_xml_results_file_path}',
                f'--report={oscap_html_report_path}',
                oscap_input_file,
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

            self.assertEqual(oscap_eval_success, oscap_eval_success_expected)

            if oscap_eval_fails_expected:
                self.assertEqual(oscap_eval_fails, oscap_eval_fails_expected)

            stdout = stdout_buff.getvalue()
            self.assertEqual(stdout, oscap_stdout_expected)

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_xccdf_do_no_fetch_remote_with_profile_all_pass(self, buildah_mock):
        TestStepImplementerSharedOpenSCAPGeneric. \
            __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=False,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_xccdf_do_yes_fetch_remote_with_profile_all_pass(self, buildah_mock):
        TestStepImplementerSharedOpenSCAPGeneric. \
            __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=True,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_xccdf_do_yes_fetch_remote_no_profile_all_pass(self, buildah_mock):
        TestStepImplementerSharedOpenSCAPGeneric. \
            __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile=None,
            oscap_fetch_remote_resources=True,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_xccdf_do_yes_fetch_remote_with_profile_with_fail(self, buildah_mock):
        TestStepImplementerSharedOpenSCAPGeneric. \
            __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=True,
            oscap_eval_success_expected=False,
            exit_code=2,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	notapplicable

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	fail

Title\r	Ensure gpgcheck Enabled for All yum Package Repositories
Rule\r	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident\r	CCE-80792-5
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	notapplicable

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail

Title	Ensure gpgcheck Enabled for All yum Package Repositories
Rule	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident	CCE-80792-5
Result	pass
""",
            oscap_eval_fails_expected="""
Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail
"""
        )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_str_oscap_fetch_remote_resources_flag(self, buildah_mock):
        TestStepImplementerSharedOpenSCAPGeneric. \
            __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources="True",
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_oval_do_no_fetch_remote_with_profile_all_pass(self, buildah_mock):
        TestStepImplementerSharedOpenSCAPGeneric. \
            __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock=buildah_mock,
            oscap_eval_type='oval',
            oscap_fetch_remote_resources=False,
            oscap_stdout="""
Definition oval:com.redhat.rhsa:def:20203699: false
Definition oval:com.redhat.rhsa:def:20203669: false
Definition oval:com.redhat.rhsa:def:20203665: false
Definition oval:com.redhat.rhsa:def:20203662: false""",
            oscap_stdout_expected="""
Definition oval:com.redhat.rhsa:def:20203699: false
Definition oval:com.redhat.rhsa:def:20203669: false
Definition oval:com.redhat.rhsa:def:20203665: false
Definition oval:com.redhat.rhsa:def:20203662: false
"""
        )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_oval_do_no_fetch_remote_with_profile_all_pass(self, buildah_mock):
        TestStepImplementerSharedOpenSCAPGeneric. \
            __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock=buildah_mock,
            oscap_eval_type='oval',
            oscap_fetch_remote_resources=False,
            oscap_eval_success_expected=False,
            oscap_stdout="""
Definition oval:com.redhat.rhsa:def:20203699: false
Definition oval:com.redhat.rhsa:def:20203669: true
Definition oval:com.redhat.rhsa:def:20203665: false
Definition oval:com.redhat.rhsa:def:20203662: true""",
            oscap_stdout_expected="""
Definition oval:com.redhat.rhsa:def:20203699: false
Definition oval:com.redhat.rhsa:def:20203669: true
Definition oval:com.redhat.rhsa:def:20203665: false
Definition oval:com.redhat.rhsa:def:20203662: true
""",
            oscap_eval_fails_expected="""Definition oval:com.redhat.rhsa:def:20203669: true
Definition oval:com.redhat.rhsa:def:20203662: true
"""
        )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_xccdf_exit_code_1(self, buildah_mock):
        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error running 'oscap xccdf eval':"
                    r".*RAN: oscap-chroot eval"
                    r".*STDOUT:"
                    r".*Title\s*Enable Kernel Page-Table Isolation \(KPTI\)"
                    r"\s*Rule\s*xccdf_org.ssgproject.content_rule_grub2_pti_argument"
                    r"\s*Ident\s*CCE-82194-2"
                    r"\s*Result\s*notapplicable"
                    r".*Title\s*Install dnf-automatic Package"
                    r"\s*Rule\s*xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed"
                    r"\s*Ident\s*CCE-82985-3"
                    r"\s*Result\s*fail"
                    r".*Title\s*Ensure gpgcheck Enabled for All yum Package Repositories"
                    r"\s*Rule\s*xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled"
                    r"\s*Ident\s*CCE-80792-5"
                    r"\s*Result\s*pass"
                    r".*STDERR:"
                    r".*mock error - exit code 1",
                    re.DOTALL
                )
        ):
            TestStepImplementerSharedOpenSCAPGeneric. \
                __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
                self,
                buildah_mock=buildah_mock,
                oscap_eval_type='xccdf',
                oscap_profile='this.is.real.i.sware',
                oscap_fetch_remote_resources=True,
                oscap_eval_success_expected=False,
                exit_code=1,
                oscap_stdout="""
    Title\r	Enable Kernel Page-Table Isolation (KPTI)
    Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
    Ident\r	CCE-82194-2
    Result\r	notapplicable

    Title\r	Install dnf-automatic Package
    Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
    Ident\r	CCE-82985-3
    Result\r	fail

    Title\r	Ensure gpgcheck Enabled for All yum Package Repositories
    Rule\r	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
    Ident\r	CCE-80792-5
    Result\r	pass""",
                oscap_stdout_expected="""
    Title	Enable Kernel Page-Table Isolation (KPTI)
    Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
    Ident	CCE-82194-2
    Result	notapplicable

    Title	Install dnf-automatic Package
    Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
    Ident	CCE-82985-3
    Result	fail

    Title	Ensure gpgcheck Enabled for All yum Package Repositories
    Rule	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
    Ident	CCE-80792-5
    Result	pass
    """
            )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_oval_exit_code_1(self, buildah_mock):
        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error running 'oscap oval eval': "
                    r".*RAN: oscap-chroot eval"
                    r".*STDOUT:"
                    r".*Definition oval:com.redhat.rhsa:def:20203699: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203669: true"
                    r".*Definition oval:com.redhat.rhsa:def:20203665: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203662: true"
                    r".*STDERR:"
                    r".*mock error - exit code 1",
                    re.DOTALL
                )
        ):
            TestStepImplementerSharedOpenSCAPGeneric. \
                __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
                self,
                buildah_mock=buildah_mock,
                oscap_eval_type='oval',
                oscap_fetch_remote_resources=False,
                oscap_eval_success_expected=False,
                exit_code=1,
                oscap_stdout="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true""",
                oscap_stdout_expected="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true
    """
            )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_oval_exit_code_2(self, buildah_mock):
        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error running 'oscap oval eval': "
                    r".*RAN: oscap-chroot eval"
                    r".*STDOUT:"
                    r".*Definition oval:com.redhat.rhsa:def:20203699: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203669: true"
                    r".*Definition oval:com.redhat.rhsa:def:20203665: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203662: true"
                    r".*STDERR:"
                    r".*mock error - exit code 2",
                    re.DOTALL
                )
        ):
            TestStepImplementerSharedOpenSCAPGeneric. \
                __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
                self,
                buildah_mock=buildah_mock,
                oscap_eval_type='oval',
                oscap_fetch_remote_resources=False,
                oscap_eval_success_expected=False,
                exit_code=2,
                oscap_stdout="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true""",
                oscap_stdout_expected="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true
    """
            )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_oval_exit_code_unknown(self, buildah_mock):
        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error running 'oscap oval eval': "
                    r".*RAN: oscap-chroot eval"
                    r".*STDOUT:"
                    r".*Definition oval:com.redhat.rhsa:def:20203699: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203669: true"
                    r".*Definition oval:com.redhat.rhsa:def:20203665: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203662: true"
                    r".*STDERR:"
                    r".*mock error - exit code 42",
                    re.DOTALL
                )
        ):
            TestStepImplementerSharedOpenSCAPGeneric. \
                __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
                self,
                buildah_mock=buildah_mock,
                oscap_eval_type='oval',
                oscap_fetch_remote_resources=False,
                oscap_eval_success_expected=False,
                exit_code=42,
                oscap_stdout="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true""",
                oscap_stdout_expected="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true
    """
            )

    @patch('sh.buildah', create=True)
    def test___run_oscap_scan_xccdf_with_tailoring_file(self, buildah_mock):
        TestStepImplementerSharedOpenSCAPGeneric. \
            __run_test___run_oscap_scan_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=False,
            oscap_tailoring_file="/does/not/matter/tailoring.xccdf.xml",
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__buildah_mount_container')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_run_step_pass(
        self,
        buildah_mock,
        get_oscap_document_type_mock,
        buildah_mount_container_mock,
        run_oscap_scan_mock
    ):
        oscap_document_type = 'Source Data Stream'
        oscap_eval_type = 'xccdf'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo'
        }
        image_tar_file_name = 'my_awesome_app'
        image_tar_file = f'/does/not/matter/{image_tar_file_name}.tar'
        oscap_eval_success = True
        oscap_eval_fails = None

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            artifact_config = {
                'image-tar-file': {'description': '', 'value': image_tar_file}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            buildah_mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails
            ]

            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            expected_results = {
                "test": {
                    "OpenSCAP": {
                        "sub-step-implementer-name": "OpenSCAP",
                        "success": True, "message": "",
                        "artifacts": {
                            "html-report": {"description": "", "value": f"{work_dir_path}/test/oscap-xccdf-report.html"},
                            "xml-report": {"description": "",  "value": f"{work_dir_path}/test/oscap-xccdf-results.xml"},
                            "stdout-report": {"description": "", "value": f"{work_dir_path}/test/oscap-xccdf-out"}}}}
            }
            self.assertEqual(expected_results, step_result.get_step_result_dict())

            stdout = stdout_buff.getvalue()

            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Import image: {image_tar_file}"
                    rf".*Imported image: {image_tar_file}"
                    rf".*Mount container: {image_tar_file_name}\-test\-OpenSCAP.*"
                    rf".*Mounted container \({image_tar_file_name}\-test\-OpenSCAP.*\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}"
                    rf".*Downloaded input definitions to: /.+/working/test/rhel\-8.ds.xml"
                    rf".*Determine OpenSCAP document type of input file: /.+/working/test/rhel\-8\.ds\.xml"
                    rf".*Determined OpenSCAP document type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_document_type}"
                    rf".*Determine OpenSCAP eval type for input file \(/.+/working/test/rhel\-8\.ds\.xml\) of document type: {oscap_document_type}"
                    rf".*Determined OpenSCAP eval type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_eval_type}"
                    rf".*Run oscap scan"
                    rf".*OpenSCAP scan completed with eval success",
                    re.DOTALL
                )
            )

    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__buildah_mount_container')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_run_step_fail(self,
                           buildah_mock,
                           get_oscap_document_type_mock,
                           buildah_mount_container_mock,
                           run_oscap_scan_mock
                           ):
        oscap_document_type = 'Source Data Stream'
        oscap_eval_type = 'xccdf'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo'
        }
        image_tar_file_name = 'my_awesome_app'
        image_tar_file = f'/does/not/matter/{image_tar_file_name}.tar'
        oscap_eval_success = False
        oscap_eval_fails = """
Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail
"""

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            artifact_config = {
                'image-tar-file': {'description': '', 'value': image_tar_file}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            buildah_mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails
            ]
            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            expected_results = {
                "test": {
                    "OpenSCAP": {
                        "sub-step-implementer-name": "OpenSCAP",
                        "success": False,
                        "message": "OSCAP eval found issues:\n\nTitle\tInstall dnf-automatic Package\nRule\txccdf_org.ssgproject.content_rule_package_dnf-automatic_installed\nIdent\tCCE-82985-3\nResult\tfail\n",
                        "artifacts": {
                            "html-report": {"description": "", "value": f"{work_dir_path}/test/oscap-xccdf-report.html"},
                            "xml-report": {"description": "", "value": f"{work_dir_path}/test/oscap-xccdf-results.xml"},
                            "stdout-report": {"description": "", "value": f"{work_dir_path}/test/oscap-xccdf-out"}}}}
            }
            self.assertEqual(expected_results, step_result.get_step_result_dict())

            stdout = stdout_buff.getvalue()

            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Import image: {image_tar_file}"
                    rf".*Imported image: {image_tar_file}"
                    rf".*Mount container: {image_tar_file_name}\-test\-OpenSCAP.*"
                    rf".*Mounted container \({image_tar_file_name}\-test\-OpenSCAP.*\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}"
                    rf".*Downloaded input definitions to: /.+/working/test/rhel\-8.ds.xml"
                    rf".*Determine OpenSCAP document type of input file: /.+/working/test/rhel\-8\.ds\.xml"
                    rf".*Determined OpenSCAP document type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_document_type}"
                    rf".*Determine OpenSCAP eval type for input file \(/.+/working/test/rhel\-8\.ds\.xml\) of document type: {oscap_document_type}"
                    rf".*Determined OpenSCAP eval type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_eval_type}"
                    rf".*Run oscap scan"
                    rf".*OpenSCAP scan completed with eval success: False",
                    re.DOTALL
                )
            )

    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__buildah_mount_container')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_run_step_pass_with_tailoring_file(
        self,
        buildah_mock,
        get_oscap_document_type_mock,
        buildah_mount_container_mock,
        run_oscap_scan_mock
    ):
        oscap_document_type = 'Source Data Stream'
        oscap_eval_type = 'xccdf'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        oscap_tailoring_uri = 'https://raw.githubusercontent.com/ploigos/ploigos-example-oscap-content/main/xccdf_com.redhat.ploigos_profile_example_ubi8-tailoring-xccdf.xml'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-tailoring-uri': oscap_tailoring_uri,
            'oscap-profile': 'foo'
        }
        image_tar_file_name = 'my_awesome_app'
        image_tar_file = f'/does/not/matter/{image_tar_file_name}.tar'
        oscap_eval_success = True
        oscap_eval_fails = None

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            artifact_config = {
                'image-tar-file': {'description': '', 'value': image_tar_file}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            buildah_mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails
            ]

            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                result = step_implementer._run_step()

            expected_results = {
                "test": {
                    "OpenSCAP": {
                        "sub-step-implementer-name": "OpenSCAP",
                        "success": True,
                        "message": "",
                        "artifacts": {
                            "html-report": {"description": "", "value": f"{work_dir_path}/test/oscap-xccdf-report.html"},
                            "xml-report": {"description": "", "value": f"{work_dir_path}/test/oscap-xccdf-results.xml"},
                            "stdout-report": {"description": "", "value": f"{work_dir_path}/test/oscap-xccdf-out"}}}}
            }
            self.assertEqual(expected_results, result.get_step_result_dict())


            stdout = stdout_buff.getvalue()

            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Import image: {image_tar_file}"
                    rf".*Imported image: {image_tar_file}"
                    rf".*Mount container: {image_tar_file_name}\-test\-OpenSCAP.*"
                    rf".*Mounted container \({image_tar_file_name}\-test\-OpenSCAP.*\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}"
                    rf".*Downloaded input definitions to: /.+/working/test/rhel\-8.ds.xml"
                    rf".*Download oscap tailoring file: {oscap_tailoring_uri}"
                    rf".*Download oscap tailoring file to: /.+/working/test/xccdf_com.redhat\.ploigos_profile_example_ubi8\-tailoring\-xccdf\.xml"
                    rf".*Determine OpenSCAP document type of input file: /.+/working/test/rhel\-8\.ds\.xml"
                    rf".*Determined OpenSCAP document type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_document_type}"
                    rf".*Determine OpenSCAP eval type for input file \(/.+/working/test/rhel\-8\.ds\.xml\) of document type: {oscap_document_type}"
                    rf".*Determined OpenSCAP eval type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_eval_type}"
                    rf".*Run oscap scan"
                    rf".*OpenSCAP scan completed with eval success",
                    re.DOTALL
                )
            )

    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.download_and_decompress_source_to_destination')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__buildah_mount_container')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_run_step_fail_downloading_open_scap_input_file(
        self,
        buildah_mock,
        get_oscap_document_type_mock,
        buildah_mount_container_mock,
        run_oscap_scan_mock,
        download_and_decompress_source_to_destination_mock
    ):
        oscap_document_type = 'Source Data Stream'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo'
        }
        image_tar_file_name = 'my_awesome_app'
        image_tar_file = f'/does/not/matter/{image_tar_file_name}.tar'
        oscap_eval_success = True
        oscap_eval_fails = None

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            artifact_config = {
                'image-tar-file': {'description': '', 'value': image_tar_file}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            buildah_mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails
            ]

            mock_error_msg = 'mock error downloading open scap file'
            download_and_decompress_source_to_destination_mock.side_effect = RuntimeError(
                mock_error_msg
            )

            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='test',
                sub_step_name='OpenSCAP',
                sub_step_implementer_name='OpenSCAP'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Error downloading OpenSCAP input file: ' \
                f'{mock_error_msg}'

            self.assertEqual(step_result.get_step_result_dict(), expected_step_result.get_step_result_dict())

            stdout = stdout_buff.getvalue()

            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Import image: {image_tar_file}"
                    rf".*Imported image: {image_tar_file}"
                    rf".*Mount container: {image_tar_file_name}\-test\-OpenSCAP.*"
                    rf".*Mounted container \({image_tar_file_name}\-test\-OpenSCAP.*\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}",
                    re.DOTALL
                )
            )

    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.download_and_decompress_source_to_destination')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__buildah_mount_container')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_run_step_fail_downloading_open_scap_tailoring_file(
        self,
        buildah_mock,
        get_oscap_document_type_mock,
        buildah_mount_container_mock,
        run_oscap_scan_mock,
        download_and_decompress_source_to_destination_mock
    ):
        oscap_document_type = 'Source Data Stream'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        oscap_tailoring_uri = 'https://raw.githubusercontent.com/ploigos/ploigos-example-oscap-content/main/xccdf_com.redhat.ploigos_profile_example_ubi8-tailoring-xccdf.xml'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-tailoring-uri': oscap_tailoring_uri,
            'oscap-profile': 'foo'
        }
        image_tar_file_name = 'my_awesome_app'
        image_tar_file = f'/does/not/matter/{image_tar_file_name}.tar'
        oscap_eval_success = True
        oscap_eval_fails = None

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            artifact_config = {
                'image-tar-file': {'description': '', 'value': image_tar_file}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            buildah_mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails
            ]

            mock_error_msg = 'mock error downloading open scap file'
            download_and_decompress_source_to_destination_mock.side_effect = [
                "foo",
                RuntimeError(mock_error_msg)
            ]

            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='test',
                sub_step_name='OpenSCAP',
                sub_step_implementer_name='OpenSCAP'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Error downloading OpenSCAP tailoring file: ' \
                f'{mock_error_msg}'

            self.assertEqual(step_result.get_step_result_dict(), expected_step_result.get_step_result_dict())

            stdout = stdout_buff.getvalue()

            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Import image: {image_tar_file}"
                    rf".*Imported image: {image_tar_file}"
                    rf".*Mount container: {image_tar_file_name}\-test\-OpenSCAP.*"
                    rf".*Mounted container \({image_tar_file_name}\-test\-OpenSCAP.*\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}",
                    re.DOTALL
                )
            )
