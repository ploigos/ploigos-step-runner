"""
Shared utils for maven deeds
"""

import xml.etree.ElementTree as ET

def generate_maven_settings(working_dir, maven_servers, maven_repositories, maven_mirrors):

    """
    Generates and returns a settings.xml file from the inputs it is provided.

    Parameters
    ----------
    :
    maven_servers:
        Dictionary of id, username, password
    maven_repositories:
        Dictionary of id, url, snapshots, releases
    maven_mirrors:
        Dictionary of id, url, mirror_of

    Returns
    -------
    dict
        Dictionary parsed from given YAML or JSON file

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
    generate_maven_servers(root, maven_servers)
    generate_maven_repositories(root, maven_repositories)
    generate_maven_mirrors(root, maven_mirrors)

    tree = ET.ElementTree(root)

    with open(working_dir + '/settings.xml', 'wb') as files:
        tree.write(files)

    settings_path = working_dir + '/settings.xml'

    return settings_path

def generate_maven_servers(ElementTree, maven_servers): # pylint: disable=invalid-name
    """
    Generates maven servers section of settings.xml
    """

    if maven_servers is not None:
        servers = ET.Element('servers')
        ElementTree.append(servers)
        for server in maven_servers:
            if server.get('id'):
                server_element = ET.Element('server')
                servers.append(server_element)
                server_id = ET.SubElement(server_element, 'id')
                server_id.text = server['id']
                if server.get('username') and server.get('password'):
                    server_username = ET.SubElement(server_element, 'username')
                    server_username.text = server['username']
                    server_password = ET.SubElement(server_element, 'password')
                    server_password.text = server['password']
                else:
                    if server.get('username') or server.get('password'):
                        raise ValueError('username and password are required for maven_servers.')
            else:
                raise ValueError('id is required for maven_servers.')

def generate_maven_repositories(ElementTree, maven_repositories): # pylint: disable=invalid-name
    """
    Generates maven repositories section of settings.xml
    """

    if maven_repositories is not None:
        profiles = ET.Element('profiles')
        ElementTree.append (profiles)
        profile = ET.Element('profile')
        profiles.append (profile)
        repositories = ET.Element('repositories')
        profile.append(repositories)

        for repository in maven_repositories:
            if repository.get('id') and repository.get('url'):
                repository_element = ET.Element('repository')
                repositories.append(repository_element)
                repository_id = ET.SubElement(repository_element, 'id')
                repository_id.text = repository['id']
                repository_url = ET.SubElement(repository_element, 'url')
                repository_url.text = repository['url']
                if repository.get('releases'):
                    repository_releases = ET.SubElement(repository_element, 'releases')
                    repository_releases_enabled = ET.SubElement(repository_releases, 'enabled')
                    repository_releases_enabled.text = repository['releases']
                if repository.get('snapshots'):
                    repository_snapshots = ET.SubElement(repository_element, 'snapshots')
                    repository_snapshots_enabled = ET.SubElement(repository_snapshots, 'enabled')
                    repository_snapshots_enabled.text = repository['snapshots']
            else:
                raise ValueError('id and url are required for maven_repositories.')

def generate_maven_mirrors(ElementTree, maven_mirrors): # pylint: disable=invalid-name
    """
    Generates maven mirrors section of settings.xml
    """

    if maven_mirrors is not None:
        mirrors = ET.Element('mirrors')
        ElementTree.append(mirrors)
        for mirror in maven_mirrors:
            if mirror.get('id') and mirror.get('url') and mirror.get('mirror-of'):
                mirror_element = ET.Element('mirror')
                mirrors.append(mirror_element)
                mirror_id = ET.SubElement(mirror_element, 'id')
                mirror_id.text = mirror['id']
                mirror_url = ET.SubElement(mirror_element, 'url')
                mirror_url.text = mirror['url']
                mirror_mirror_of = ET.SubElement(mirror_element, 'mirrorOf')
                mirror_mirror_of.text = mirror['mirror-of']
            else:
                raise ValueError('id, url and mirrorOf are required for maven_mirrors.')
