"""Shared utils for dealing with containers.
"""

import sys

import sh
from ploigos_step_runner.config.config_value import ConfigValue


def container_registries_login(  #pylint: disable=too-many-branches
    registries,
    containers_config_auth_file=None,
    containers_config_tls_verify=True):
    """Logs into one or more container registries.

    Requires one of the following to be installed to do the authentication:
    * buidlah
    * podman
    * skopeo

    Notes
    -----
    registries example 1 (dict of dicts where child dict keys are registry uri):

        {
            'registry.redhat.io': {
                'username': 'hello@world.xyz',
                'password': 'nope'
            },
            'registry.internal.example.xyz': {
                'username': 'hello@example.xyz',
                'password': 'nope'
            }
        }

    registries example 2 (dict of dicts where uri is key in child dicts):

        {
            'redhat': {
                'uri': registry.redhat.io
                'username': 'hello@world.xyz',
                'password': 'nope'
            },
            'internal': {
                'uri': 'registry.internal.example.xyz'
                'username': 'hello@example.xyz',
                'password': 'nope'
            }
        }

    registries example 3 (list of dicts where uri is key in child dicts):

        [
            {
                'uri': registry.redhat.io
                'username': 'hello@world.xyz',
                'password': 'nope'
            },
            {
                'uri': 'registry.internal.example.xyz'
                'username': 'hello@example.xyz',
                'password': 'nope'
            }
        ]

    Parameters
    ----------
    registries : dict or list or None
        Dict of dicts of registry configurations or a list of dicts of registry configurations.
        See Notes section for details.
        If none, does nothing.
    containers_config_auth_file : str, optional
        Path of the authentication file.
        If not specified default of the underlying authentication system will be used.

    See Also
    --------
    container_registry_login : Performs the login for a single container registry
    sh.buildah : https://www.mankier.com/1/buildah-login
    sh.podman : https://www.mankier.com/1/podman-login
    sh.skopeo : https://www.mankier.com/1/skopeo-login
    """

    if registries is None:
        return

    assert isinstance(registries, (dict, list))

    if isinstance(registries, dict):
        for registry_key, registry_conf in registries.items():
            if isinstance(registry_conf, ConfigValue):
                registry_conf = registry_conf.value

            assert 'username' in registry_conf, \
                f"Configuration for container registry ({registry_key}) " \
                f"must specify a 'username': {registry_conf}"
            assert 'password' in registry_conf, \
                f"Configuration for container registry ({registry_key}) " \
                f"must specify a 'password': {registry_conf}"

            # if uri is key in the dict then use that for the registry uri
            # else use the dict key for the registry conf as the registry uri
            if 'uri' in registry_conf:
                registry_uri = registry_conf['uri']
            else:
                registry_uri = registry_key

            if containers_config_tls_verify is False:
                registry_tls_verify = False
            else:
                if 'tls-verify' in registry_conf:
                    registry_tls_verify = registry_conf['tls-verify']
                else:
                    registry_tls_verify = True

            container_registry_login(
                container_registry_uri=registry_uri,
                container_registry_username=registry_conf['username'],
                container_registry_password=registry_conf['password'],
                container_registry_tls_verify=registry_tls_verify,
                containers_config_auth_file=containers_config_auth_file
            )
    elif isinstance(registries, list):
        for registry_conf in registries:
            if isinstance(registry_conf, ConfigValue):
                registry_conf = registry_conf.value

            assert 'uri' in registry_conf, \
                f"Configuration for container registry " \
                f"must specify a 'uri': {registry_conf}"
            assert 'username' in registry_conf, \
                f"Configuration for container registry " \
                f"must specify a 'username': {registry_conf}"
            assert 'password' in registry_conf, \
                f"Configuration for container registry " \
                f"must specify a 'password': {registry_conf}"

            if containers_config_tls_verify is False:
                registry_tls_verify = False
            else:
                if 'tls-verify' in registry_conf:
                    registry_tls_verify = registry_conf['tls-verify']
                else:
                    registry_tls_verify = True

            container_registry_login(
                container_registry_uri=registry_conf['uri'],
                container_registry_username=registry_conf['username'],
                container_registry_password=registry_conf['password'],
                container_registry_tls_verify=registry_tls_verify,
                containers_config_auth_file=containers_config_auth_file
            )

def container_registry_login(
    container_registry_uri,
    container_registry_username,
    container_registry_password,
    container_registry_tls_verify=True,
    containers_config_auth_file=None
):
    """Performs the login for a single container registry.

    Requires one of the following to be installed to do the authentication:
    * buidlah
    * podman
    * skopeo

    Parameters
    ----------
    container_registry_uri : str or ConfigValue
        URI to the container registry to log into.
    container_registry_username : str or ConfigValue
        Username to log into the container registry with.
    container_registry_password : str or ConfigValue
        Password to log into the container registry with.
    container_registry_tls_verify : bool or str or ConfigValue
        True to verify container registry certificates as part of authenticating.
        False to ignore certificate chain.
        NOTE: no matter what SSL is used to authenticate with container registry
    containers_config_auth_file : str or ConfigValue, optional
        Path of the authentication file.
        If not specified default of the underlying authentication system will be used.

    Raises
    ------
    RuntimeError
        When can not find tool to login to container registry with.
        When error loging into container registry.

    See Also
    --------
    container_registries_login : authenticate with multiple container registries
    sh.buildah : https://www.mankier.com/1/buildah-login
    sh.podman : https://www.mankier.com/1/podman-login
    sh.skopeo : https://www.mankier.com/1/skopeo-login
    """

    assert container_registry_uri
    assert container_registry_username
    assert container_registry_password

    if isinstance(container_registry_uri, ConfigValue):
        container_registry_uri = container_registry_uri.value
    if isinstance(container_registry_username, ConfigValue):
        container_registry_username = container_registry_username.value
    if isinstance(container_registry_password, ConfigValue):
        container_registry_password = container_registry_password.value
    if isinstance(container_registry_tls_verify, ConfigValue):
        container_registry_tls_verify = container_registry_tls_verify.value
    if isinstance(containers_config_auth_file, ConfigValue):
        containers_config_auth_file = containers_config_auth_file.value

    # can use any of these tools to authenticate, look for them all and use first available
    #
    # NOTE: this all works because these three commands take the exact same parameters for login
    # if implementing some new command, like docker, you will need to deal with the differences
    buildah_path = sh.which('buildah')
    podman_path = sh.which('podman')
    skopeo_path = sh.which('skopeo')
    if buildah_path is not None:
        container_command = sh.buildah.bake() #pylint: disable=no-member
    elif podman_path is not None:
        container_command = sh.podman.bake() #pylint: disable=no-member
    elif skopeo_path is not None:
        container_command = sh.skopeo.bake() #pylint: disable=no-member
    else:
        raise RuntimeError(
            f"When attempting to login to container registry ({container_registry_uri}) "
            "could not find one of the expected tools (buildah, podman, skopeo) to login with."
        )

    login_command_named_flags = {
        'password_stdin': True,
        'username': container_registry_username,
        'tls_verify': str(container_registry_tls_verify).lower()
    }
    if containers_config_auth_file:
        login_command_named_flags['authfile'] = containers_config_auth_file

    try:
        # NOTE: need to bake in the flags prior to the registry due to nonesense with
        #       required ordering by the login command and how sh handles
        #       escaping and ordering parameters
        login_comnmand = container_command.login.bake(**login_command_named_flags)
        login_comnmand(
            container_registry_uri,
            _in=container_registry_password,
            _out=sys.stdout,
            _err=sys.stderr,
            _tee='err'
        )
    except sh.ErrorReturnCode as error:
        raise RuntimeError(
            f"Failed to login to container registry ({container_registry_uri}) "
            f"with username ({container_registry_username}): {error}"
        ) from error
