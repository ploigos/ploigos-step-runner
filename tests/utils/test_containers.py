import re
from io import IOBase
from unittest.mock import ANY, call, patch

import sh
from ploigos_step_runner.config import ConfigValue
from ploigos_step_runner.utils.containers import *
from tests.helpers.base_test_case import BaseTestCase
from tests.helpers.test_utils import *


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

    @patch('sh.Command')
    @patch('sh.which', create=True)
    def test_use_given_command_exists(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd='fake-podman',
            cmd_path='/mock/fake-podman'
        )

        container_registry_login(
            container_registry_uri='registry.example.xyz',
            container_registry_username='example',
            container_registry_password='nope',
            container_command_short_name='fake-podman'
        )

        container_command_mock().bake.assert_called_once()
        container_command_mock().bake().login.bake.assert_called_once_with(
            password_stdin=True,
            username='example',
            tls_verify='true'
        )
        container_command_mock().bake().login.bake().assert_called_once_with(
            'registry.example.xyz',
            _in='nope',
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.Command')
    @patch('sh.which', create=True)
    def test_use_given_command_does_not_exists(self, which_mock, container_command_mock):
        which_mock.side_effect = create_which_side_effect(
            cmd=None,
            cmd_path=None
        )

        with self.assertRaisesRegex(
            RuntimeError,
            r"When attempting to login to container registry \(registry.example.xyz\) "
            r"could not find the given expected tool \(fake-podman\) to login with"
        ):
            container_registry_login(
                container_registry_uri='registry.example.xyz',
                container_registry_username='example',
                container_registry_password='nope',
                container_command_short_name='fake-podman'
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
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name=None
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
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name=None
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
                containers_config_auth_file=None,
                container_command_short_name=None,
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name=None
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
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name=None
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
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name=None
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
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name=None
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
                containers_config_auth_file='/tmp/mock/auth.json',
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file='/tmp/mock/auth.json',
                container_command_short_name=None
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
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name=None
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

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_given_command_short_name_exists(self, container_registry_login_mock):
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

        container_registries_login(
            registries=registries,
            container_command_short_name='fake-podman'
        )

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name='fake-podman'
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name='fake-podman'
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)


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
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=False,
                containers_config_auth_file=None,
                container_command_short_name=None
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
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=False,
                containers_config_auth_file=None,
                container_command_short_name=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)


    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_list_of_dicts_truthy(self, container_registry_login_mock):
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

        container_registries_login(registries, containers_config_tls_verify=1)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=True,
                containers_config_auth_file=None,
                container_command_short_name=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

    @patch('ploigos_step_runner.utils.containers.container_registry_login')
    def test_list_of_dicts_falsey(self, container_registry_login_mock):
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

        container_registries_login(registries, containers_config_tls_verify=0)

        calls = [
            call(
                container_registry_uri='registry.redhat.io',
                container_registry_username='hello1@world.xyz',
                container_registry_password='nope1',
                container_registry_tls_verify=False,
                containers_config_auth_file=None,
                container_command_short_name=None
            ),
            call(
                container_registry_uri='registry.internal.example.xyz',
                container_registry_username='hello2@example.xyz',
                container_registry_password='nope2',
                container_registry_tls_verify=False,
                containers_config_auth_file=None,
                container_command_short_name=None
            )
        ]
        container_registry_login_mock.assert_has_calls(calls)

class Test_create_container_from_image(BaseTestCase):
    @patch('sh.buildah', create=True)
    def test_success_default_repository_type(self, buildah_mock):
        # setup test
        image_tag = "localhost/mock-org/mock-image:v0.42.0-mock"

        # run test
        buildah_mock.side_effect = create_sh_side_effect(
            mock_stdout='mock-image-working-container-mock'
        )
        actual_container_name = create_container_from_image(
            image_tag=image_tag
        )

        # verify
        self.assertEqual(actual_container_name, 'mock-image-working-container-mock')

        buildah_mock.assert_called_once_with(
            'from',
            f"container-storage:{image_tag}",
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    def test_success_remote_repository_type(self, buildah_mock):
        # setup test
        image_tag = "quay.io/mock-org/mock-image:v0.42.0-mock"

        # run test
        buildah_mock.side_effect = create_sh_side_effect(
            mock_stdout='mock-image-working-container-mock'
        )
        actual_container_name = create_container_from_image(
            image_tag=image_tag,
            repository_type='docker://'
        )

        # verify
        self.assertEqual(actual_container_name, 'mock-image-working-container-mock')

        buildah_mock.assert_called_once_with(
            'from',
            f"docker://{image_tag}",
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    def test_error(self, buildah_mock):
        # setup test
        image_tag = "localhost/mock-org/mock-image:v0.42.0-mock"

        # run test with mock error
        with self.assertRaisesRegex(
            RuntimeError,
            re.compile(
                rf"Error creating container from image \({image_tag}\):"
                r".*RAN: buildah"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            )
        ):
            buildah_mock.side_effect = sh.ErrorReturnCode('buildah', b'mock out', b'mock error')
            create_container_from_image(
                image_tag=image_tag
            )

        # verify
        buildah_mock.assert_called_once_with(
            'from',
            f"container-storage:{image_tag}",
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

class Test_mount_container(BaseTestCase):
    @patch('sh.buildah', create=True)
    def test_success(self, buildah_mock):
        buildah_unshare_command = sh.buildah.bake('unshare')
        container_name = "test"

        expected_mount_path = '/this/is/a/path'
        buildah_mock.bake('unshare').bake('buildah', 'mount').side_effect = create_sh_side_effect(
            mock_stdout=f"{expected_mount_path}",
        )

        container_mount_path = mount_container(
            buildah_unshare_command=buildah_unshare_command,
            container_id=container_name
        )

        self.assertEqual(container_mount_path, expected_mount_path)

        buildah_mock.bake('unshare').bake('buildah', 'mount').assert_called_once_with(
            container_name,
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

    @patch('sh.buildah', create=True)
    def test_buildah_error(self, buildah_mock):
        buildah_unshare_command = sh.buildah.bake('unshare')
        container_name = "test"

        buildah_mock.bake('unshare').bake('buildah', 'mount').side_effect = sh.ErrorReturnCode(
            'buildah mount',
            b'mock out',
            b'mock error'
        )

        with self.assertRaisesRegex(
                RuntimeError,
                re.compile(
                    rf"Error mounting container \({container_name}\):"
                    r".*RAN: buildah"
                    r".*STDOUT:"
                    r".*mock out"
                    r".*STDERR:"
                    r".*mock error",
                    re.DOTALL
                )
        ):
            mount_container(
                buildah_unshare_command=buildah_unshare_command,
                container_id=container_name
            )

        buildah_mock.bake('unshare').bake('buildah', 'mount').assert_called_once_with(
            container_name,
            _out=Any(IOBase),
            _err=Any(IOBase),
            _tee='err'
        )

class Test_determine_container_image_build_tag_info(BaseTestCase):
    def test_given_image_version(self):
        actual_build_full_tag, actual_build_short_tag, actual_image_registry_uri, \
            actual_image_repository, actual_image_version = \
            determine_container_image_build_tag_info(
                image_version='1.0-123abc',
                organization='mock-org',
                application_name='mock-app',
                service_name='mock-service'
            )

        self.assertEqual(
            actual_build_full_tag,
            'localhost/mock-org/mock-app-mock-service:1.0-123abc'
        )
        self.assertEqual(
            actual_build_short_tag,
            'mock-org/mock-app-mock-service:1.0-123abc'
        )
        self.assertEqual(
            actual_image_registry_uri,
            'localhost'
        )
        self.assertEqual(
            actual_image_repository,
            'mock-app-mock-service'
        )
        self.assertEqual(
            actual_image_version,
            '1.0-123abc'
        )

    def test_default_image_version(self):
        actual_build_full_tag, actual_build_short_tag, actual_image_registry_uri, \
            actual_image_repository, actual_image_version = \
            determine_container_image_build_tag_info(
                image_version=None,
                organization='mock-org',
                application_name='mock-app',
                service_name='mock-service'
            )

        self.assertEqual(
            actual_build_full_tag,
            'localhost/mock-org/mock-app-mock-service:latest'
        )
        self.assertEqual(
            actual_build_short_tag,
            'mock-org/mock-app-mock-service:latest'
        )
        self.assertEqual(
            actual_image_registry_uri,
            'localhost'
        )
        self.assertEqual(
            actual_image_repository,
            'mock-app-mock-service'
        )
        self.assertEqual(
            actual_image_version,
            'latest'
        )

@patch('sh.buildah', create=True)
class Test_inspect_container_image(BaseTestCase):
    def test_success_no_auth(self, mock_buildah):
        # setup mock
        def buildah_inspect_side_effect(container_image_uri, _out):
            _out.write('''{
  "mock-value": "mock container details"
}''')
        mock_buildah.inspect.side_effect = buildah_inspect_side_effect

        # run test
        actual_container_details = inspect_container_image(
            container_image_uri='mock.io/mock/awesome-image:latest'
        )

        # validate
        self.assertEqual(
            actual_container_details,
            {
                'mock-value': 'mock container details'
            }
        )
        mock_buildah.pull.assert_called_once_with(
            'mock.io/mock/awesome-image:latest'
        )
        mock_buildah.inspect.assert_called_once_with(
            'mock.io/mock/awesome-image:latest',
            _out=ANY
        )

    def test_success_with_auth(self, mock_buildah):
        # setup mock
        def buildah_inspect_side_effect(*args, _out):
            _out.write('''{
  "mock-value": "mock container details"
}''')
        mock_buildah.inspect.side_effect = buildah_inspect_side_effect

        # run test
        actual_container_details = inspect_container_image(
            container_image_uri='mock.io/mock/awesome-image:latest',
            containers_config_auth_file='/mock/auth-file'
        )

        # validate
        self.assertEqual(
            actual_container_details,
            {
                'mock-value': 'mock container details'
            }
        )
        mock_buildah.pull.assert_called_once_with(
            '--authfile', '/mock/auth-file',
            'mock.io/mock/awesome-image:latest'
        )
        mock_buildah.inspect.assert_called_once_with(
            'mock.io/mock/awesome-image:latest',
            _out=ANY
        )

    def test_failure_pull_no_auth(self, mock_buildah):
        # setup mock
        mock_buildah.pull.side_effect = sh.ErrorReturnCode('buildah pull', b'mock out', b'mock error')

        # run test
        with self.assertRaisesRegex(
            RuntimeError,
            re.compile(
                "Error pulling container image \(mock.io/mock/awesome-image:latest\) for inspection:"
                r".*RAN: buildah pull"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            )
        ):
            inspect_container_image(
                container_image_uri='mock.io/mock/awesome-image:latest'
            )

        # validate
        mock_buildah.pull.assert_called_once_with(
            'mock.io/mock/awesome-image:latest'
        )
        mock_buildah.inspect.assert_not_called()

    def test_failure_inspect_no_auth(self, mock_buildah):
        # setup mock
        mock_buildah.inspect.side_effect = sh.ErrorReturnCode('buildah', b'mock out', b'mock error')

        # run test
        with self.assertRaisesRegex(
            RuntimeError,
            re.compile(
                "Error inspecting container image \(mock.io/mock/awesome-image:latest\)"
                r".*RAN: buildah"
                r".*STDOUT:"
                r".*mock out"
                r".*STDERR:"
                r".*mock error",
                re.DOTALL
            )
        ):
            inspect_container_image(
                container_image_uri='mock.io/mock/awesome-image:latest'
            )

        # validate
        mock_buildah.pull.assert_called_once_with(
            'mock.io/mock/awesome-image:latest'
        )
        mock_buildah.inspect.assert_called_once_with(
            'mock.io/mock/awesome-image:latest',
            _out=ANY
        )
