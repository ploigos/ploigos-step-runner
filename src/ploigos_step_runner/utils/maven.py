"""Shared utils for maven operations.
"""

import xml.etree.ElementTree as ET

import sh
from ploigos_step_runner.exceptions import StepRunnerException


def generate_maven_settings(working_dir, maven_servers, maven_repositories, maven_mirrors):
    """
    Generates and returns a settings.xml file from the inputs it is provided.

    Parameters
    ----------
    maven_servers:
        Dictionary of id, username, password
    maven_repositories:
        Dictionary of id, url, snapshots, releases
    maven_mirrors:
        Dictionary of id, url, mirror_of

    Raises
    ------
    ValueError
        If the given file can not be parsed as YAML or JSON.

    Returns
    -------
    Str
        The path to the settings.xml that was generated.
    """

    root = ET.Element('settings')
    add_maven_servers(root, maven_servers)
    add_maven_repositories(root, maven_repositories)
    add_maven_mirrors(root, maven_mirrors)

    tree = ET.ElementTree(root)

    settings_path = working_dir + '/settings.xml'
    with open(settings_path, 'wb') as file:
        tree.write(file)

    return settings_path

def add_maven_servers(parent_element, maven_servers):
    """Adds <servers> element to parent element and creates <server> elements for each given
    maven server.

    Parameters
    ----------
    parent_element : ET.Element
        Parent element to add the <servers> element too.

    maven_servers : (dict, list)
        List of dicts or dicts of dicts to create <server> elements for.

    Raises
    ------
    AssertionError
        * if username given without password or password without username
        * if no id given
    """

    if maven_servers is None:
        return

    assert isinstance(maven_servers, (dict, list))

    servers_element = ET.Element('servers')
    parent_element.append(servers_element)

    if isinstance(maven_servers, dict):
        for maven_server_key, maven_server_conf in maven_servers.items():
            assert \
                ( \
                    ('username' in maven_server_conf) \
                    and \
                    ('password' in maven_server_conf) \
                ) \
                or \
                ( \
                    ('username' not in maven_server_conf) \
                    and \
                    ('password' not in maven_server_conf) \
                ), \
                f"Configuration for maven server ({maven_server_key})" \
                f" must specify both 'username' and 'password' or neither: {maven_server_conf}"

            # if id is key in the dict then use that for the maven server id
            # else use the dict key for the maven server conf as the maven server id
            if 'id' in maven_server_conf:
                maven_server_id = maven_server_conf['id']
            else:
                maven_server_id = maven_server_key

            add_maven_server(
                parent_element=servers_element,
                maven_server_id=maven_server_id,
                maven_server_username=maven_server_conf.get('username'),
                maven_server_password=maven_server_conf.get('password')
            )
    elif isinstance(maven_servers, list):
        for maven_server_conf in maven_servers:
            assert 'id' in maven_server_conf, \
                "Configuration for maven servers" \
                f" must specify a 'id': {maven_server_conf}"

            assert \
                ( \
                    ('username' in maven_server_conf) \
                    and \
                    ('password' in maven_server_conf) \
                ) \
                or \
                ( \
                    ('username' not in maven_server_conf) \
                    and \
                    ('password' not in maven_server_conf) \
                ), \
                "Configuration for maven servers" \
                f" must specify both 'username' and 'password' or neither: {maven_server_conf}"

            maven_server_id = maven_server_conf['id']

            add_maven_server(
                parent_element=servers_element,
                maven_server_id=maven_server_id,
                maven_server_username=maven_server_conf.get('username'),
                maven_server_password=maven_server_conf.get('password')
            )

def add_maven_server(
    parent_element,
    maven_server_id,
    maven_server_username=None,
    maven_server_password=None
):
    """Adds a <server> element to the given parent element.

    Parameters
    ----------
    parent_element : ET.Element
        The parent element to append the new server too.

    maven_server_id : str
        ID of the maven server to add.

    maven_server_username : str, optional
        Username for the maven server to add.
        Only used if maven_server_password also provided.

    maven_server_password : str, optional
        Password for the maven server to add.
        Only used if maven_server_username is provided.
    """
    server_element = ET.Element('server')
    parent_element.append(server_element)
    server_id = ET.SubElement(server_element, 'id')
    server_id.text = maven_server_id
    if maven_server_username and maven_server_password:
        server_username = ET.SubElement(server_element, 'username')
        server_username.text = maven_server_username
        server_password = ET.SubElement(server_element, 'password')
        server_password.text = maven_server_password

def add_maven_repositories(parent_element, maven_repositories): # pylint: disable=invalid-name
    """Adds <repositories> element to parent element and child <repository> element for each
    given maven repository.

    Parameters
    ----------
    parent_element : ET.Element
        Parent element to add the <repositories> element to.

    maven_repositories : (dict, list)
        List of dicts or dicts of dicts to create <repository> elements for.

    Raises
    ------
    AssertionError
        * id not specified
        * url not specified
    """

    if maven_repositories is None:
        return

    assert isinstance(maven_repositories, (dict, list))

    profiles_element = ET.Element('profiles')
    parent_element.append(profiles_element)
    profile_element = ET.Element('profile')
    profiles_element.append(profile_element)
    repositories_element = ET.Element('repositories')
    profile_element.append(repositories_element)

    if isinstance(maven_repositories, dict):
        for maven_repository_key, maven_repository_conf in maven_repositories.items():
            assert 'url' in maven_repository_conf, \
                f"Configuration for maven repository ({maven_repository_key})" \
                f" must specify a 'url': {maven_repository_conf}"

            # if id is key in the dict then use that for the maven repository id
            # else use the dict key for the maven server conf as the maven server id
            if 'id' in maven_repository_conf:
                repository_id = maven_repository_conf['id']
            else:
                repository_id = maven_repository_key

            repository_url = maven_repository_conf['url']
            releases_enabled = maven_repository_conf.get('releases')
            snapshots_enabled = maven_repository_conf.get('snapshots')

            add_maven_repository(
                parent_element=repositories_element,
                repository_id=repository_id,
                repository_url=repository_url,
                releases_enabled=releases_enabled,
                snapshots_enabled=snapshots_enabled
            )
    elif isinstance(maven_repositories, list):
        for maven_repository_conf in maven_repositories:
            assert 'id' in maven_repository_conf, \
                "Configuration for maven repository" \
                f" must specify a 'id': {maven_repository_conf}"

            assert 'url' in maven_repository_conf, \
                "Configuration for maven repository" \
                f" must specify a 'url': {maven_repository_conf}"

            repository_id = maven_repository_conf['id']
            repository_url = maven_repository_conf['url']
            releases_enabled = maven_repository_conf.get('releases')
            snapshots_enabled = maven_repository_conf.get('snapshots')

            add_maven_repository(
                parent_element=repositories_element,
                repository_id=repository_id,
                repository_url=repository_url,
                releases_enabled=releases_enabled,
                snapshots_enabled=snapshots_enabled
            )

def add_maven_repository(
    parent_element,
    repository_id,
    repository_url,
    releases_enabled=None,
    snapshots_enabled=None
):
    """Add a <repository> element to the given parent element

    Parameters
    ----------
    parent_element : ET.Element
        Parent elemtnt to add the <repository> element to.

    repository_id : str
        Value for the <id> element

    repository_url : str
        Value for the <url> element

    releases_enabled : (str, bool), optional
        Value for <releases><enabled>{snapshots_enabled}</enabled></releases>

    snapshots_enabled : (str, bool), optional
        Value for <snapshots><enabled>{snapshots_enabled}</enabled></snapshots>

    """
    repository_element = ET.Element('repository')
    parent_element.append(repository_element)

    repository_id_element = ET.SubElement(repository_element, 'id')
    repository_id_element.text = repository_id

    repository_url_element = ET.SubElement(repository_element, 'url')
    repository_url_element.text = repository_url

    if releases_enabled is not None:
        repository_releases = ET.SubElement(repository_element, 'releases')
        repository_releases_enabled = ET.SubElement(repository_releases, 'enabled')
        repository_releases_enabled.text = str(releases_enabled)

    if snapshots_enabled is not None:
        repository_snapshots = ET.SubElement(repository_element, 'snapshots')
        repository_snapshots_enabled = ET.SubElement(repository_snapshots, 'enabled')
        repository_snapshots_enabled.text = str(snapshots_enabled)

def add_maven_mirrors(parent_element, maven_mirrors):
    """Add <mirror> element for given maven mirror to <mirrors> element to given parent element.

    Parameters
    ----------
    parent_element : ET.Element
        Parent element to add <mirrors> element to.

    maven_mirrors : (dict, list)
        List of dicts or dicts of dicts of maven mirror configurations.

    Raises
    ------
    AssertionError
        * if maven mirror id not given
        * if maven mirror url not given
        * if maven mirror mirror-of not given
    """

    if maven_mirrors is None:
        return

    assert isinstance(maven_mirrors, (dict, list))

    mirrors_element = ET.Element('mirrors')
    parent_element.append(mirrors_element)

    if isinstance(maven_mirrors, dict):
        for maven_mirror_key, maven_mirror_conf in maven_mirrors.items():
            assert 'url' in maven_mirror_conf, \
                f"Configuration for maven mirror ({maven_mirror_key})" \
                f" must specify a 'url': {maven_mirror_conf}"
            assert 'mirror-of' in maven_mirror_conf, \
                f"Configuration for maven mirror ({maven_mirror_key})" \
                f" must specify a 'mirror-of': {maven_mirror_conf}"

            # if id is key in the dict then use that for the maven mirror id
            # else use the dict key for the maven mirror conf as the maven mirror id
            if 'id' in maven_mirror_conf:
                maven_mirror_id = maven_mirror_conf['id']
            else:
                maven_mirror_id = maven_mirror_key

            add_maven_mirror(
                parent_element=mirrors_element,
                maven_mirror_id=maven_mirror_id,
                maven_mirror_url=maven_mirror_conf['url'],
                maven_mirror_mirror_of=maven_mirror_conf['mirror-of']
            )
    elif isinstance(maven_mirrors, list):
        for maven_mirror_conf in maven_mirrors:
            assert 'id' in maven_mirror_conf, \
                "Configuration for maven mirror" \
                f" must specify a 'id': {maven_mirror_conf}"
            assert 'url' in maven_mirror_conf, \
                "Configuration for maven mirror" \
                f" must specify a 'url': {maven_mirror_conf}"
            assert 'mirror-of' in maven_mirror_conf, \
                "Configuration for maven mirror" \
                f" must specify a 'mirror-of': {maven_mirror_conf}"

            add_maven_mirror(
                parent_element=mirrors_element,
                maven_mirror_id=maven_mirror_conf['id'],
                maven_mirror_url=maven_mirror_conf['url'],
                maven_mirror_mirror_of=maven_mirror_conf['mirror-of']
            )

def add_maven_mirror(
    parent_element,
    maven_mirror_id,
    maven_mirror_url,
    maven_mirror_mirror_of
):
    """Adds a <mirror> element to given parent element.

    Parameters
    ----------
    parent_element : ElementTree.Element
        Parent element to add new <mirror> element to

    maven_mirror_id : str
        Value for <id> element.

    maven_mirror_url : str
        Value for <url> element.

    maven_mirror_mirror_of : str
        Value for <mirrorOf> element.

    """
    mirror_element = ET.Element('mirror')
    parent_element.append(mirror_element)

    mirror_id = ET.SubElement(mirror_element, 'id')
    mirror_id.text = maven_mirror_id

    mirror_url = ET.SubElement(mirror_element, 'url')
    mirror_url.text = maven_mirror_url

    mirror_mirror_of = ET.SubElement(mirror_element, 'mirrorOf')
    mirror_mirror_of.text = maven_mirror_mirror_of

def write_effective_pom(
    pom_file_path,
    output_path
):
    """Generates the effective pom for a given pom and writes it to a given directory

    Parameters
    ----------
    pom_file_path : str
        Path to pom file to render the effective pom for.
    output_path : str
        Path to write the effective pom to.

    See
    ---
    * https://maven.apache.org/plugins/maven-help-plugin/effective-pom-mojo.html

    Returns
    -------
    str
        Absolute path to the written effective pom generated from the given pom file path.

    Raises
    ------
    StepRunnerException
        If issue generating effective pom.
    """

    try:
        sh.mvn( # pylint: disable=no-member
            'help:effective-pom',
            f'-f={pom_file_path}',
            f'-Doutput={output_path}'
        )
    except sh.ErrorReturnCode as error:
        raise StepRunnerException(
            f"Error generating effective pom for '{pom_file_path}' to '{output_path}': {error}"
        ) from error

    return output_path
