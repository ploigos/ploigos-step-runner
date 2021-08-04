"""Shared utils for dealing with containers.
"""

import sys
from io import StringIO

import sh
from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback


def container_registries_login(  #pylint: disable=too-many-branches
    registries,
    containers_config_auth_file=None,
    containers_config_tls_verify=True,
    container_command_short_name=None
):
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
    container_command_short_name : str, optional
        Short name for the command to log in with.
        If not provided will pick the first command found in order (buildah, podman, skopeo).

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

            if containers_config_tls_verify:
                if 'tls-verify' in registry_conf:
                    registry_tls_verify = registry_conf['tls-verify']
                else:
                    registry_tls_verify = True
            else:
                registry_tls_verify = False

            container_registry_login(
                container_registry_uri=registry_uri,
                container_registry_username=registry_conf['username'],
                container_registry_password=registry_conf['password'],
                container_registry_tls_verify=registry_tls_verify,
                containers_config_auth_file=containers_config_auth_file,
                container_command_short_name=container_command_short_name
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

            if containers_config_tls_verify:
                if 'tls-verify' in registry_conf:
                    registry_tls_verify = registry_conf['tls-verify']
                else:
                    registry_tls_verify = True
            else:
                registry_tls_verify = False

            container_registry_login(
                container_registry_uri=registry_conf['uri'],
                container_registry_username=registry_conf['username'],
                container_registry_password=registry_conf['password'],
                container_registry_tls_verify=registry_tls_verify,
                containers_config_auth_file=containers_config_auth_file,
                container_command_short_name=container_command_short_name
            )

def container_registry_login( #pylint: disable=too-many-arguments,too-many-branches
    container_registry_uri,
    container_registry_username,
    container_registry_password,
    container_registry_tls_verify=True,
    containers_config_auth_file=None,
    container_command_short_name=None
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
    container_command_short_name : str, optional
        Short name for the command to log in with.
        If not provided will pick the first command found in order (buildah, podman, skopeo).

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
    if container_command_short_name:
        given_command_path = sh.which(container_command_short_name)
        if given_command_path:
            container_command = sh.Command(container_command_short_name).bake()
        else:
            raise RuntimeError(
                f"When attempting to login to container registry ({container_registry_uri}) "
                f"could not find the given expected tool ({container_command_short_name}) "
                "to login with."
            )
    elif buildah_path is not None:
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
        print(f"Login ({container_command}) to container image registry ({container_registry_uri})")
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

def create_container_from_image(
    image_tag,
    repository_type='container-storage:'
):
    """Import a container image using buildah form a TAR file.

    Parameters
    ----------
    image_tag : str
        Image tag to create a container from.
        ex:
        * localhost/my-app:latest
        * quay.io/my-org/my-app:latest
        * docker-archive:/local/path/to/my-app-container-image.tar
    container_name : str
        name for the working container.
    repository_type : str
        The type of repository to mount the given image tag from.
        See https://github.com/containers/skopeo for details on different repository types.

    Returns
    -------
    str
        Name of the imported container.

    Raises
    ------
    RuntimeError
        If error importing image.
    """
    container_name = None
    try:
        buildah_from_out_buff = StringIO()
        buildah_from_out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
            sys.stdout,
            buildah_from_out_buff
        ])
        sh.buildah(  # pylint: disable=no-member
            'from',
            f"{repository_type}{image_tag}",
            _out=buildah_from_out_callback,
            _err=sys.stderr,
            _tee='err'
        )
        container_name = buildah_from_out_buff.getvalue().rstrip()
    except sh.ErrorReturnCode as error:
        raise RuntimeError(
            f'Error creating container from image ({image_tag}): {error}'
        ) from error

    return container_name


def mount_container(buildah_unshare_command, container_id):
    """Use buildah to mount a container.

    Parameters
    ----------
    buildah_unshare_command : sh.buildah.unshare.bake()
        A baked sh.buildah.unshare command to use to run this command in the context off
        so that this can be done "rootless".
    container_id : str
        ID of the container to mount.

    Returns
    -------
    str
        Absolute path to the mounted container.

    Raises
    ------
    RuntimeError
        If error mounting the container.
    """
    mount_path = None
    try:
        buildah_mount_out_buff = StringIO()
        buildah_mount_out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
            sys.stdout,
            buildah_mount_out_buff
        ])
        buildah_mount_command = buildah_unshare_command.bake("buildah", "mount")
        buildah_mount_command(
            container_id,
            _out=buildah_mount_out_callback,
            _err=sys.stderr,
            _tee='err'
        )
        mount_path = buildah_mount_out_buff.getvalue().rstrip()
    except sh.ErrorReturnCode as error:
        raise RuntimeError(
            f'Error mounting container ({container_id}): {error}'
        ) from error

    return mount_path

def determine_container_image_build_tag_info(
    image_version,
    organization,
    application_name,
    service_name
):
    """Determines the full and short build tags for a new container image.

    Parameters
    ----------
    image_version : str
        A given image version. If none given, latest will be used.
    organization : str
        Organization the container image belongs to.
    application_name : str
        Application the container image belongs to.
    service_name : str
        Service the container image implements.

    Returns
    -------
    str, str, str, str, str
        First result is the full build tag, including registry URI.
        Second result is the short build tag, as in no registry URI.
        Third result is the image registry uri.
        Forth result is the image repository name.
        Fifth result is the used image version.

    """
    if image_version is None:
        image_version = 'latest'
        print('No image tag version found in metadata. Using latest')
    image_registry_uri = 'localhost'
    image_registry_organization = organization
    image_repository = f"{application_name}-{service_name}"
    build_short_tag = f"{image_registry_organization}/{image_repository}:{image_version}"
    build_full_tag = f"{image_registry_uri}/{build_short_tag}"

    return build_full_tag, build_short_tag, image_registry_uri, image_repository, image_version
