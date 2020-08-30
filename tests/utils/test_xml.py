import os

import unittest
from testfixtures import TempDirectory

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

from tssc.utils.xml import get_xml_element

class TestXMLUtils(BaseTSSCTestCase):
    def test_get_xml_element_from_pom_file(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('pom.xml',b'''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>42.1</version>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            version = get_xml_element(pom_file_path, 'version').text
            artifact_id = get_xml_element(pom_file_path, 'artifactId').text
            group_id = get_xml_element(pom_file_path, 'groupId').text

            assert version == '42.1'
            assert artifact_id == 'my-app'
            assert group_id == 'com.mycompany.app'

    def test_get_xml_element_from_pom_file_with_namespace(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('pom.xml',b'''<?xml version="1.0"?>
    <project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
      xmlns="http://maven.apache.org/POM/4.0.0"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>42.1</version>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            version = get_xml_element(pom_file_path, 'version').text
            artifact_id = get_xml_element(pom_file_path, 'artifactId').text
            group_id = get_xml_element(pom_file_path, 'groupId').text

            assert version == '42.1'
            assert artifact_id == 'my-app'
            assert group_id == 'com.mycompany.app'

    def test_get_xml_element_none_existent_file(self):
        with self.assertRaisesRegex(
                ValueError,
                r"Given xml file does not exist: does_not_exist/pom.xml"):

            get_xml_element("does_not_exist/pom.xml", 'version').text

    def test_get_xml_element_element_does_not_exist(self):
        with TempDirectory() as temp_dir:
            temp_dir.write('pom.xml',b'''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>42.1</version>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            with self.assertRaisesRegex(
                    ValueError,
                    r"Given xml file \(.*\) does not have ./does-not-exist element"):

                get_xml_element(pom_file_path, 'does-not-exist')
