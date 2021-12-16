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

class TestXMLUtils_get_xml_element_if_present(BaseTestCase):
    def test_gets_element(self):
        """Test getting an xml element."""
        with TempDirectory() as temp_dir:
            file = b'''<baseelement>
                            <child>my-value</child>
                        </baseelement>'''
            temp_dir.write('file.xml', file)
            file_path = path.join(temp_dir.path, 'file.xml')

            actual_value = get_xml_element_if_present(file_path, 'child').text

            self.assertEqual('my-value', actual_value)

    def test_returns_none_for_nonexistent_element(self):
        """Test getting an xml element."""
        with TempDirectory() as temp_dir:
            file = b'''<baseelement>
                            <child>my-value</child>
                        </baseelement>'''
            temp_dir.write('file.xml', file)
            file_path = path.join(temp_dir.path, 'file.xml')

            actual_element = get_xml_element_if_present(file_path, 'not-present')

            self.assertEqual(None, actual_element)

    def test_returns_first_of_two_elements(self):
        """Test getting an xml element."""
        with TempDirectory() as temp_dir:
            file = b'''<baseelement>
                            <child1>value1</child1>
                            <child2>value2</child2>
                        </baseelement>'''
            temp_dir.write('file.xml', file)
            file_path = path.join(temp_dir.path, 'file.xml')

            actual_value = get_xml_element_if_present(file_path, 'child1').text

            self.assertEqual('value1', actual_value)

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
