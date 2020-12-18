"""Test for maven.py

Test for the utility for maven operations.
"""
import re
import xml.etree.ElementTree as ET
from io import BytesIO
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_test_case import BaseTestCase
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.maven import *


class TestMavenUtils(BaseTestCase):
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
                self.assertEqual(results, settings)

    def test_generate_maven_servers_id_does_not_exist(self):
        maven_servers = [
            {
                "username": "user1",
                "password": "password1"
            }
        ]
        with TempDirectory() as temp_dir:
            with self.assertRaisesRegex(
                AssertionError,
                r"Configuration for maven servers must specify a 'id':"
                r" {'username': 'user1', 'password': 'password1'}"
            ):
                generate_maven_settings(temp_dir.path, maven_servers, None, None)

    def test_generate_maven_servers_username_does_not_exist(self):
        maven_servers = [
            {
                "id": "one",
                "password": "password1"
            }
        ]
        with TempDirectory() as temp_dir:
            with self.assertRaisesRegex(
                AssertionError,
                r"Configuration for maven servers must specify both "
                r"'username' and 'password' or neither: {'id': 'one', 'password': 'password1'}"
            ):
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
                self.assertEqual(results, settings)

    def test_generate_maven_repositories_id_does_not_exists(self):
        maven_repositories = [
            {
                "url": "repo_url1",
                "releases": "true",
                "snapshots": "true"
            }
        ]
        with TempDirectory() as temp_dir:
            with self.assertRaisesRegex(
                AssertionError,
                r"Configuration for maven repository must specify a 'id':"
                r" {'url': 'repo_url1', 'releases': 'true', 'snapshots': 'true'}"
            ):
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
                self.assertEqual(results, settings)

    def test_generate_maven_mirrors_exists_id_does_not_exists(self):
        maven_mirrors = [
            {
                "url": "mirror_url1",
                "mirror-of": "false"
            }
        ]
        with TempDirectory() as temp_dir:
            with self.assertRaisesRegex(
                AssertionError,
                r"Configuration for maven mirror must specify a 'id':"
                r" {'url': 'mirror_url1', 'mirror-of': 'false'}"
            ):
                generate_maven_settings(temp_dir.path, None, None, maven_mirrors)

    def test_generate_maven_params_empty(self):
        settings = '<settings />'

        with TempDirectory() as temp_dir:
            generate_maven_settings(temp_dir.path, None, None, None)
            with open(temp_dir.path + '/settings.xml', 'r') as tester:
                results = tester.read()
                self.assertEqual(results, settings)

    def test_generate_maven_mirrors_empty(self):
        settings = '<settings />'

        with TempDirectory() as temp_dir:
            generate_maven_settings(temp_dir.path, None, None, None)
            with open(temp_dir.path + '/settings.xml', 'r') as tester:
                results = tester.read()
                self.assertEqual(results, settings)

    def test_add_maven_server_no_user_no_pass(self):
        root_element = ET.Element('settings')
        tree = ET.ElementTree(root_element)
        servers_element = ET.Element('servers')
        root_element.append(servers_element)

        add_maven_server(
            parent_element=servers_element,
            maven_server_id='foo'
        )

        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            '<settings><servers><server><id>foo</id></server></servers></settings>'
        )

    def test_add_maven_server_user_and_pass(self):
        root_element = ET.Element('settings')
        tree = ET.ElementTree(root_element)
        servers_element = ET.Element('servers')
        root_element.append(servers_element)

        add_maven_server(
            parent_element=servers_element,
            maven_server_id='foo',
            maven_server_username='test-user',
            maven_server_password='test-pass'
        )

        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            '<settings><servers><server><id>foo</id>'
            '<username>test-user</username>'
            '<password>test-pass</password>'
            '</server></servers></settings>'
        )

    def test_add_maven_server_yes_user_no_pass(self):
        root_element = ET.Element('settings')
        tree = ET.ElementTree(root_element)
        servers_element = ET.Element('servers')
        root_element.append(servers_element)

        add_maven_server(
            parent_element=servers_element,
            maven_server_id='foo',
            maven_server_username='test-user'
        )

        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            '<settings><servers><server><id>foo</id></server></servers></settings>'
        )

    def test_add_maven_server_no_user_yes_pass(self):
        root_element = ET.Element('settings')
        tree = ET.ElementTree(root_element)
        servers_element = ET.Element('servers')
        root_element.append(servers_element)

        add_maven_server(
            parent_element=servers_element,
            maven_server_id='foo',
            maven_server_password='test-pass'
        )

        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            '<settings><servers><server><id>foo</id></server></servers></settings>'
        )

    def test_add_maven_servers_list(self):
        root_element = ET.Element('settings')
        tree = ET.ElementTree(root_element)

        maven_servers = [
            {
                'id': 'id1'
            },
            {
                'id': 'id1',
                'username': 'username1',
                'password': 'password1'
            }
        ]

        add_maven_servers(
            parent_element=root_element,
            maven_servers=maven_servers
        )

        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            '<settings><servers>'
            '<server><id>id1</id></server>'
            '<server><id>id1</id><username>username1</username><password>password1</password></server>'
            '</servers></settings>'
        )

    def test_add_maven_servers_dict_no_ids(self):
        root_element = ET.Element('settings')
        tree = ET.ElementTree(root_element)

        maven_servers = {
            'id-from-key-1': {
                'username': 'username1',
                'password': 'password1'
            },
            'id-from-key-2': {
                'username': 'username2',
                'password': 'password2'
            }
        }

        add_maven_servers(
            parent_element=root_element,
            maven_servers=maven_servers
        )

        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            '<settings><servers>'
            '<server><id>id-from-key-1</id><username>username1</username><password>password1</password></server>'
            '<server><id>id-from-key-2</id><username>username2</username><password>password2</password></server>'
            '</servers></settings>'
        )

    def test_add_maven_servers_dict_with_ids(self):
        root_element = ET.Element('settings')
        tree = ET.ElementTree(root_element)

        maven_servers = {
            'id-from-key-1': {
                'username': 'username1',
                'password': 'password1'
            },
            'id-from-key-2': {
                'id': 'override-id-2',
                'username': 'username2',
                'password': 'password2'
            }
        }

        add_maven_servers(
            parent_element=root_element,
            maven_servers=maven_servers
        )

        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            '<settings><servers>'
            '<server><id>id-from-key-1</id><username>username1</username><password>password1</password></server>'
            '<server><id>override-id-2</id><username>username2</username><password>password2</password></server>'
            '</servers></settings>'
        )

    def test_add_maven_servers_list_missing_pass(self):
        root_element = ET.Element('settings')

        maven_servers = [
            {
                'id': 'invalid',
                'username': 'username1',
            },
            {
                'id': 'valid',
                'username': 'username1',
                'password': 'password1'
            }
        ]

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for maven servers must specify both 'username' and 'password'"
            r" or neither: {'id': 'invalid', 'username': 'username1'}"
        ):
            add_maven_servers(
                parent_element=root_element,
                maven_servers=maven_servers
            )

    def test_add_maven_servers_list_missing_username(self):
        root_element = ET.Element('settings')

        maven_servers = [
            {
                'id': 'invalid',
                'password': 'password1'
            },
            {
                'id': 'valid',
                'username': 'username1',
                'password': 'password1'
            }
        ]

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for maven servers must specify both 'username' and 'password'"
            r" or neither: {'id': 'invalid', 'password': 'password1'}"
        ):
            add_maven_servers(
                parent_element=root_element,
                maven_servers=maven_servers
            )
    def test_add_maven_servers_dict_missing_pass(self):
        root_element = ET.Element('settings')

        maven_servers = {
            'invalid': {
                'username': 'username1',
            },
            'valid': {
                'username': 'username1',
                'password': 'password1'
            }
        }

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for maven server \(invalid\) must specify"
            r" both 'username' and 'password' or neither: {'username': 'username1'}"
        ):
            add_maven_servers(
                parent_element=root_element,
                maven_servers=maven_servers
            )

    def test_add_maven_servers_dict_missing_username(self):
        root_element = ET.Element('settings')

        maven_servers = {
            'invalid': {
                'password': 'password1'
            },
            'valid': {
                'username': 'username1',
                'password': 'password1'
            }
        }

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for maven server \(invalid\) must specify"
            r" both 'username' and 'password' or neither: {'password': 'password1'}"
        ):
            add_maven_servers(
                parent_element=root_element,
                maven_servers=maven_servers
            )

    def test_add_maven_repository_no_release_no_snapshot(self):
        root_element = ET.Element('settings')
        profiles_element = ET.Element('profiles')
        root_element.append(profiles_element)
        profile_element = ET.Element('profile')
        profiles_element.append(profile_element)
        repositories_element = ET.Element('repositories')
        profile_element.append(repositories_element)

        add_maven_repository(
            parent_element=repositories_element,
            repository_id='test-id-1',
            repository_url='test-url'
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles>"
            r"<profile><repositories>"
            r"<repository><id>test-id-1</id><url>test-url</url></repository>"
            r"</repositories></profile>"
            r"</profiles></settings>"
        )

    def test_add_maven_repository_false_release_no_snapshot(self):
        root_element = ET.Element('settings')
        profiles_element = ET.Element('profiles')
        root_element.append(profiles_element)
        profile_element = ET.Element('profile')
        profiles_element.append(profile_element)
        repositories_element = ET.Element('repositories')
        profile_element.append(repositories_element)

        add_maven_repository(
            parent_element=repositories_element,
            repository_id='test-id-1',
            repository_url='test-url',
            releases_enabled=False
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles>"
            r"<profile><repositories>"
            r"<repository><id>test-id-1</id><url>test-url</url><releases><enabled>False</enabled></releases></repository>"
            r"</repositories></profile>"
            r"</profiles></settings>"
        )

    def test_add_maven_repository_true_release_no_snapshot(self):
        root_element = ET.Element('settings')
        profiles_element = ET.Element('profiles')
        root_element.append(profiles_element)
        profile_element = ET.Element('profile')
        profiles_element.append(profile_element)
        repositories_element = ET.Element('repositories')
        profile_element.append(repositories_element)

        add_maven_repository(
            parent_element=repositories_element,
            repository_id='test-id-1',
            repository_url='test-url',
            releases_enabled=True
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles>"
            r"<profile><repositories>"
            r"<repository><id>test-id-1</id><url>test-url</url><releases><enabled>True</enabled></releases></repository>"
            r"</repositories></profile>"
            r"</profiles></settings>"
        )

    def test_add_maven_repository_no_release_false_snapshot(self):
        root_element = ET.Element('settings')
        profiles_element = ET.Element('profiles')
        root_element.append(profiles_element)
        profile_element = ET.Element('profile')
        profiles_element.append(profile_element)
        repositories_element = ET.Element('repositories')
        profile_element.append(repositories_element)

        add_maven_repository(
            parent_element=repositories_element,
            repository_id='test-id-1',
            repository_url='test-url',
            snapshots_enabled=False
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles>"
            r"<profile><repositories>"
            r"<repository><id>test-id-1</id><url>test-url</url><snapshots><enabled>False</enabled></snapshots></repository>"
            r"</repositories></profile>"
            r"</profiles></settings>"
        )

    def test_add_maven_repository_no_release_true_snapshot(self):
        root_element = ET.Element('settings')
        profiles_element = ET.Element('profiles')
        root_element.append(profiles_element)
        profile_element = ET.Element('profile')
        profiles_element.append(profile_element)
        repositories_element = ET.Element('repositories')
        profile_element.append(repositories_element)

        add_maven_repository(
            parent_element=repositories_element,
            repository_id='test-id-1',
            repository_url='test-url',
            snapshots_enabled=True
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles>"
            r"<profile><repositories>"
            r"<repository><id>test-id-1</id><url>test-url</url><snapshots><enabled>True</enabled></snapshots></repository>"
            r"</repositories></profile>"
            r"</profiles></settings>"
        )

    def test_add_maven_repository_False_release_true_snapshot(self):
        root_element = ET.Element('settings')
        profiles_element = ET.Element('profiles')
        root_element.append(profiles_element)
        profile_element = ET.Element('profile')
        profiles_element.append(profile_element)
        repositories_element = ET.Element('repositories')
        profile_element.append(repositories_element)

        add_maven_repository(
            parent_element=repositories_element,
            repository_id='test-id-1',
            repository_url='test-url',
            releases_enabled=False,
            snapshots_enabled=True
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles>"
            r"<profile><repositories>"
            r"<repository><id>test-id-1</id><url>test-url</url>"
            r"<releases><enabled>False</enabled></releases>"
            r"<snapshots><enabled>True</enabled></snapshots></repository>"
            r"</repositories></profile>"
            r"</profiles></settings>"
        )

    def test_add_maven_repository_true_release_true_snapshot(self):
        root_element = ET.Element('settings')
        profiles_element = ET.Element('profiles')
        root_element.append(profiles_element)
        profile_element = ET.Element('profile')
        profiles_element.append(profile_element)
        repositories_element = ET.Element('repositories')
        profile_element.append(repositories_element)

        add_maven_repository(
            parent_element=repositories_element,
            repository_id='test-id-1',
            repository_url='test-url',
            releases_enabled=True,
            snapshots_enabled=True
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles>"
            r"<profile><repositories>"
            r"<repository><id>test-id-1</id><url>test-url</url>"
            r"<releases><enabled>True</enabled></releases>"
            r"<snapshots><enabled>True</enabled></snapshots></repository>"
            r"</repositories></profile>"
            r"</profiles></settings>"
        )

    def test_add_maven_servers_list(self):
        root_element = ET.Element('settings')

        maven_repositories = [
            {
                'id': 'server-id-1',
                'url': 'url-1'
            },
            {
                'id': 'server-id-2',
                'url': 'url-2'
            }
        ]

        add_maven_repositories(
            parent_element=root_element,
            maven_repositories=maven_repositories
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles><profile><repositories>"
            r"<repository><id>server-id-1</id><url>url-1</url></repository>"
            r"<repository><id>server-id-2</id><url>url-2</url></repository>"
            r"</repositories></profile></profiles></settings>"
        )

    def test_add_maven_servers_dict_with_id_elements(self):
        root_element = ET.Element('settings')

        maven_repositories = {
            'ignore-me-1': {
                'id': 'server-id-1',
                'url': 'url-1'
            },
            'ingnore-me-2': {
                'id': 'server-id-2',
                'url': 'url-2'
            }
        }

        add_maven_repositories(
            parent_element=root_element,
            maven_repositories=maven_repositories
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles><profile><repositories>"
            r"<repository><id>server-id-1</id><url>url-1</url></repository>"
            r"<repository><id>server-id-2</id><url>url-2</url></repository>"
            r"</repositories></profile></profiles></settings>"
        )

    def test_add_maven_servers_dict_no_id_elements(self):
        root_element = ET.Element('settings')

        maven_repositories = {
            'use-me-1': {
                'url': 'url-1'
            },
            'ingnore-me-2': {
                'id': 'server-id-2',
                'url': 'url-2'
            }
        }

        add_maven_repositories(
            parent_element=root_element,
            maven_repositories=maven_repositories
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><profiles><profile><repositories>"
            r"<repository><id>use-me-1</id><url>url-1</url></repository>"
            r"<repository><id>server-id-2</id><url>url-2</url></repository>"
            r"</repositories></profile></profiles></settings>"
        )

    def test_add_maven_mirror_valid(self):
        root_element = ET.Element('settings')
        mirrors_element = ET.Element('mirrors')
        root_element.append(mirrors_element)

        add_maven_mirror(
            parent_element=mirrors_element,
            maven_mirror_id='test-id-1',
            maven_mirror_url='test-url-1',
            maven_mirror_mirror_of='test-mirror-of-1'
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><mirrors>"
            r"<mirror>"
            r"<id>test-id-1</id>"
            r"<url>test-url-1</url>"
            r"<mirrorOf>test-mirror-of-1</mirrorOf>"
            r"</mirror>"
            r"</mirrors></settings>"
        )

    def test_add_maven_mirrors_list_valid(self):
        root_element = ET.Element('settings')

        maven_mirrors = [
            {
                'id': 'test-id-1',
                'url': 'test-url-1',
                'mirror-of': 'test-mirror-of-1'
            },
            {
                'id': 'test-id-2',
                'url': 'test-url-2',
                'mirror-of': 'test-mirror-of-2'
            }
        ]

        add_maven_mirrors(
            parent_element=root_element,
            maven_mirrors=maven_mirrors
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><mirrors>"
            r"<mirror>"
            r"<id>test-id-1</id>"
            r"<url>test-url-1</url>"
            r"<mirrorOf>test-mirror-of-1</mirrorOf>"
            r"</mirror>"
            r"<mirror>"
            r"<id>test-id-2</id>"
            r"<url>test-url-2</url>"
            r"<mirrorOf>test-mirror-of-2</mirrorOf>"
            r"</mirror>"
            r"</mirrors></settings>"
        )

    def test_add_maven_mirrors_dict_with_ids(self):
        root_element = ET.Element('settings')

        maven_mirrors = {
            'ignore-me-1': {
                'id': 'test-id-1',
                'url': 'test-url-1',
                'mirror-of': 'test-mirror-of-1'
            },
            'ignore-me-2': {
                'id': 'test-id-2',
                'url': 'test-url-2',
                'mirror-of': 'test-mirror-of-2'
            }
        }

        add_maven_mirrors(
            parent_element=root_element,
            maven_mirrors=maven_mirrors
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><mirrors>"
            r"<mirror>"
            r"<id>test-id-1</id>"
            r"<url>test-url-1</url>"
            r"<mirrorOf>test-mirror-of-1</mirrorOf>"
            r"</mirror>"
            r"<mirror>"
            r"<id>test-id-2</id>"
            r"<url>test-url-2</url>"
            r"<mirrorOf>test-mirror-of-2</mirrorOf>"
            r"</mirror>"
            r"</mirrors></settings>"
        )

    def test_add_maven_mirrors_dict_without_id(self):
        root_element = ET.Element('settings')

        maven_mirrors = {
            'use-me-1': {
                'url': 'test-url-1',
                'mirror-of': 'test-mirror-of-1'
            },
            'ignore-me-2': {
                'id': 'test-id-2',
                'url': 'test-url-2',
                'mirror-of': 'test-mirror-of-2'
            }
        }

        add_maven_mirrors(
            parent_element=root_element,
            maven_mirrors=maven_mirrors
        )

        tree = ET.ElementTree(root_element)
        tree_write_out = BytesIO()
        tree.write(tree_write_out)

        self.assertEqual(
            tree_write_out.getvalue().decode(),
            r"<settings><mirrors>"
            r"<mirror>"
            r"<id>use-me-1</id>"
            r"<url>test-url-1</url>"
            r"<mirrorOf>test-mirror-of-1</mirrorOf>"
            r"</mirror>"
            r"<mirror>"
            r"<id>test-id-2</id>"
            r"<url>test-url-2</url>"
            r"<mirrorOf>test-mirror-of-2</mirrorOf>"
            r"</mirror>"
            r"</mirrors></settings>"
        )

    def test_add_maven_mirrors_list_missing_id(self):
        root_element = ET.Element('settings')

        maven_mirrors = [
            {
                'url': 'test-url-1',
                'mirror-of': 'test-mirror-of-1'
            }
        ]

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for maven mirror must specify a 'id':"
            r" {'url': 'test-url-1', 'mirror-of': 'test-mirror-of-1'}"
        ):
            add_maven_mirrors(
                parent_element=root_element,
                maven_mirrors=maven_mirrors
            )

    def test_add_maven_mirrors_list_missing_url(self):
        root_element = ET.Element('settings')

        maven_mirrors = [
            {
                'id': 'test-id-1',
                'mirror-of': 'test-mirror-of-1'
            }
        ]

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for maven mirror must specify a 'url':"
            r" {'id': 'test-id-1', 'mirror-of': 'test-mirror-of-1'}"
        ):
            add_maven_mirrors(
                parent_element=root_element,
                maven_mirrors=maven_mirrors
            )

    def test_add_maven_mirrors_list_missing_mirror_of(self):
        root_element = ET.Element('settings')

        maven_mirrors = [
            {
                'id': 'test-id-1',
                'url': 'test-url-1'
            }
        ]

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for maven mirror must specify"
            r" a 'mirror-of': {'id': 'test-id-1', 'url': 'test-url-1'}"
        ):
            add_maven_mirrors(
                parent_element=root_element,
                maven_mirrors=maven_mirrors
            )

    def test_add_maven_mirrors_dict_missing_url(self):
        root_element = ET.Element('settings')

        maven_mirrors = {
            'ignore-me-1': {
                'id': 'test-id-1',
                'mirror-of': 'test-mirror-of-1'
            }
        }

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for maven mirror \(ignore-me-1\) must specify a 'url':"
            r" {'id': 'test-id-1', 'mirror-of': 'test-mirror-of-1'}"
        ):
            add_maven_mirrors(
                parent_element=root_element,
                maven_mirrors=maven_mirrors
            )

    def test_add_maven_mirrors_dict_missing_mirror_of(self):
        root_element = ET.Element('settings')

        maven_mirrors = {
            'ignore-me-1': {
                'id': 'test-id-1',
                'url': 'test-url-1'
            }
        }

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for maven mirror \(ignore-me-1\) must specify a 'mirror-of':"
            r" {'id': 'test-id-1', 'url': 'test-url-1'}"
        ):
            add_maven_mirrors(
                parent_element=root_element,
                maven_mirrors=maven_mirrors
            )

    @patch('sh.mvn', create=True)
    def test_write_effective_pom_success(self, mvn_mock):
        pom_file_path = 'input/pom.xml'
        effective_pom_path = 'output/effective-pom.xml'

        actual_effective_pom_path = write_effective_pom(
            pom_file_path=pom_file_path,
            output_path=effective_pom_path
        )
        self.assertEqual(actual_effective_pom_path, effective_pom_path)
        mvn_mock.assert_any_call(
            'help:effective-pom',
            f'-f={pom_file_path}',
            f'-Doutput={effective_pom_path}'
        )

    @patch('sh.mvn', create=True)
    def test_write_effective_pom_fail(self, mvn_mock):
        pom_file_path = 'input/pom.xml'
        effective_pom_path = 'output/effective-pom.xml'

        mvn_mock.side_effect = sh.ErrorReturnCode('mvn', b'mock stdout', b'mock error')

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Error generating effective pom for '{pom_file_path}' to '{effective_pom_path}'"
                r".*RAN: mvn"
                r".*STDOUT:"
                r".*mock stdout"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            )
        ):
            write_effective_pom(
                pom_file_path=pom_file_path,
                output_path=effective_pom_path
            )
            mvn_mock.assert_any_call(
                'help:effective-pom',
                f'-f={pom_file_path}',
                f'-Doutput={effective_pom_path}'
            )
