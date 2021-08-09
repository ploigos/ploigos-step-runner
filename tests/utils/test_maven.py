"""Test for maven.py

Test for the utility for maven operations.
"""
import re
import xml.etree.ElementTree as ET
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import call, mock_open, patch

import sh
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.maven import *
from testfixtures import TempDirectory
from tests.helpers.base_test_case import BaseTestCase
from tests.helpers.test_utils import Any


class TestMavenUtils_other(BaseTestCase):
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
class TestMavenUtils_write_effective_pom(BaseTestCase):
    def test_success(self, mvn_mock):
        pom_file_path = 'input/pom.xml'
        effective_pom_path = '/tmp/output/effective-pom.xml'

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

    def test_with_one_profile_string(self, mvn_mock):
        pom_file_path = 'input/pom.xml'
        effective_pom_path = '/tmp/output/effective-pom.xml'

        actual_effective_pom_path = write_effective_pom(
            pom_file_path=pom_file_path,
            output_path=effective_pom_path,
            profiles='mock-profile1'
        )
        self.assertEqual(actual_effective_pom_path, effective_pom_path)
        mvn_mock.assert_any_call(
            'help:effective-pom',
            f'-f={pom_file_path}',
            f'-Doutput={effective_pom_path}',
            '-P', 'mock-profile1'
        )

    def test_with_one_profile_list(self, mvn_mock):
        pom_file_path = 'input/pom.xml'
        effective_pom_path = '/tmp/output/effective-pom.xml'

        actual_effective_pom_path = write_effective_pom(
            pom_file_path=pom_file_path,
            output_path=effective_pom_path,
            profiles=['mock-profile1']
        )
        self.assertEqual(actual_effective_pom_path, effective_pom_path)
        mvn_mock.assert_any_call(
            'help:effective-pom',
            f'-f={pom_file_path}',
            f'-Doutput={effective_pom_path}',
            '-P', 'mock-profile1'
        )

    def test_with_mutliple_profiles(self, mvn_mock):
        pom_file_path = 'input/pom.xml'
        effective_pom_path = '/tmp/output/effective-pom.xml'

        actual_effective_pom_path = write_effective_pom(
            pom_file_path=pom_file_path,
            output_path=effective_pom_path,
            profiles=['mock-profile1', 'mock-profile2']
        )
        self.assertEqual(actual_effective_pom_path, effective_pom_path)
        mvn_mock.assert_any_call(
            'help:effective-pom',
            f'-f={pom_file_path}',
            f'-Doutput={effective_pom_path}',
            '-P', 'mock-profile1,mock-profile2'
        )

    def test_fail(self, mvn_mock):
        pom_file_path = 'input/pom.xml'
        effective_pom_path = '/tmp/output/effective-pom.xml'

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

    def test_fail_not_absolute_path(self, mvn_mock):
        pom_file_path = 'input/pom.xml'
        effective_pom_path = 'output/effective-pom.xml'

        mvn_mock.side_effect = sh.ErrorReturnCode('mvn', b'mock stdout', b'mock error')

        with self.assertRaisesRegex(
            StepRunnerException,
            re.compile(
                rf"Given output path \({effective_pom_path}\) is not absolute which will mean "
                rf"your output file will actually end up being relative to the pom file "
                rf"\({pom_file_path}\) rather than your expected root. Rather then handling this, "
                rf"just give this function an absolute path. "
                rf"If you are a user seeing this, a programmer messed up somewhere, "
                rf"report an issue.",
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

@patch('ploigos_step_runner.utils.maven.write_effective_pom')
class TestMavenUtils_get_effective_pom(BaseTestCase):
    def test_does_call_once(self, mock_write_effective_pom):
        with TempDirectory() as temp_dir:
            # set up mock
            def mock_write_effective_pom_side_effect(pom_file_path, output_path, profiles):
                Path(output_path).touch()
            mock_write_effective_pom.side_effect = mock_write_effective_pom_side_effect

            # run test
            effective_pom = get_effective_pom(
                work_dir_path=temp_dir.path,
                pom_file='mock-pom.xml',
                profiles=None
            )

            # validate
            expected_effective_pom = os.path.join(temp_dir.path, 'effective-pom.xml')
            self.assertEqual(effective_pom, expected_effective_pom)
            mock_write_effective_pom.assert_called_once_with(
                pom_file_path='mock-pom.xml',
                output_path=expected_effective_pom,
                profiles=None
            )

    def test_does_call_twice(self, mock_write_effective_pom):
        with TempDirectory() as temp_dir:
            # set up mock
            def mock_write_effective_pom_side_effect(pom_file_path, output_path, profiles):
                Path(output_path).touch()
            mock_write_effective_pom.side_effect = mock_write_effective_pom_side_effect

            # run test (first call)
            effective_pom = get_effective_pom(
                work_dir_path=temp_dir.path,
                pom_file='mock-pom.xml',
                profiles=None
            )

            # validate
            expected_effective_pom = os.path.join(temp_dir.path, 'effective-pom.xml')
            self.assertEqual(effective_pom, expected_effective_pom)
            mock_write_effective_pom.assert_called_once_with(
                pom_file_path='mock-pom.xml',
                output_path=expected_effective_pom,
                profiles=None
            )

            # run test (second call)
            mock_write_effective_pom.reset_mock()
            effective_pom = get_effective_pom(
                work_dir_path=temp_dir.path,
                pom_file='mock-pom.xml',
                profiles=None
            )

            # validate
            expected_effective_pom = os.path.join(temp_dir.path, 'effective-pom.xml')
            self.assertEqual(effective_pom, expected_effective_pom)
            mock_write_effective_pom.assert_not_called()

class TestMavenUtils_get_maven_plugin_xml_element_path(BaseTestCase):
    def test_given_plugin_name(self):
        actual_xml_element_path = get_maven_plugin_xml_element_path('maven-surefire-plugin')
        self.assertEqual(
            actual_xml_element_path,
            './mvn:build/mvn:plugins/mvn:plugin[mvn:artifactId="maven-surefire-plugin"]'
        )

class TestMavenUtils_run_maven(BaseTestCase):
    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.utils.maven.create_sh_redirect_to_multiple_streams_fn_callback')
    @patch("builtins.open", new_callable=mock_open)
    def test_success_defaults(self, mock_open, redirect_mock, mvn_mock):
        with TempDirectory() as temp_dir:
            mvn_output_file_path = os.path.join(temp_dir.path, 'maven_output.txt')
            settings_file = '/fake/settings.xml'
            pom_file = '/fake/pom.xml'
            phases_and_goals = 'fake'

            run_maven(
                mvn_output_file_path=mvn_output_file_path,
                settings_file=settings_file,
                pom_file=pom_file,
                phases_and_goals=phases_and_goals,
            )

            mock_open.assert_called_with(mvn_output_file_path, 'w', encoding='utf-8')
            redirect_mock.assert_has_calls([
                call([
                    sys.stdout,
                    mock_open.return_value
                ]),
                call([
                    sys.stderr,
                    mock_open.return_value
                ])
            ])

            mvn_mock.assert_called_once_with(
                'fake',
                '-f', '/fake/pom.xml',
                '-s', '/fake/settings.xml',
                '--no-transfer-progress',
                _out=Any(StringIO),
                _err=Any(StringIO)
            )

    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.utils.maven.create_sh_redirect_to_multiple_streams_fn_callback')
    @patch("builtins.open", new_callable=mock_open)
    def test_success_with_single_profile(self, mock_open, redirect_mock, mvn_mock):
        with TempDirectory() as temp_dir:
            mvn_output_file_path = os.path.join(temp_dir.path, 'maven_output.txt')
            settings_file = '/fake/settings.xml'
            pom_file = '/fake/pom.xml'
            phases_and_goals = 'fake'

            run_maven(
                mvn_output_file_path=mvn_output_file_path,
                settings_file=settings_file,
                pom_file=pom_file,
                phases_and_goals=phases_and_goals,
                profiles=['fake-profile']
            )

            mock_open.assert_called_with(mvn_output_file_path, 'w', encoding='utf-8')
            redirect_mock.assert_has_calls([
                call([
                    sys.stdout,
                    mock_open.return_value
                ]),
                call([
                    sys.stderr,
                    mock_open.return_value
                ])
            ])

            mvn_mock.assert_called_once_with(
                'fake',
                '-f', '/fake/pom.xml',
                '-s', '/fake/settings.xml',
                '-P', 'fake-profile',
                '--no-transfer-progress',
                _out=Any(StringIO),
                _err=Any(StringIO)
            )

    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.utils.maven.create_sh_redirect_to_multiple_streams_fn_callback')
    @patch("builtins.open", new_callable=mock_open)
    def test_success_with_multiple_profile(self, mock_open, redirect_mock, mvn_mock):
        with TempDirectory() as temp_dir:
            mvn_output_file_path = os.path.join(temp_dir.path, 'maven_output.txt')
            settings_file = '/fake/settings.xml'
            pom_file = '/fake/pom.xml'
            phases_and_goals = 'fake'

            run_maven(
                mvn_output_file_path=mvn_output_file_path,
                settings_file=settings_file,
                pom_file=pom_file,
                phases_and_goals=phases_and_goals,
                profiles=['fake-profile1', 'fake-profile2']
            )

            mock_open.assert_called_with(mvn_output_file_path, 'w', encoding='utf-8')
            redirect_mock.assert_has_calls([
                call([
                    sys.stdout,
                    mock_open.return_value
                ]),
                call([
                    sys.stderr,
                    mock_open.return_value
                ])
            ])

            mvn_mock.assert_called_once_with(
                'fake',
                '-f', '/fake/pom.xml',
                '-s', '/fake/settings.xml',
                '-P', 'fake-profile1,fake-profile2',
                '--no-transfer-progress',
                _out=Any(StringIO),
                _err=Any(StringIO)
            )

    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.utils.maven.create_sh_redirect_to_multiple_streams_fn_callback')
    @patch("builtins.open", new_callable=mock_open)
    def test_success_with_no_tls(self, mock_open, redirect_mock, mvn_mock):
        with TempDirectory() as temp_dir:
            mvn_output_file_path = os.path.join(temp_dir.path, 'maven_output.txt')
            settings_file = '/fake/settings.xml'
            pom_file = '/fake/pom.xml'
            phases_and_goals = 'fake'

            run_maven(
                mvn_output_file_path=mvn_output_file_path,
                settings_file=settings_file,
                pom_file=pom_file,
                phases_and_goals=phases_and_goals,
                tls_verify=False
            )

            mock_open.assert_called_with(mvn_output_file_path, 'w', encoding='utf-8')
            redirect_mock.assert_has_calls([
                call([
                    sys.stdout,
                    mock_open.return_value
                ]),
                call([
                    sys.stderr,
                    mock_open.return_value
                ])
            ])

            mvn_mock.assert_called_once_with(
                'fake',
                '-f', '/fake/pom.xml',
                '-s', '/fake/settings.xml',
                '--no-transfer-progress',
                '-Dmaven.wagon.http.ssl.insecure=true',
                '-Dmaven.wagon.http.ssl.allowall=true',
                '-Dmaven.wagon.http.ssl.ignore.validity.dates=true',
                _out=Any(StringIO),
                _err=Any(StringIO)
            )

    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.utils.maven.create_sh_redirect_to_multiple_streams_fn_callback')
    @patch("builtins.open", new_callable=mock_open)
    def test_success_transfer_progress(self, mock_open, redirect_mock, mvn_mock):
        with TempDirectory() as temp_dir:
            mvn_output_file_path = os.path.join(temp_dir.path, 'maven_output.txt')
            settings_file = '/fake/settings.xml'
            pom_file = '/fake/pom.xml'
            phases_and_goals = 'fake'

            run_maven(
                mvn_output_file_path=mvn_output_file_path,
                settings_file=settings_file,
                pom_file=pom_file,
                phases_and_goals=phases_and_goals,
                no_transfer_progress=False
            )

            mock_open.assert_called_with(mvn_output_file_path, 'w', encoding='utf-8')
            redirect_mock.assert_has_calls([
                call([
                    sys.stdout,
                    mock_open.return_value
                ]),
                call([
                    sys.stderr,
                    mock_open.return_value
                ])
            ])

            mvn_mock.assert_called_once_with(
                'fake',
                '-f', '/fake/pom.xml',
                '-s', '/fake/settings.xml',
                None,
                _out=Any(StringIO),
                _err=Any(StringIO)
            )

    @patch('sh.mvn', create=True)
    @patch('ploigos_step_runner.utils.maven.create_sh_redirect_to_multiple_streams_fn_callback')
    @patch("builtins.open", new_callable=mock_open)
    def test_success_failure(self, mock_open, redirect_mock, mvn_mock):
        with TempDirectory() as temp_dir:
            mvn_output_file_path = os.path.join(temp_dir.path, 'maven_output.txt')
            settings_file = '/fake/settings.xml'
            pom_file = '/fake/pom.xml'
            phases_and_goals = 'fake'

            mvn_mock.side_effect = sh.ErrorReturnCode('mvn', b'mock stdout', b'mock error')

            with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error running maven."
                    r".*RAN: mvn"
                    r".*STDOUT:"
                    r".*mock stdout"
                    r".*STDERR:"
                    r".*mock error",
                    re.DOTALL
                )
            ):
                run_maven(
                    mvn_output_file_path=mvn_output_file_path,
                    settings_file=settings_file,
                    pom_file=pom_file,
                    phases_and_goals=phases_and_goals,
                )

                mock_open.assert_called_with(mvn_output_file_path, 'w', encoding='utf-8')
                redirect_mock.assert_has_calls([
                    call([
                        sys.stdout,
                        mock_open.return_value
                    ]),
                    call([
                        sys.stderr,
                        mock_open.return_value
                    ])
                ])

                mvn_mock.assert_called_once_with(
                    'fake',
                    '-f', '/fake/pom.xml',
                    '-s', '/fake/settings.xml',
                    '--no-transfer-progress',
                    _out=Any(StringIO),
                    _err=Any(StringIO)
                )

@patch('ploigos_step_runner.utils.maven.get_xml_element_text_by_path')
@patch('ploigos_step_runner.utils.maven.get_xml_element_by_path')
@patch('ploigos_step_runner.utils.maven.get_maven_plugin_xml_element_path')
@patch('ploigos_step_runner.utils.maven.get_effective_pom')
class TestMavenUtils_get_plugin_configuration_values(BaseTestCase):
    def test_no_profiles_no_phases(
        self,
        mock_get_effective_pom,
        mock_get_maven_plugin_xml_element_path,
        mock_get_xml_element_by_path,
        mock_get_xml_element_text_by_path
    ):
        # set up mocks
        mock_get_xml_element_text_by_path.return_value = ['mock-config-value-1']

        # run test
        actual_values = get_plugin_configuration_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=None
        )

        # validate
        self.assertEqual(actual_values, ['mock-config-value-1'])
        mock_get_xml_element_text_by_path.assert_called_once()
        mock_get_effective_pom.assert_called_once_with(
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None
        )

    def test_with_profile_no_phases(
        self,
        mock_get_effective_pom,
        mock_get_maven_plugin_xml_element_path,
        mock_get_xml_element_by_path,
        mock_get_xml_element_text_by_path
    ):
        # set up mocks
        mock_get_xml_element_text_by_path.return_value = ['mock-config-value-1']

        # run test
        actual_values = get_plugin_configuration_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=['mock-profile'],
            phases_and_goals=None
        )

        # validate
        self.assertEqual(actual_values, ['mock-config-value-1'])
        mock_get_xml_element_text_by_path.assert_called_once()
        mock_get_effective_pom.assert_called_once_with(
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=['mock-profile']
        )

    def test_with_no_profiles_one_phase_with_one_matching_config(
        self,
        mock_get_effective_pom,
        mock_get_maven_plugin_xml_element_path,
        mock_get_xml_element_by_path,
        mock_get_xml_element_text_by_path
    ):
        mock_phases_with_values = ['mock-test-phase']

        # set up mocks
        def mock_get_xml_element_text_by_path_side_effect(
            xml_file_path,
            xpath,
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=False
        ):
            for mock_phase in mock_phases_with_values:
                if f'[mvn:phase="{mock_phase}"]' in xpath:
                    return [f'{mock_phase}-mock-config-value']

        mock_get_xml_element_text_by_path.side_effect = mock_get_xml_element_text_by_path_side_effect

        # run test
        actual_values = get_plugin_configuration_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=['mock-test-phase']
        )

        # validate
        self.assertEqual(actual_values, ['mock-test-phase-mock-config-value'])
        self.assertEqual(mock_get_xml_element_text_by_path.call_count, 2)
        mock_get_effective_pom.assert_called_once_with(
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None
        )

    def test_with_no_profiles_one_phase_with_multiple_matching_config(
        self,
        mock_get_effective_pom,
        mock_get_maven_plugin_xml_element_path,
        mock_get_xml_element_by_path,
        mock_get_xml_element_text_by_path
    ):
        mock_phases_with_values = ['mock-test-phase']

        # set up mocks
        def mock_get_xml_element_text_by_path_side_effect(
            xml_file_path,
            xpath,
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=False
        ):
            for mock_phase in mock_phases_with_values:
                if f'[mvn:phase="{mock_phase}"]' in xpath:
                    return [f'{mock_phase}-mock-config-value-1', f'{mock_phase}-mock-config-value-2']

        mock_get_xml_element_text_by_path.side_effect = mock_get_xml_element_text_by_path_side_effect

        # run test
        actual_values = get_plugin_configuration_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=['mock-test-phase']
        )

        # validate
        self.assertEqual(
            actual_values,
            ['mock-test-phase-mock-config-value-1', 'mock-test-phase-mock-config-value-2']
        )
        self.assertEqual(mock_get_xml_element_text_by_path.call_count, 2)
        mock_get_effective_pom.assert_called_once_with(
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None
        )

    def test_with_no_profiles_multiple_phases_each_with_one_matching_config(
        self,
        mock_get_effective_pom,
        mock_get_maven_plugin_xml_element_path,
        mock_get_xml_element_by_path,
        mock_get_xml_element_text_by_path
    ):
        mock_phases_with_values = ['mock-test-phase-1', 'mock-test-phase-2']

        # set up mocks
        def mock_get_xml_element_text_by_path_side_effect(
            xml_file_path,
            xpath,
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=False
        ):
            for mock_phase in mock_phases_with_values:
                if f'[mvn:phase="{mock_phase}"]' in xpath:
                    return [f'{mock_phase}-mock-config-value']

        mock_get_xml_element_text_by_path.side_effect = mock_get_xml_element_text_by_path_side_effect

        # run test
        actual_values = get_plugin_configuration_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=['mock-test-phase-1', 'mock-test-phase-2']
        )

        # validate
        self.assertEqual(
            actual_values,
            ['mock-test-phase-1-mock-config-value', 'mock-test-phase-2-mock-config-value']
        )
        self.assertEqual(mock_get_xml_element_text_by_path.call_count, 4)
        mock_get_effective_pom.assert_called_once_with(
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None
        )

    def test_with_no_profiles_multiple_phases_each_with_multiple_matching_config(
        self,
        mock_get_effective_pom,
        mock_get_maven_plugin_xml_element_path,
        mock_get_xml_element_by_path,
        mock_get_xml_element_text_by_path
    ):
        mock_phases_with_values = ['mock-test-phase-1', 'mock-test-phase-2']

        # set up mocks
        def mock_get_xml_element_text_by_path_side_effect(
            xml_file_path,
            xpath,
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=False
        ):
            for mock_phase in mock_phases_with_values:
                if f'[mvn:phase="{mock_phase}"]' in xpath:
                    return [f'{mock_phase}-mock-config-value-1', f'{mock_phase}-mock-config-value-2']

        mock_get_xml_element_text_by_path.side_effect = mock_get_xml_element_text_by_path_side_effect

        # run test
        actual_values = get_plugin_configuration_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=['mock-test-phase-1', 'mock-test-phase-2']
        )

        # validate
        self.assertEqual(
            actual_values,
            [
                'mock-test-phase-1-mock-config-value-1',
                'mock-test-phase-1-mock-config-value-2',
                'mock-test-phase-2-mock-config-value-1',
                'mock-test-phase-2-mock-config-value-2'
            ]
        )
        self.assertEqual(mock_get_xml_element_text_by_path.call_count, 4)
        mock_get_effective_pom.assert_called_once_with(
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None
        )

    def test_with_no_profiles_multiple_phases_no_matching_config(
        self,
        mock_get_effective_pom,
        mock_get_maven_plugin_xml_element_path,
        mock_get_xml_element_by_path,
        mock_get_xml_element_text_by_path
    ):
        # set up mocks
        mock_phases_without_values = ['mock-test-phase-1', 'mock-test-phase-2']
        def mock_get_xml_element_text_by_path_side_effect(
            xml_file_path,
            xpath,
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=False
        ):
            for mock_phase in mock_phases_without_values:
                if f'[mvn:phase="{mock_phase}"]' in xpath:
                    return []

            return ['mock-default-value']

        mock_get_xml_element_text_by_path.side_effect = mock_get_xml_element_text_by_path_side_effect

        # run test
        actual_values = get_plugin_configuration_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=['mock-test-phase-1', 'mock-test-phase-2']
        )

        # validate
        self.assertEqual(
            actual_values,
            ['mock-default-value']
        )
        self.assertEqual(mock_get_xml_element_text_by_path.call_count, 4)
        mock_get_effective_pom.assert_called_once_with(
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None
        )

    def test_plugin_not_found(
        self,
        mock_get_effective_pom,
        mock_get_maven_plugin_xml_element_path,
        mock_get_xml_element_by_path,
        mock_get_xml_element_text_by_path
    ):
        # set up mocks
        mock_get_xml_element_by_path.return_value = None

        # run test
        with self.assertRaisesRegex(
            RuntimeError,
            r"Expected maven plugin \(mock-maven-plugin\) not found in "
            r" effective pom for given pom \(mock-pom.xml\)."
        ):
            get_plugin_configuration_values(
                plugin_name='mock-maven-plugin',
                configuration_key='mockAwesomeConfig',
                work_dir_path='/mock/work_dir',
                pom_file='mock-pom.xml',
                profiles=None,
                phases_and_goals=['mock-test-phase-1', 'mock-test-phase-2']
            )

        # validate
        mock_get_effective_pom.assert_called_once_with(
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None
        )
        mock_get_xml_element_text_by_path.assert_not_called()

    def test_with_no_profiles_one_goal_with_one_matching_config(
        self,
        mock_get_effective_pom,
        mock_get_maven_plugin_xml_element_path,
        mock_get_xml_element_by_path,
        mock_get_xml_element_text_by_path
    ):
        mock_goals_with_values = ['mock-test-goal']

        # set up mocks
        def mock_get_xml_element_text_by_path_side_effect(
            xml_file_path,
            xpath,
            default_namespace=None,
            xml_namespace_dict=None,
            find_all=False
        ):
            for mock_goal in mock_goals_with_values:
                if f'[mvn:goal="{mock_goal}"]' in xpath:
                    return [f'{mock_goal}-mock-config-value']

        mock_get_xml_element_text_by_path.side_effect = mock_get_xml_element_text_by_path_side_effect

        # run test
        actual_values = get_plugin_configuration_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=['mock-test-goal']
        )

        # validate
        self.assertEqual(actual_values, ['mock-test-goal-mock-config-value'])
        self.assertEqual(mock_get_xml_element_text_by_path.call_count, 2)
        mock_get_effective_pom.assert_called_once_with(
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None
        )
# Integration Test with XML, primarly for testing xpaths
# NOTE: isn't full integration test because mocking the effective pom so don't have to have
#       maven installed.
@patch('ploigos_step_runner.utils.maven.get_effective_pom')
class TestMavenUtils_get_plugin_configuration_values_IT_XML(BaseTestCase):

    def __get_test_file_path(self, file):
        return os.path.join(
            os.path.dirname(__file__),
            'files',
            'get_plugin_configuration_values_IT',
            file
        )

    def test_no_profiles_no_phases_no_config_surefire(self, get_effective_pom_mock):
        # setup
        pom_file = self.__get_test_file_path('pom-no-plugin-config.xml')
        get_effective_pom_mock.return_value = pom_file

        with TempDirectory() as temp_dir:
            # run test
            actual_values = get_plugin_configuration_values(
                plugin_name='maven-surefire-plugin',
                configuration_key='reportsDirectory',
                work_dir_path=temp_dir.path,
                pom_file=pom_file,
                profiles=None,
                phases_and_goals=None
            )

            # validate
            self.assertEqual(actual_values, [])

    def test_no_profiles_no_phases_no_config_failsafe(self, get_effective_pom_mock):
        # setup
        pom_file = self.__get_test_file_path('pom-no-plugin-config.xml')
        get_effective_pom_mock.return_value = pom_file

        with TempDirectory() as temp_dir:
            # run test
            actual_values = get_plugin_configuration_values(
                plugin_name='maven-failsafe-plugin',
                configuration_key='reportsDirectory',
                work_dir_path=temp_dir.path,
                pom_file=pom_file,
                profiles=None,
                phases_and_goals=None
            )

            # validate
            self.assertEqual(actual_values, [])

    def test_no_profiles_no_phases_with_config_surefire(self, get_effective_pom_mock):
        # setup
        pom_file = self.__get_test_file_path('pom-plugin-config.xml')
        get_effective_pom_mock.return_value = pom_file

        with TempDirectory() as temp_dir:
            # run test
            actual_values = get_plugin_configuration_values(
                plugin_name='maven-surefire-plugin',
                configuration_key='reportsDirectory',
                work_dir_path=temp_dir.path,
                pom_file=pom_file,
                profiles=None,
                phases_and_goals=None
            )

            # validate
            self.assertEqual(
                actual_values,
                ['${project.build.directory}/surefire-reports-unit-test']
            )

    def test_no_profiles_no_phases_with_config_failsafe(self, get_effective_pom_mock):
        # setup
        pom_file = self.__get_test_file_path('pom-plugin-config.xml')
        get_effective_pom_mock.return_value = pom_file

        with TempDirectory() as temp_dir:
            # run test
            actual_values = get_plugin_configuration_values(
                plugin_name='maven-failsafe-plugin',
                configuration_key='reportsDirectory',
                work_dir_path=temp_dir.path,
                pom_file=pom_file,
                profiles=None,
                phases_and_goals=None
            )

            # validate
            self.assertEqual(
                actual_values,
                ['${project.build.directory}/failsafe-reports-integration-test']
            )

    def test_no_profiles_surefire_both_UT_and_IT_via_phase_get_UT_config(self, get_effective_pom_mock):
        # setup
        pom_file = self.__get_test_file_path('pom-plugin-phase-config.xml')
        get_effective_pom_mock.return_value = pom_file

        with TempDirectory() as temp_dir:
            # run test
            actual_values = get_plugin_configuration_values(
                plugin_name='maven-surefire-plugin',
                configuration_key='reportsDirectory',
                work_dir_path=temp_dir.path,
                pom_file=pom_file,
                profiles=None,
                phases_and_goals=None
            )

            # validate
            self.assertEqual(
                actual_values,
                ['${project.build.directory}/surefire-reports-unit-test']
            )

    def test_no_profiles_surefire_both_UT_and_IT_via_phase_get_IT_config(self, get_effective_pom_mock):
        # setup
        pom_file = self.__get_test_file_path('pom-plugin-phase-config.xml')
        get_effective_pom_mock.return_value = pom_file

        with TempDirectory() as temp_dir:
            # run test
            actual_values = get_plugin_configuration_values(
                plugin_name='maven-surefire-plugin',
                configuration_key='reportsDirectory',
                work_dir_path=temp_dir.path,
                pom_file=pom_file,
                profiles=None,
                phases_and_goals=['integration-test']
            )

            # validate
            self.assertEqual(
                actual_values,
                ['${project.build.directory}/surefire-reports-uat']
            )

    def test_failsafe_with_default_and_goal_execution_config_specify_no_goal(self, get_effective_pom_mock):
        # setup
        pom_file = self.__get_test_file_path('pom-plugin-goal-config.xml')
        get_effective_pom_mock.return_value = pom_file

        with TempDirectory() as temp_dir:
            # run test
            actual_values = get_plugin_configuration_values(
                plugin_name='maven-failsafe-plugin',
                configuration_key='reportsDirectory',
                work_dir_path=temp_dir.path,
                pom_file=pom_file,
                profiles=None,
                phases_and_goals=[]
            )

            # validate
            self.assertEqual(
                actual_values,
                ['${project.build.directory}/failsafe-reports-default']
            )

    def test_failsafe_with_default_and_goal_execution_config_specify_goal(self, get_effective_pom_mock):
        # setup
        pom_file = self.__get_test_file_path('pom-plugin-goal-config.xml')
        get_effective_pom_mock.return_value = pom_file

        with TempDirectory() as temp_dir:
            # run test
            actual_values = get_plugin_configuration_values(
                plugin_name='maven-failsafe-plugin',
                configuration_key='reportsDirectory',
                work_dir_path=temp_dir.path,
                pom_file=pom_file,
                profiles=None,
                phases_and_goals=['integration-test']
            )

            # validate
            self.assertEqual(
                actual_values,
                ['${project.build.directory}/failsafe-reports-execution']
            )

# Integration Test with XML and Maven
class TestMavenUtils_get_plugin_configuration_values_IT_Maven(BaseTestCase):

    def setUp(self):
        super().setUp()

        maven_path = sh.which('mvn')
        if not maven_path:
            self.skipTest('maven is not installed')

    def __get_test_file_path(self, file):
        return os.path.join(
            os.path.dirname(__file__),
            'files',
            'get_plugin_configuration_values_IT',
            file
        )

    def test_with_profile_no_phases_with_config_surefire(self):
        # setup
        pom_file = self.__get_test_file_path('pom-no-plugin-config.xml')

        with TempDirectory() as temp_dir:
            # run test
            actual_values = get_plugin_configuration_values(
                plugin_name='maven-surefire-plugin',
                configuration_key='reportsDirectory',
                work_dir_path=temp_dir.path,
                pom_file=pom_file,
                profiles='integration-test',
                phases_and_goals=None
            )

            # validate
            self.assertEqual(len(actual_values), 1)
            self.assertEqual(
                actual_values[0],
                os.path.join(
                    os.path.dirname(os.path.abspath(pom_file)),
                    'target',
                    'surefire-reports-integration-test'
                )
            )

@patch('ploigos_step_runner.utils.maven.get_plugin_configuration_values')
class TestMavenUtils_get_plugin_configuration_absolute_path_values(BaseTestCase):
    def test_one_relative_result_with_relative_pom(self, mock_get_plugin_configuration_values):
        # set up mock
        mock_get_plugin_configuration_values.return_value = ['mock/relative/path/foo1']

        # run test
        actual_values = get_plugin_configuration_absolute_path_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=None
        )

        # validate
        self.assertEqual(actual_values, [os.path.join(os.getcwd(), 'mock/relative/path/foo1')])

    def test_one_relative_result_with_absolute_pom(self, mock_get_plugin_configuration_values):
        # set up mock
        mock_get_plugin_configuration_values.return_value = ['mock/relative/path/foo1']

        # run test
        actual_values = get_plugin_configuration_absolute_path_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='/mock/absolute/path/mock-pom.xml',
            profiles=None,
            phases_and_goals=None
        )

        # validate
        self.assertEqual(actual_values, ['/mock/absolute/path/mock/relative/path/foo1'])

    def test_one_abslute_result_with_relative_pom(self, mock_get_plugin_configuration_values):
        # set up mock
        mock_get_plugin_configuration_values.return_value = ['/mock/absolute/path/foo1']

        # run test
        actual_values = get_plugin_configuration_absolute_path_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=None
        )

        # validate
        self.assertEqual(actual_values, ['/mock/absolute/path/foo1'])

    def test_one_abslute_result_with_absolute_pom(self, mock_get_plugin_configuration_values):
        # set up mock
        mock_get_plugin_configuration_values.return_value = ['/mock/absolute/path/foo1']

        # run test
        actual_values = get_plugin_configuration_absolute_path_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='/mock/awesome/different/aboslute/path/mock-pom.xml',
            profiles=None,
            phases_and_goals=None
        )

        # validate
        self.assertEqual(actual_values, ['/mock/absolute/path/foo1'])

    def test_no_config_values_found_none_returned(self, mock_get_plugin_configuration_values):
        # set up mock
        mock_get_plugin_configuration_values.return_value = None

        # run test
        actual_values = get_plugin_configuration_absolute_path_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=None
        )

        # validate
        self.assertEqual(actual_values, [])

    def test_no_config_values_found_empty_list_returned(self, mock_get_plugin_configuration_values):
        # set up mock
        mock_get_plugin_configuration_values.return_value = []

        # run test
        actual_values = get_plugin_configuration_absolute_path_values(
            plugin_name='mock-maven-plugin',
            configuration_key='mockAwesomeConfig',
            work_dir_path='/mock/work_dir',
            pom_file='mock-pom.xml',
            profiles=None,
            phases_and_goals=None
        )

        # validate
        self.assertEqual(actual_values, [])
