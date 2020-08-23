import os
import sys
import sh

import unittest
from unittest.mock import patch, MagicMock
from testfixtures import TempDirectory
import yaml

from tssc import TSSCFactory
from tssc.step_implementers.container_image_static_compliance_scan import OpenSCAP
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from test_utils import *

class TestStepImplementerContainerImageStaticComplianceScan(BaseTSSCTestCase):


    def test_container_image_static_compliance_scan_specify_openscap_implementer_missing_config_scap_input_file(self):
        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'ref-app-quarkus',
                        'service-name': 'backend',
                        'organization': 'tssc-team'
                    },
                    'container-image-static-compliance-scan': {
                        'implementer': 'OpenSCAP',
                        'config': {
                           'destination-url': 'quay-quay-enterprise.apps.tssc.rht-set.com',
                           'log-level': 'info'
                        }
                    }
                }
            }
            with self.assertRaisesRegex(
                    AssertionError,
                    r"The runtime step configuration \(.*\) is missing the required configuration keys \(\['scap-input-file'\]\)"):
                run_step_test_with_result_validation(temp_dir, 'container-image-static-compliance-scan', config, {})




    @patch('sh.buildah', create=True)
    def test_container_image_static_compliance_scan_specify_openscap_implementer_with_existing_vfs_containers (self, buildah_mock):

        image_tag = 'not_latest'
        git_tag = 'git_tag'
        image_url = 'quay.io/tssc/myimage'
        image_location = 'quay-quay-enterprise.apps.tssc.rht-set.com/tssc-team/ref-app-quarkus-backend:1.0.0-feature_napsspo-999'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    f'''tssc-results:
                  generate-metadata:
                    image-tag: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    image-tag: {image_location}
                ''',
                'utf-8')
                )

            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'ref-app-quarkus',
                        'service-name': 'backend',
                        'organization': 'tssc-team'
                    },
                    'container-image-static-compliance-scan': {
                        'implementer': 'OpenSCAP',
                        'config': {
                           'destination-url': 'quay-quay-enterprise.apps.tssc.rht-set.com',
                           'log-level': 'info',
                           'scap-input-file': '/usr/share/xml/scap/ssg/content/ssg-jre-oval.xml',
                           'scan-output-absolute-path': '/tmp/scap_output.txt',
                           'scan-report-absolute-path': '/tmp/scap_compliance_report.html'
                        }
                    }
                }
            }

            result1 = MagicMock()
            result1.stdout='\n\n\n'

            result2 = ''

            result3 = MagicMock()
            result3.stdout='containerid'

            result4 = MagicMock()
            result4.stderr='stderr'
            result4.stdout='mount path'
            result4.returncode=123

            buildah_mock.side_effect = [result1,
                                        result2,
                                        result3,
                                        result4]

            with self.assertRaisesRegex(
                    ValueError,
                    r"Zero vfs base containers should be running"):
                run_step_test_with_result_validation(temp_dir, 'container-image-static-compliance-scan', config, {})

            buildah_mock.assert_called

    @patch('sh.buildah', create=True)
    def test_container_image_static_compliance_scan_specify_openscap_implementer_buildah_error(self, buildah_mock):

        git_tag = 'git_tag'
        image_url = 'quay.io/tssc/myimage'
        image_location = 'quay-quay-enterprise.apps.tssc.rht-set.com/tssc-team/ref-app-quarkus-backend:1.0.0-feature_napsspo-999'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    f'''tssc-results:
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    image-tag: {image_location}
                ''',
                'utf-8')
                )

            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'ref-app-quarkus',
                        'service-name': 'backend',
                        'organization': 'tssc-team'
                    },
                    'container-image-static-compliance-scan': {
                        'implementer': 'OpenSCAP',
                        'config': {
                           'destination-url': 'quay-quay-enterprise.apps.tssc.rht-set.com',
                           'log-level': 'info',
                           'scap-input-file': '/usr/share/xml/scap/ssg/content/ssg-jre-oval.xml',
                           'scan-output-absolute-path': '/tmp/scap_output.txt',
                           'scan-report-absolute-path': '/tmp/scap_compliance_report.html'
                        }
                    }
                }
            }

            result1 = MagicMock()
            result1.stdout="test"
            buildah_mock.side_effect = [result1, sh.ErrorReturnCode('buildah', b'stdout', b'stderror')]

            with self.assertRaisesRegex(
                    RuntimeError,
                    r"Unexpected runtime error"):
                run_step_test_with_result_validation(temp_dir, 'container-image-static-compliance-scan', config, {})


    @patch('sh.oscap_chroot', create=True)
    @patch('sh.buildah', create=True)
    def test_container_image_static_compliance_scan_specify_openscap_implementer_no_version(self, buildah_mock, oscap_mock):

        git_tag = 'git_tag'
        image_url = 'quay.io/tssc/myimage'
        image_location = 'quay-quay-enterprise.apps.tssc.rht-set.com/tssc-team/ref-app-quarkus-backend:1.0.0-feature_napsspo-999'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    f'''tssc-results:
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    image-tag: {image_location}
                ''',
                'utf-8')
                )

            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'ref-app-quarkus',
                        'service-name': 'backend',
                        'organization': 'tssc-team'
                    },
                    'container-image-static-compliance-scan': {
                        'implementer': 'OpenSCAP',
                        'config': {
                           'destination-url': 'quay-quay-enterprise.apps.tssc.rht-set.com',
                           'log-level': 'info',
                           'scap-input-file': '/usr/share/xml/scap/ssg/content/ssg-jre-oval.xml',
                           'scan-output-absolute-path': '/tmp/scap_output.txt',
                           'scan-report-absolute-path': '/tmp/scap_compliance_report.html'
                        }
                    }
                }
            }

            result1 = MagicMock()
            result1.stdout='no containers'

            result2 = ''

            result3 = MagicMock()
            result3.stdout='containerid'

            result4 = MagicMock()
            result4.stderr='stderr'
            result4.stdout='mount path'
            result4.returncode=123

            buildah_mock.side_effect = [result1,
                                        result2,
                                        result3,
                                        result4]

            oscap_result = MagicMock()
            oscap_result.stdout = 'report\nresults\n'
            oscap_mock.side_effect = [oscap_result]

            expected_step_results =  {'tssc-results': {'container-image-static-compliance-scan': {'report-artifacts': [{'name': 'container-image-static-compliance-scan '
                                                                                           'result '
                                                                                           'set',
                                                                                   'path': f'file://{temp_dir.path}/tssc-working/container-image-static-compliance-scan/scap-compliance-report.html'}],
                                                             'result': {'message': 'container-image-static-compliance-scan '
                                                                                   'step '
                                                                                   'completed',
                                                                        'success': True}},
                    'push-container-image' : {'image-tag': f'{image_location}'},
                  'tag-source': {'tag': 'git_tag'}} }

            run_step_test_with_result_validation(temp_dir, 'container-image-static-compliance-scan', config, expected_step_results)

            buildah_mock.assert_called
            oscap_mock.assert_called


    @patch('sh.oscap_chroot', create=True)
    @patch('sh.buildah', create=True)
    def test_container_image_static_compliance_scan_specify_openscap_implementer_no_image_to_scan(self, buildah_mock, oscap_mock):

        git_tag = 'git_tag'
        image_url = 'quay.io/tssc/myimage'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    f'''tssc-results:
                  tag-source:
                    tag: {git_tag}
                ''',
                'utf-8')
                )

            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'ref-app-quarkus',
                        'service-name': 'backend',
                        'organization': 'tssc-team'
                    },
                    'container-image-static-compliance-scan': {
                        'implementer': 'OpenSCAP',
                        'config': {
                           'destination-url': 'quay-quay-enterprise.apps.tssc.rht-set.com',
                           'log-level': 'info',
                           'scap-input-file': '/usr/share/xml/scap/ssg/content/ssg-jre-oval.xml',
                           'scan-output-absolute-path': '/tmp/scap_output.txt',
                           'scan-report-absolute-path': '/tmp/scap_compliance_report.html'
                        }
                    }
                }
            }

            result1 = MagicMock()
            result1.stdout='no containers'

            result2 = ''

            result3 = MagicMock()
            result3.stdout='containerid'

            result4 = MagicMock()
            result4.stderr='stderr'
            result4.stdout='mount path'
            result4.returncode=123

            buildah_mock.side_effect = [result1,
                                        result2,
                                        result3,
                                        result4]

            oscap_result = MagicMock()
            oscap_result.stdout = 'report\nresults\n'
            oscap_mock.side_effect = [oscap_result]

            with self.assertRaisesRegex(
                    ValueError,
                    r"Unable to find image to scan from push-container-image"):
                run_step_test_with_result_validation(temp_dir, 'container-image-static-compliance-scan', config, {})

    @patch('sh.oscap_chroot', create=True)
    @patch('sh.buildah', create=True)
    def test_container_image_static_compliance_scan_specify_openscap_implementer_happy_path(self, buildah_mock, oscap_mock):

        image_tag = 'not_latest'
        git_tag = 'git_tag'
        image_location = 'quay-quay-enterprise.apps.tssc.rht-set.com/tssc-team/ref-app-quarkus-backend:1.0.0-feature_napsspo-999'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    f'''tssc-results:
                  generate-metadata:
                    image-tag: {image_tag}
                  push-container-image:
                    image-tag: {image_location}
                  tag-source:
                    tag: {git_tag}
                ''',
                'utf-8')
                )

            config = {
                'tssc-config': {
                    'global-defaults': {
                        'application-name': 'ref-app-quarkus',
                        'service-name': 'backend',
                        'organization': 'tssc-team'
                    },
                    'container-image-static-compliance-scan': {
                        'implementer': 'OpenSCAP',
                        'config': {
                           'log-level': 'info',
                           'scap-input-file': '/usr/share/xml/scap/ssg/content/ssg-jre-oval.xml',
                           'scan-output-absolute-path': '/tmp/scap_output.txt',
                           'scan-report-absolute-path': '/tmp/scap_compliance_report.html'
                        }
                    }
                }
            }

            result1 = MagicMock()
            result1.stdout='no containers'

            result2 = ''

            result3 = MagicMock()
            result3.stdout='containerid'

            result4 = MagicMock()
            result4.stderr='stderr'
            result4.stdout='mount path'
            result4.returncode=123

            buildah_mock.side_effect = [result1,
                                        result2,
                                        result3,
                                        result4]

            oscap_result = MagicMock()
            oscap_result.stdout = 'report\nresults\n'
            oscap_mock.side_effect = [oscap_result]
            expected_step_results =  {'tssc-results': {'container-image-static-compliance-scan': {'report-artifacts': [{'name': 'container-image-static-compliance-scan '
                                                                                           'result '
                                                                                           'set',
                                                                                   'path': f'file://{temp_dir.path}/tssc-working/container-image-static-compliance-scan/scap-compliance-report.html'}],
                                                             'result': {'message': 'container-image-static-compliance-scan '
                                                                                   'step '
                                                                                   'completed',
                                                                        'success': True}},
                    'generate-metadata': {'image-tag': 'not_latest'},
                    'push-container-image' : {'image-tag': f'{image_location}'},
                  'tag-source': {'tag': 'git_tag'}} }

            run_step_test_with_result_validation(temp_dir, 'container-image-static-compliance-scan', config, expected_step_results)

            buildah_mock.assert_called
            oscap_mock.assert_called