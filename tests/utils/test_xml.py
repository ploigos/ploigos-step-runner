"""Test for xml.py

Test for the utility for xml operations.
"""
from os import path
from testfixtures import TempDirectory
from tests.helpers.base_test_case import BaseTestCase
from ploigos_step_runner.utils.xml import get_xml_element, get_xml_element_by_path

# pylint: disable=no-self-use
class TestXMLUtils(BaseTestCase):
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

    def test_get_xml_by_path_element_none_existent_file(self):
        """Test get xml element by xpath but file does not exist."""
        with self.assertRaisesRegex(
                ValueError,
                r"Given xml file does not exist: does_not_exist/pom.xml"):

            # pylint: disable=expression-not-assigned
            get_xml_element_by_path('does_not_exist/pom.xml', 'build').text

    def test_get_xml_element_by_path_exists(self):
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

            assert element.text == 'mycompany-reports-directory'

    def test_get_xml_element_by_path_exists_no_namespaces(self):
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

            assert element.text == 'mycompany-reports-directory'

    def test_get_xml_element_by_path_no_exists(self):
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

            assert element is None

    def test_get_xml_element_by_path_no_exists_no_namespaces(self):
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

            assert element is None
