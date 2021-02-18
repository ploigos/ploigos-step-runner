import os
import re
from io import IOBase, StringIO
from shutil import copyfile
from unittest.mock import patch

from testfixtures import TempDirectory
from tests.helpers.maven_step_implementer_test_case import \
    MaveStepImplementerTestCase
from tests.helpers.test_utils import Any
from ploigos_step_runner.config.config import Config
from ploigos_step_runner.step_implementers.unit_test import Maven
from ploigos_step_runner.step_result import StepResult
from ploigos_step_runner.utils.file import create_parent_dir
from ploigos_step_runner.workflow_result import WorkflowResult


class TestStepImplementerMavenUnitTest(MaveStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Maven,
            step_config=step_config,
            step_name='unit-test',
            implementer='Maven',
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = Maven.step_implementer_config_defaults()
        expected_defaults = {
            'fail-on-no-tests': True,
            'pom-file': 'pom.xml',
            'tls-verify': True
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Maven._required_config_or_result_keys()
        expected_required_keys = [
            'fail-on-no-tests',
            'pom-file'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def __run__run_step_test(
        self,
        test_dir,
        mvn_mock,
        write_effective_pom_mock,
        generate_maven_settings_mock,
        pom_content,
        group_id,
        artifact_id,
        surefire_reports_dir,
        write_mock_test_results=True,
        assert_mvn_called=True,
        assert_report_artifact=True,
        expected_result_success=True,
        expected_result_message='',
        expected_result_message_regex=None,
        fail_on_no_tests=None,
        raise_error_on_tests=False,
        set_tls_verify_false=False,
    ):
        results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
        results_file_name = 'step-runner-results.yml'
        work_dir_path = os.path.join(test_dir.path, 'working')

        test_dir.write('pom.xml', pom_content)

        pom_file_path = os.path.join(test_dir.path, 'pom.xml')
        step_config = {
            'pom-file': pom_file_path,
            'tls-verify': True
        }

        if set_tls_verify_false:
            step_config['tls-verify'] = False

        if fail_on_no_tests is not None:
            step_config['fail-on-no-tests'] = fail_on_no_tests
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path,
        )

        # mock generating settings
        settings_file_path = "/does/not/matter/settings.xml"
        def generate_maven_settings_side_effect():
            return settings_file_path
        generate_maven_settings_mock.side_effect = generate_maven_settings_side_effect

        # mock effective pom
        def write_effective_pom_mock_side_effect(pom_file_path, output_path):
            create_parent_dir(pom_file_path)
            copyfile(pom_file_path, output_path)
        write_effective_pom_mock.side_effect = write_effective_pom_mock_side_effect

        # mock test results
        if write_mock_test_results:
            mvn_mock.side_effect = MaveStepImplementerTestCase.create_mvn_side_effect(
                pom_file=pom_file_path,
                artifact_parent_dir=surefire_reports_dir,
                artifact_names=[
                    f'{group_id}.{artifact_id}.ClassNameTest.txt',
                    f'TEST-{group_id}.{artifact_id}.ClassNameTest.xml'
                ],
                raise_error_on_tests=raise_error_on_tests
            )

        result = step_implementer._run_step()
        if assert_mvn_called:
            if not set_tls_verify_false:
                mvn_mock.assert_called_once_with(
                    'clean',
                    'test',
                    '-f', pom_file_path,
                    '-s', settings_file_path,
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                )
            else:
                mvn_mock.assert_called_once_with(
                    'clean',
                    'test',
                    '-f', pom_file_path,
                    '-s', settings_file_path,
                    '-Dmaven.wagon.http.ssl.insecure=true',
                    '-Dmaven.wagon.http.ssl.allowall=true',
                    '-Dmaven.wagon.http.ssl.ignore.validity.dates=true',
                    _out=Any(IOBase),
                    _err=Any(IOBase)
                )

        expected_step_result = StepResult(
            step_name='unit-test',
            sub_step_name='Maven',
            sub_step_implementer_name='Maven'
        )
        expected_step_result.success = expected_result_success
        expected_step_result.message = expected_result_message

        if assert_report_artifact:
            mvn_test_output_file_path = os.path.join(
                work_dir_path,
                'unit-test',
                'mvn_test_output.txt'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from 'mvn test'.",
                name='maven-output',
                value=mvn_test_output_file_path
            )
            expected_step_result.add_artifact(
                name='surefire-reports',
                description="Surefire reports generated from 'mvn test'.",
                value=surefire_reports_dir,
            )

        if expected_result_message_regex:
            self.assertEqual(result.success, expected_step_result.success)
            self.assertRegex(result.message, expected_result_message_regex)
            self.assertEqual(result.artifacts, expected_step_result.artifacts)
        else:
            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch.object(Maven, '_generate_maven_settings')
    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
    def test__run_step_success_default_reports_dir(
        self,
        write_effective_pom_mock,
        mvn_mock,
        generate_maven_settings_mock
    ):
        with TempDirectory() as test_dir:
            group_id = 'com.mycompany.app'
            artifact_id = 'my-app'
            version = '1.0'
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            pom_content = bytes(
'''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
xmlns="http://maven.apache.org/POM/4.0.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
            </plugin>
        </plugins>
    </build>
</project>'''.format(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=version
                ), 'utf-8'
            )

            self.__run__run_step_test(
                test_dir=test_dir,
                mvn_mock=mvn_mock,
                write_effective_pom_mock=write_effective_pom_mock,
                generate_maven_settings_mock=generate_maven_settings_mock,
                pom_content=pom_content,
                group_id=group_id,
                artifact_id=artifact_id,
                surefire_reports_dir=surefire_reports_dir,
            )

    @patch.object(Maven, '_generate_maven_settings')
    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
    def test__run_step_tls_verify_false(
        self,
        write_effective_pom_mock,
        mvn_mock,
        generate_maven_settings_mock
    ):
        with TempDirectory() as test_dir:
            group_id = 'com.mycompany.app'
            artifact_id = 'my-app'
            version = '1.0'
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            pom_content = bytes(
'''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
xmlns="http://maven.apache.org/POM/4.0.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
            </plugin>
        </plugins>
    </build>
</project>'''.format(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=version
                ), 'utf-8'
            )

            self.__run__run_step_test(
                test_dir=test_dir,
                mvn_mock=mvn_mock,
                write_effective_pom_mock=write_effective_pom_mock,
                generate_maven_settings_mock=generate_maven_settings_mock,
                pom_content=pom_content,
                group_id=group_id,
                artifact_id=artifact_id,
                surefire_reports_dir=surefire_reports_dir,
                set_tls_verify_false=True
            )

    @patch.object(Maven, '_generate_maven_settings')
    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
    def test__run_step_success_pom_specified_reports_dir(
        self,
        write_effective_pom_mock,
        mvn_mock,
        generate_maven_settings_mock
    ):
        with TempDirectory() as test_dir:
            group_id = 'com.mycompany.app'
            artifact_id = 'my-app'
            version = '1.0'
            surefire_reports_dir = os.path.join(test_dir.path, 'target/custom-surefire-reports-dir')
            pom_content = bytes(
'''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
xmlns="http://maven.apache.org/POM/4.0.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
                <configuration>
                    <reportsDirectory>{surefire_reports_dir}</reportsDirectory>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>'''.format(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=version,
                    surefire_reports_dir=surefire_reports_dir
                ), 'utf-8'
            )

            self.__run__run_step_test(
                test_dir=test_dir,
                mvn_mock=mvn_mock,
                write_effective_pom_mock=write_effective_pom_mock,
                generate_maven_settings_mock=generate_maven_settings_mock,
                pom_content=pom_content,
                group_id=group_id,
                artifact_id=artifact_id,
                surefire_reports_dir=surefire_reports_dir
            )

    @patch.object(Maven, '_generate_maven_settings')
    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
    def test__run_step_fail_missing_surefire_plugin(
        self,
        write_effective_pom_mock,
        mvn_mock,
        generate_maven_settings_mock
    ):
        with TempDirectory() as test_dir:
            group_id = 'com.mycompany.app'
            artifact_id = 'my-app'
            version = '1.0'
            surefire_reports_dir = os.path.join(test_dir.path, 'target/custom-surefire-reports-dir')
            pom_content = bytes(
'''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
xmlns="http://maven.apache.org/POM/4.0.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
        </plugins>
    </build>
</project>'''.format(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=version
                ), 'utf-8'
            )

            effective_pom_path = os.path.join(
                test_dir.path,
                'working',
                'effective-pom.xml'
            )
            self.__run__run_step_test(
                test_dir=test_dir,
                mvn_mock=mvn_mock,
                write_effective_pom_mock=write_effective_pom_mock,
                generate_maven_settings_mock=generate_maven_settings_mock,
                pom_content=pom_content,
                group_id=group_id,
                artifact_id=artifact_id,
                surefire_reports_dir=surefire_reports_dir,
                expected_result_success=False,
                expected_result_message='Unit test dependency "maven-surefire-plugin" ' \
                    f'missing from effective pom ({effective_pom_path}).',
                assert_mvn_called=False,
                assert_report_artifact=False
            )

    @patch.object(Maven, '_generate_maven_settings')
    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
    def test__run_step_fail_no_unit_tests_defined(
        self,
        write_effective_pom_mock,
        mvn_mock,
        generate_maven_settings_mock
    ):
        with TempDirectory() as test_dir:
            group_id = 'com.mycompany.app'
            artifact_id = 'my-app'
            version = '1.0'
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            pom_content = bytes(
'''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
xmlns="http://maven.apache.org/POM/4.0.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
            </plugin>
        </plugins>
    </build>
</project>'''.format(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=version
                ), 'utf-8'
            )

            self.__run__run_step_test(
                test_dir=test_dir,
                mvn_mock=mvn_mock,
                write_effective_pom_mock=write_effective_pom_mock,
                generate_maven_settings_mock=generate_maven_settings_mock,
                pom_content=pom_content,
                group_id=group_id,
                artifact_id=artifact_id,
                surefire_reports_dir=surefire_reports_dir,
                write_mock_test_results=False,
                expected_result_success=False,
                expected_result_message='No unit tests defined.'
            )

    @patch.object(Maven, '_generate_maven_settings')
    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
    def test__run_step_success_fail_on_no_tests_false_and_no_tests(
        self,
        write_effective_pom_mock,
        mvn_mock,
        generate_maven_settings_mock
    ):
        with TempDirectory() as test_dir:
            group_id = 'com.mycompany.app'
            artifact_id = 'my-app'
            version = '1.0'
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            pom_content = bytes(
'''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
xmlns="http://maven.apache.org/POM/4.0.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
            </plugin>
        </plugins>
    </build>
</project>'''.format(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=version
                ), 'utf-8'
            )

            self.__run__run_step_test(
                test_dir=test_dir,
                mvn_mock=mvn_mock,
                write_effective_pom_mock=write_effective_pom_mock,
                generate_maven_settings_mock=generate_maven_settings_mock,
                pom_content=pom_content,
                group_id=group_id,
                artifact_id=artifact_id,
                surefire_reports_dir=surefire_reports_dir,
                write_mock_test_results=False,
                fail_on_no_tests=False,
                expected_result_message="No unit tests defined, but 'fail-on-no-tests' is False."
            )

    @patch.object(Maven, '_generate_maven_settings')
    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
    def test__run_step_fail_mvn_test_failure(
        self,
        write_effective_pom_mock,
        mvn_mock,
        generate_maven_settings_mock
    ):
        with TempDirectory() as test_dir:
            group_id = 'com.mycompany.app'
            artifact_id = 'my-app'
            version = '1.0'
            surefire_reports_dir = os.path.join(test_dir.path, 'target/surefire-reports')
            pom_content = bytes(
'''<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
xmlns="http://maven.apache.org/POM/4.0.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{surefire-plugin.version}}</version>
            </plugin>
        </plugins>
    </build>
</project>'''.format(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=version
                ), 'utf-8'
            )

            self.__run__run_step_test(
                test_dir=test_dir,
                mvn_mock=mvn_mock,
                write_effective_pom_mock=write_effective_pom_mock,
                generate_maven_settings_mock=generate_maven_settings_mock,
                pom_content=pom_content,
                group_id=group_id,
                artifact_id=artifact_id,
                surefire_reports_dir=surefire_reports_dir,
                raise_error_on_tests=True,
                expected_result_success=False,
                expected_result_message_regex=re.compile(
                    r"Unit test failures. See 'maven-output'" \
                    r" and 'surefire-reports' report artifacts for details:"
                    r".*RAN: mvn"
                    r".*STDOUT:"
                    r".*mock out"
                    r".*STDERR:"
                    r".*mock error",
                    re.DOTALL
                )
            )
