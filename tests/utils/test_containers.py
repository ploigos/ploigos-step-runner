import sys
import sh
import re
from io import IOBase
from unittest.mock import patch, call

from tests.helpers.base_test_case import BaseTestCase
from tests.helpers.test_utils import *

from ploigos_step_runner.config import ConfigValue
from ploigos_step_runner.utils.containers import container_registry_login, container_registries_login

def create_which_side_effect(cmd, cmd_path):
    def which_side_effect(*args, **kwargs):
        if args[0] == cmd:
            return cmd_path
        else:
            return None

    return which_side_effect

class TestContainerRegistryLogin(BaseTestCase):
    @patch('sh.buildah', create=True)
    @patch('sh.which', create=True)
    def test_buildah(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='buildah',
            cmd_path='/mock/buildah'
        )

        container_registry_login(
            container_registry_uri='registry.example.xyz',
            container_registry_username='example',
            container_registry_password='nope'
        )

        container_command_mock.bake.assert_called_once()
        container_command_mock.bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='true'
        )
        container_command_mock.bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.podman', create=True)
    @patch('sh.which', create=True)
    def test_podman(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='podman',
            cmd_path='/mock/podman'
        )

        container_registry_login(
            container_registry_uri='registry.example.xyz',
            container_registry_username='example',
            container_registry_password='nope'
        )

        container_command_mock.bake.assert_called_once()
        container_command_mock.bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='true'
        )
        container_command_mock.bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.skopeo', create=True)
    @patch('sh.which', create=True)
    def test_skopeo(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='skopeo',
            cmd_path='/mock/skopeo'
        )

        container_registry_login(
            container_registry_uri='registry.example.xyz',
            container_registry_username='example',
            container_registry_password='nope'
        )

        container_command_mock.bake.assert_called_once()
        container_command_mock.bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='true'
        )
        container_command_mock.bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    @patch('sh.which', create=True)
    def test_config_auth_param(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='buildah',
            cmd_path='/mock/buildah'
        )

        container_registry_login(
            container_registry_uri='registry.example.xyz',
            container_registry_username='example',
            container_registry_password='nope',
            containers_config_auth_file='/tmp/test/auth.json'
        )

        container_command_mock.bake.assert_called_once()
        container_command_mock.bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='true',
            authfile='/tmp/test/auth.json'
        )
        container_command_mock.bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    @patch('sh.which', create=True)
    def test_tls_verify_param_bool_false(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='buildah',
            cmd_path='/mock/buildah'
        )

        container_registry_login(
            container_registry_uri='registry.example.xyz',
            container_registry_username='example',
            container_registry_password='nope',
            container_registry_tls_verify=False
        )

        container_command_mock.bake.assert_called_once()
        container_command_mock.bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='false',
        )
        container_command_mock.bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    @patch('sh.which', create=True)
    def test_tls_verify_param_str_false(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='buildah',
            cmd_path='/mock/buildah'
        )

        container_registry_login(
            container_registry_uri='registry.example.xyz',
            container_registry_username='example',
            container_registry_password='nope',
            container_registry_tls_verify="false"
        )

        container_command_mock.bake.assert_called_once()
        container_command_mock.bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='false',
        )
        container_command_mock.bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    @patch('sh.which', create=True)
    def test_tls_verify_param_bool_true(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='buildah',
            cmd_path='/mock/buildah'
        )

        container_registry_login(
            container_registry_uri='registry.example.xyz',
            container_registry_username='example',
            container_registry_password='nope',
            container_registry_tls_verify=True
        )

        container_command_mock.bake.assert_called_once()
        container_command_mock.bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='true',
        )
        container_command_mock.bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    @patch('sh.which', create=True)
    def test_tls_verify_param_str_true(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='buildah',
            cmd_path='/mock/buildah'
        )

        container_registry_login(
            container_registry_uri='registry.example.xyz',
            container_registry_username='example',
            container_registry_password='nope',
            container_registry_tls_verify="true"
        )

        container_command_mock.bake.assert_called_once()
        container_command_mock.bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='true',
        )
        container_command_mock.bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    @patch('sh.which', create=True)
    def test_configvalue_params(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='buildah',
            cmd_path='/mock/buildah'
        )

        container_registry_login(
            container_registry_uri=ConfigValue('registry.example.xyz'),
            container_registry_username=ConfigValue('example'),
            container_registry_password=ConfigValue('nope'),
            container_registry_tls_verify=ConfigValue(True),
            containers_config_auth_file=ConfigValue('/tmp/test/auth.json')
        )

        container_command_mock.bake.assert_called_once()
        container_command_mock.bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='true',
            authfile='/tmp/test/auth.json'
        )
        container_command_mock.bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.which', create=True)
    def test_no_container_registry_login_tools_found(self, which_mock):
        # ensure none of the tools are found
        which_mock.side_effect = create_which_side_effect(
            cmd=None,
            cmd_path=None
        )

        with self.assertRaisesRegex(
            RuntimeError,
            r"When attempting to login to container registry \(registry.example.xyz\) "
            r"could not find one of the expected tools \(buildah, podman, skopeo\) to login with."
        ):
            container_registry_login(
                container_registry_uri='registry.example.xyz',
                container_registry_username='example',
                container_registry_password='nope'
            )

    @patch('sh.buildah', create=True)
    @patch('sh.which', create=True)
    def test_buildah_login_fail(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='buildah',
            cmd_path='/mock/buildah'
        )

        with self.assertRaisesRegex(
            RuntimeError,
            re.compile(
                r"Failed to login to container registry \(registry.example.xyz\)"
                r" with username \(example\):"
                r".*RAN: buildah login"
                r".*STDOUT:"
                r".*mock stdout"
                r".*STDERR:"
                r".*mock stderr login error",
                re.DOTALL
            )
        ):
            container_command_mock.bake().login.bake().side_effect = sh.ErrorReturnCode(
                'buildah login',
                b'mock stdout',
                b'mock stderr login error'
            )
            container_registry_login(
                container_registry_uri='registry.example.xyz',
                container_registry_username='example',
                container_registry_password='nope'
            )

class TestContainerRegistriesLogin(BaseTestCase):
    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_dict_of_dicts(self, container_registry_login_mock):
        registries = {
            'registry.redhat.io': {
                'username': 'hello1@world.xyz',
                'password': 'nope1'
            },
            'registry.internal.example.xyz': {
                'username': 'hello2@example.xyz',
                'password': 'nope2'
            }
        }

        container_registries_login(registries)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_dict_of_dicts_with_tls_verify_value(self, container_registry_login_mock):
        registries = {
            'registry.redhat.io': {
                'username': 'hello1@world.xyz',
                'password': 'nope1',
                'tls-verify': False
            },
            'registry.internal.example.xyz': {
                'username': 'hello2@example.xyz',
                'password': 'nope2',
                'tls-verify': True
            }
        }

        container_registries_login(registries)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=False,
                containers_config_auth_file=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_list_of_dicts_with_containers_config_auth_file(self, container_registry_login_mock):
        registries = {
            'registry.redhat.io': {
                'username': 'hello1@world.xyz',
                'password': 'nope1',
                'tls-verify': False
            },
            'registry.internal.example.xyz': {
                'username': 'hello2@example.xyz',
                'password': 'nope2',
                'tls-verify': True
            }
        }

        container_registries_login(registries, '/tmp/mock/auth.json')

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=True,
                containers_config_auth_file='/tmp/mock/auth.json'
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file='/tmp/mock/auth.json'
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_dict_of_config_values(self, container_registry_login_mock):
        registries = {
            'registry.redhat.io': ConfigValue({
                'username': 'hello1@world.xyz',
                'password': 'nope1'
            }),
            'registry.internal.example.xyz': ConfigValue({
                'username': 'hello2@example.xyz',
                'password': 'nope2'
            })
        }

        container_registries_login(registries)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_dict_of_dicts_with_uri_keys(self, container_registry_login_mock):
        registries = {
            'redhat': {
                'uri': 'registry.redhat.io',
                'username': 'hello1@world.xyz',
                'password': 'nope1'
            },
            'internal': {
                'uri': 'registry.internal.example.xyz',
                'username': 'hello2@example.xyz',
                'password': 'nope2'
            }
        }

        container_registries_login(registries)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_list_of_dicts(self, container_registry_login_mock):
        registries = [
            {
                'uri': 'registry.redhat.io',
                'username': 'hello1@world.xyz',
                'password': 'nope1'
            },
            {
                'uri': 'registry.internal.example.xyz',
                'username': 'hello2@example.xyz',
                'password': 'nope2'
            }
        ]

        container_registries_login(registries)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_list_of_dicts_with_tls_verify_value(self, container_registry_login_mock):
        registries = [
            {
                'uri': 'registry.redhat.io',
                'username': 'hello1@world.xyz',
                'password': 'nope1',
                'tls-verify': False
            },
            {
                'uri': 'registry.internal.example.xyz',
                'username': 'hello2@example.xyz',
                'password': 'nope2',
                'tls-verify': True
            }
        ]

        container_registries_login(registries)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=False,
                containers_config_auth_file=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_list_of_dicts_with_containers_config_auth_file(self, container_registry_login_mock):
        registries = [
            {
                'uri': 'registry.redhat.io',
                'username': 'hello1@world.xyz',
                'password': 'nope1'
            },
            {
                'uri': 'registry.internal.example.xyz',
                'username': 'hello2@example.xyz',
                'password': 'nope2'
            }
        ]

        container_registries_login(registries, '/tmp/mock/auth.json')

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=True,
                containers_config_auth_file='/tmp/mock/auth.json'
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file='/tmp/mock/auth.json'
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_list_of_config_value(self, container_registry_login_mock):
        registries = [
            ConfigValue({
                'uri': 'registry.redhat.io',
                'username': 'hello1@world.xyz',
                'password': 'nope1'
            }),
            ConfigValue({
                'uri': 'registry.internal.example.xyz',
                'username': 'hello2@example.xyz',
                'password': 'nope2'
            })
        ]

        container_registries_login(registries)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    def test_dict_of_dicts_missing_username(self):
        registries = {
            'registry.redhat.io': {
                'password': 'nope1'
            }
        }

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for container registry \(registry.redhat.io\) "
            r"must specify a 'username': {'password': 'nope1'}"
        ):
            container_registries_login(registries)

    def test_dict_of_dicts_missing_password(self):
        registries = {
            'registry.redhat.io': {
                'username': 'hello1@world.xyz'
            }
        }

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for container registry \(registry.redhat.io\) "
            r"must specify a 'password': {'username': 'hello1@world.xyz'}"
        ):
            container_registries_login(registries)

    def test_dict_of_dicts_missing_username(self):
        registries = {
            'registry.redhat.io': {
                'password': 'nope1'
            }
        }

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for container registry \(registry.redhat.io\) "
            r"must specify a 'username': {'password': 'nope1'}"
        ):
            container_registries_login(registries)

    def test_list_of_dicts_missing_uri(self):
        registries = [
            {
                'username': 'hello1@world.xyz',
                'password': 'nope1'
            }
        ]

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for container registry "
            r"must specify a 'uri': {'username': 'hello1@world.xyz', 'password': 'nope1'}"
        ):
            container_registries_login(registries)

    def test_list_of_dicts_missing_password(self):
        registries = [
            {
                'uri': 'registry.redhat.io',
                'username': 'hello1@world.xyz'
            }
        ]

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for container registry "
            r"must specify a 'password': {'uri': 'registry.redhat.io', 'username': 'hello1@world.xyz'}"
        ):
            container_registries_login(registries)

    def test_list_of_dicts_missing_username(self):
        registries = [
            {
                'uri': 'registry.redhat.io',
                'password': 'nope1'
            }
        ]

        with self.assertRaisesRegex(
            AssertionError,
            r"Configuration for container registry "
            r"must specify a 'username': {'uri': 'registry.redhat.io', 'password': 'nope1'}"
        ):
            container_registries_login(registries)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_registries_none(self, container_registry_login):
        registries = None

        container_registries_login(registries)

        container_registry_login.assert_not_called()


class TestContainerRegistriesLoginForceOverrideTlsVerifyLogin(BaseTestCase):
    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_dict_of_dicts(self, container_registry_login_mock):
        registries = {
            'registry.redhat.io': {
                'username': 'hello1@world.xyz',
                'password': 'nope1'
            },
            'registry.internal.example.xyz': {
                'username': 'hello2@example.xyz',
                'password': 'nope2'
            }
        }

        container_registries_login(registries, containers_config_tls_verify=False)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=False,
                containers_config_auth_file=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=False,
                containers_config_auth_file=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_list_of_dicts(self, container_registry_login_mock):
        registries = [
            {
                'uri': 'registry.redhat.io',
                'username': 'hello1@world.xyz',
                'password': 'nope1'
            },
            {
                'uri': 'registry.internal.example.xyz',
                'username': 'hello2@example.xyz',
                'password': 'nope2'
            }
        ]

        container_registries_login(registries, containers_config_tls_verify=False)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=False,
                containers_config_auth_file=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=False,
                containers_config_auth_file=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)
