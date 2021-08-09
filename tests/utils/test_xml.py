import os
from os import path
from unittest.mock import Mock, patch

from ploigos_step_runner.utils.xml import *
from testfixtures import TempDirectory
from tests.helpers.base_test_case import BaseTestCase


class TestXMLUtils_other(BaseTestCase):
    """Test for XML Utilities"""
    def test_get_xml_element_from_pom_file(self):
        """Test getting an xml element from the pom file."""
        with TempDirectory() as temp_dir:
            pom = b'''<project>
                        <modelVersion>4.0.0</modelVersion>
                        <groupId>com.mycompany.app</groupId>
                        <artifactId>my-app</artifactId>
                        <version>42.1</version>
                    </project>'''
            temp_dir.write('pom.xml', pom)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')

            version = get_xml_element(pom_file_path, 'version').text
            artifact_id = get_xml_element(pom_file_path, 'artifactId').text
            group_id = get_xml_element(pom_file_path, 'groupId').text

            assert version == '42.1'
            assert artifact_id == 'my-app'
            assert group_id == 'com.mycompany.app'

    def test_get_xml_element_from_pom_file_with_namespace(self):
        """Test get xml element from pom file with namespace."""
        with TempDirectory() as temp_dir:
            pom = b'''<?xml version="1.0"?>
                      <project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
                          xmlns="http://maven.apache.org/POM/4.0.0"
                          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                          <modelVersion>4.0.0</modelVersion>
                          <groupId>com.mycompany.app</groupId>
                          <artifactId>my-app</artifactId>
                          <version>42.1</version>
                      </project>'''

            temp_dir.write('pom.xml', pom)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')

            version = get_xml_element(pom_file_path, 'version').text
            artifact_id = get_xml_element(pom_file_path, 'artifactId').text
            group_id = get_xml_element(pom_file_path, 'groupId').text

            assert version == '42.1'
            assert artifact_id == 'my-app'
            assert group_id == 'com.mycompany.app'

    def test_get_xml_element_none_existent_file(self):
        """Test get xml element but file does not exist."""
        with self.assertRaisesRegex(
                ValueError,
                r"Given xml file does not exist: does_not_exist/pom.xml"):

            # pylint: disable=expression-not-assigned
            get_xml_element('does_not_exist/pom.xml', 'version').text

    def test_get_xml_element_element_does_not_exist(self):
        """Test get xml element but does not exist."""
        with TempDirectory() as temp_dir:
            pom = b'''<project>
                          <modelVersion>4.0.0</modelVersion>
                          <groupId>com.mycompany.app</groupId>
                          <artifactId>my-app</artifactId>
                          <version>42.1</version>
                      </project>'''

            temp_dir.write('pom.xml', pom)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')

            with self.assertRaisesRegex(
                    ValueError,
                    r"Given xml file \(.*\) does not have ./does-not-exist element"):

                get_xml_element(pom_file_path, 'does-not-exist')

    def test_parse_xml_element_for_attributes(self):
        """Test to get an xml attribute from xml element

        """

        sample_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'sample.xml'
        )

        element = 'testsuite'
        attribs = ['time', 'tests']

        results = aggregate_xml_element_attribute_values(sample_file_path, element, attribs)

        expected_results = {'tests': 3, 'time': 4.485}

        self.assertEqual(results, expected_results)

    def test_parse_xml_element_for_attributes_multiple_files(self):
        """Test that element attributes are aggregated if multiple files with same element/attributes exist.

        """

        sample_file_path = os.path.join(
            os.path.dirname(__file__),
            'files/multiple_xml'
        )

        element = 'testsuite'
        attribs = ['time', 'tests','quality']

        results = aggregate_xml_element_attribute_values(sample_file_path, element, attribs)

        expected_results = {'time': 8.97, 'tests': 6, 'quality': ['42', 'medium-rare']}

        self.assertCountEqual(results, expected_results)

    def test_parse_xml_element_for_attributes_element_not_found(self):
        """Test that function returns empty dict if element is not found in file.
        """

        sample_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'sample.xml'
        )

        element = 'testsuite2'
        attribs = ['time', 'tests']

        results = aggregate_xml_element_attribute_values(sample_file_path, element, attribs)

        expected_results = {}

        self.assertEqual(results, expected_results)

    def test_parse_xml_element_for_attributes_some_there_some_missing_attributes(self):
        """Test that function returns empty dict if attribute is not found in element in file.

        Should get the values that are there and ignore the ones that aren't.
        """

        sample_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'sample.xml'
        )

        element = 'testsuite'
        attribs = ['time', 'tests', 'mock1']

        results = aggregate_xml_element_attribute_values(sample_file_path, element, attribs)

        expected_results = {'time': 4.485, 'tests': 3}

        self.assertEqual(results, expected_results)

    def test_parse_xml_element_for_attributes_all_missing_attributes(self):
        """Test that function returns empty dict if attribute is not found in element in file.
        """

        sample_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'sample.xml'
        )

        element = 'testsuite'
        attribs = ['mock1', 'mock2']

        results = aggregate_xml_element_attribute_values(sample_file_path, element, attribs)

        expected_results = {}

        self.assertEqual(results, expected_results)

class TestXMLUtils_get_xml_element_by_path(BaseTestCase):
    def test_none_existent_file(self):
        """Test get xml element by xpath but file does not exist."""
        with self.assertRaisesRegex(
            ValueError,
            r"Given xml file does not exist: does_not_exist/pom.xml"
        ):
            get_xml_element_by_path('does_not_exist/pom.xml', 'build').text

    def test__exists(self):
        """Test to get an xml element where it exists."""
        with TempDirectory() as temp_dir:
            pom = b'''<project
                        xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
                        xmlns="http://maven.apache.org/POM/4.0.0"
                        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <modelVersion>4.0.0</modelVersion>
                        <groupId>com.mycompany.app</groupId>
                        <artifactId>my-app</artifactId>
                        <version>42.1</version>
                        <build>
                            <plugins>
                                <plugin>
                                    <artifactId>maven-surefire-plugin</artifactId>
                                    <configuration>
                                        <reportsDirectory>mycompany-reports-directory</reportsDirectory>
                                    </configuration>
                                </plugin>
                            </plugins>
                        </build>
                    </project>'''

            temp_dir.write('pom.xml', pom)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            element = get_xml_element_by_path(
                pom_file_path,
                'mvn:build/mvn:plugins/mvn:plugin/[mvn:artifactId="maven-surefire-plugin"]/'\
                    'mvn:configuration/mvn:reportsDirectory',
                default_namespace='mvn'
            )

            self.assertEqual(element.text, 'mycompany-reports-directory')

    def test_exists_no_namespaces(self):
        """Test to get an xml element where it exists, but no namespaces exist."""
        with TempDirectory() as temp_dir:
            pom = b'''<project>
                        <modelVersion>4.0.0</modelVersion>
                        <groupId>com.mycompany.app</groupId>
                        <artifactId>my-app</artifactId>
                        <version>42.1</version>
                        <build>
                            <plugins>
                                <plugin>
                                    <artifactId>maven-surefire-plugin</artifactId>
                                    <configuration>
                                        <reportsDirectory>mycompany-reports-directory</reportsDirectory>
                                    </configuration>
                                </plugin>
                            </plugins>
                        </build>
                    </project>'''

            temp_dir.write('pom.xml', pom)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            element = get_xml_element_by_path(
                pom_file_path,
                'build/plugins/plugin/[artifactId="maven-surefire-plugin"]/' \
                    'configuration/reportsDirectory'
            )

            self.assertEqual(element.text, 'mycompany-reports-directory')

    def test_element_not_found(self):
        """Test to get an xml element where it does not exist."""
        with TempDirectory() as temp_dir:
            pom = b'''<project
                        xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
                        xmlns="http://maven.apache.org/POM/4.0.0"
                        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <modelVersion>4.0.0</modelVersion>
                        <groupId>com.mycompany.app</groupId>
                        <artifactId>my-app</artifactId>
                        <version>42.1</version>
                        <build>
                            <plugins>
                                <plugin>
                                    <artifactId>maven-surefire-plugin</artifactId>
                                    <configuration>
                                        <reportsDirectory>mycompany-reports-directory</reportsDirectory>
                                    </configuration>
                                </plugin>
                            </plugins>
                        </build>
                    </project>'''

            temp_dir.write('pom.xml', pom)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            element = get_xml_element_by_path(
                pom_file_path,
                'mvn:this_does_not_exist',
                default_namespace='mvn'
            )

            self.assertIsNone(element)

    def test_element_not_found_no_namespaces(self):
        """Test to get an xml element where it does not exist and no namespaces exist."""
        with TempDirectory() as temp_dir:
            pom = b'''<project>
                        <modelVersion>4.0.0</modelVersion>
                        <groupId>com.mycompany.app</groupId>
                        <artifactId>my-app</artifactId>
                        <version>42.1</version>
                        <build>
                            <plugins>
                                <plugin>
                                    <artifactId>maven-surefire-plugin</artifactId>
                                    <configuration>
                                        <reportsDirectory>mycompany-reports-directory</reportsDirectory>
                                    </configuration>
                                </plugin>
                            </plugins>
                        </build>
                    </project>'''

            temp_dir.write('pom.xml', pom)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            element = get_xml_element_by_path(
                pom_file_path,
                'this-does-not-exist'
            )

            self.assertIsNone(element)

    def test_find_all_single_result(self):
        with TempDirectory() as temp_dir:
            pom = b'''<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
    <version>42.1</version>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${surefire-plugin.version}</version>
                <configuration>
                    <skipTests>true</skipTests>
                </configuration>
                <executions>
                    <execution>
                        <id>unit-tests</id>
                        <phase>test</phase>
                        <goals>
                            <goal>test</goal>
                        </goals>
                        <configuration>
                            <skipTests>${skipTests}</skipTests>
                            <reportsDirectory>${project.build.directory}/surefire-reports-unit-test</reportsDirectory>
                        </configuration>
                    </execution>
                    <execution>
                        <id>unit-tests2</id>
                        <phase>test</phase>
                        <goals>
                            <goal>test</goal>
                        </goals>
                        <configuration>
                            <skipTests>${skipTests}</skipTests>
                            <reportsDirectory>${project.build.directory}/surefire-reports-unit-test2</reportsDirectory>
                        </configuration>
                    </execution>
                    <execution>
                        <id>integration-tests</id>
                        <phase>integration-test</phase>
                        <goals>
                            <goal>test</goal>
                        </goals>
                        <configuration>
                            <skipTests>${skipITs}</skipTests>
                            <reportsDirectory>${project.build.directory}/surefire-reports-uat</reportsDirectory>
                            <systemProperties>
                            <java.util.logging.manager>org.jboss.logmanager.LogManager</java.util.logging.manager>
                            </systemProperties>
                            <includes>
                            <include>**/*IT.*</include>
                            </includes>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>'''

            temp_dir.write('pom.xml', pom)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            elements = get_xml_element_by_path(
                pom_file_path,
                'build/plugins/plugin/[artifactId="maven-surefire-plugin"]/executions/execution/[phase="integration-test"]/configuration/reportsDirectory',
                find_all=True
            )

            self.assertEqual(len(elements), 1)
            self.assertEqual(
                elements[0].text,
                '${project.build.directory}/surefire-reports-uat'
            )

    def test_find_all_multiple_results(self):
        with TempDirectory() as temp_dir:
            pom = b'''<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
    <version>42.1</version>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${surefire-plugin.version}</version>
                <configuration>
                    <skipTests>true</skipTests>
                </configuration>
                <executions>
                    <execution>
                        <id>unit-tests</id>
                        <phase>test</phase>
                        <goals>
                            <goal>test</goal>
                        </goals>
                        <configuration>
                            <skipTests>${skipTests}</skipTests>
                            <reportsDirectory>${project.build.directory}/surefire-reports-unit-test</reportsDirectory>
                        </configuration>
                    </execution>
                    <execution>
                        <id>unit-tests2</id>
                        <phase>test</phase>
                        <goals>
                            <goal>test</goal>
                        </goals>
                        <configuration>
                            <skipTests>${skipTests}</skipTests>
                            <reportsDirectory>${project.build.directory}/surefire-reports-unit-test2</reportsDirectory>
                        </configuration>
                    </execution>
                    <execution>
                        <id>integration-tests</id>
                        <phase>integration-test</phase>
                        <goals>
                            <goal>test</goal>
                        </goals>
                        <configuration>
                            <skipTests>${skipITs}</skipTests>
                            <reportsDirectory>${project.build.directory}/surefire-reports-uat</reportsDirectory>
                            <systemProperties>
                            <java.util.logging.manager>org.jboss.logmanager.LogManager</java.util.logging.manager>
                            </systemProperties>
                            <includes>
                            <include>**/*IT.*</include>
                            </includes>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>'''

            temp_dir.write('pom.xml', pom)
            pom_file_path = path.join(temp_dir.path, 'pom.xml')
            elements = get_xml_element_by_path(
                pom_file_path,
                'build/plugins/plugin/[artifactId="maven-surefire-plugin"]/executions/' \
                    'execution/[phase="test"]/configuration/reportsDirectory',
                find_all=True
            )

            self.assertEqual(len(elements), 2)
            self.assertEqual(
                elements[0].text,
                '${project.build.directory}/surefire-reports-unit-test'
            )
            self.assertEqual(
                elements[1].text,
                '${project.build.directory}/surefire-reports-unit-test2'
            )

@patch('ploigos_step_runner.utils.xml.get_xml_element_by_path')
class TestXMLUtils_get_xml_element_text_by_path(BaseTestCase):
    def test_find_one(self, mock_get_xml_element_by_path):
        # set up mock
        mock_get_xml_element_by_path.return_value = Mock(text='mock element text')

        # run test
        actual_results = get_xml_element_text_by_path(
            xml_file_path='/mock.xml',
            xpath='mock-path',
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=False
        )

        # do verification
        self.assertEqual(actual_results, 'mock element text')
        mock_get_xml_element_by_path.assert_called_once_with(
            xml_file_path='/mock.xml',
            xpath='mock-path',
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=False
        )

    def test_find_multiple(self, mock_get_xml_element_by_path):
        # set up mock
        mock_get_xml_element_by_path.return_value = [
            Mock(text='mock element text 1'),
            Mock(text='mock element text 2')
        ]

        # run test
        actual_results = get_xml_element_text_by_path(
            xml_file_path='/mock.xml',
            xpath='mock-path',
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=True
        )

        # do verification
        self.assertEqual(actual_results, ['mock element text 1', 'mock element text 2'])

        mock_get_xml_element_by_path.assert_called_once_with(
            xml_file_path='/mock.xml',
            xpath='mock-path',
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=True
        )
