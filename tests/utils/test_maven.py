"""Test for maven.py

Test for the utility for maven operations.
"""
from testfixtures import TempDirectory
from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tssc.utils.maven import generate_maven_settings


class TestMavenUtils(BaseTSSCTestCase):
    # def test_generate_maven_settings_maven_servers_is_none(self):

    def test_generate_maven_servers_exist(self):
        maven_servers = [
            {
                "id": "one",
                "username": "user1",
                "password": "password1"
            }
        ]

        settings = '''<settings><servers><server><id>one</id><username>user1</username><password>password1</password></server></servers></settings>'''

        with TempDirectory() as temp_dir:
            generate_maven_settings(temp_dir.path, maven_servers, None, None)
            with open(temp_dir.path + '/settings.xml', 'r') as tester:
                results = tester.read()
                assert results == settings

    def test_generate_maven_servers_id_does_not_exist(self):
        maven_servers = [
            {
                "username": "user1",
                "password": "password1"
            }
        ]
        with TempDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, 'id is required for maven_servers.'):
                generate_maven_settings(temp_dir.path, maven_servers, None, None)

    def test_generate_maven_servers_username_does_not_exist(self):
        maven_servers = [
            {
                "id": "one",
                "password": "password1"
            }
        ]
        with TempDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError,
                                        'username and password are required for maven_servers.'):
                generate_maven_settings(temp_dir.path, maven_servers, None, None)

    def test_generate_maven_repositories_exists(self):
        maven_repositories = [
            {
                "id": "repo1",
                "url": "repo_url1",
                "releases": "true",
                "snapshots": "true"
            }
        ]
        settings = '''<settings><profiles><profile><repositories><repository><id>repo1</id><url>repo_url1</url><releases><enabled>true</enabled></releases><snapshots><enabled>true</enabled></snapshots></repository></repositories></profile></profiles></settings>'''

        with TempDirectory() as temp_dir:
            generate_maven_settings(temp_dir.path, None, maven_repositories, None)
            with open(temp_dir.path + '/settings.xml', 'r') as tester:
                results = tester.read()
                assert results == settings

    def test_generate_maven_repositories_id_does_not_exists(self):
        maven_repositories = [
            {
                "url": "repo_url1",
                "releases": "true",
                "snapshots": "true"
            }
        ]
        with TempDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError,
                                        'id and url are required for maven_repositories.'):
                generate_maven_settings(temp_dir.path, None, maven_repositories, None)

    def test_generate_maven_mirrors_exists(self):
        maven_mirrors = [
            {
                "id": "mirror1",
                "url": "mirror_url1",
                "mirror-of": "false"
            }
        ]

        settings = '''<settings><mirrors><mirror><id>mirror1</id><url>mirror_url1</url><mirrorOf>false</mirrorOf></mirror></mirrors></settings>'''

        with TempDirectory() as temp_dir:
            generate_maven_settings(temp_dir.path, None, None, maven_mirrors)
            with open(temp_dir.path + '/settings.xml', 'r') as tester:
                results = tester.read()
                assert results == settings

    def test_generate_maven_mirrors_exists_id_does_not_exists(self):
        maven_mirrors = [
            {
                "url": "mirror_url1",
                "mirror-of": "false"
            }
        ]
        with TempDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError,
                                        'id, url and mirrorOf are required for maven_mirrors.'):
                generate_maven_settings(temp_dir.path, None, None, maven_mirrors)

    def test_generate_maven_params_empty(self):
        settings = '<settings />'

        with TempDirectory() as temp_dir:
            generate_maven_settings(temp_dir.path, None, None, None)
            with open(temp_dir.path + '/settings.xml', 'r') as tester:
                results = tester.read()
                assert results == settings

    def test_generate_maven_mirrors_empty(self):
        settings = '<settings />'

        with TempDirectory() as temp_dir:
            generate_maven_settings(temp_dir.path, None, None, None)
            with open(temp_dir.path + '/settings.xml', 'r') as tester:
                results = tester.read()
                assert results == settings
