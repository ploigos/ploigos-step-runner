import os

import pytest
from testfixtures import TempDirectory

from tssc.step_implementers.utils.xml import get_xml_element

from test_utils import *


def test_get_xml_element_from_pom_file():
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
        
def test_get_xml_element_none_existent_file():

    with pytest.raises(ValueError):
        get_xml_element("does_not_exist/pom.xml", 'version').text