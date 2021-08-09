"""Shared utils for maven operations.
"""
import os
import sys
import xml.etree.ElementTree as ET

import sh
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback
from ploigos_step_runner.utils.xml import (get_xml_element_by_path,
                                           get_xml_element_text_by_path)


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
    output_path,
    profiles=None
):
    """Generates the effective pom for a given pom and writes it to a given directory

    Parameters
    ----------
    pom_file_path : str
        Path to pom file to render the effective pom for.
    output_path : str
        Path to write the effective pom to.
    profiles : list
        Maven profiles to use when generating the effective pom.

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

    if not os.path.isabs(output_path):
        raise StepRunnerException(
            f"Given output path ({output_path}) is not absolute which will mean your output"
            f" file will actually end up being relative to the pom file ({pom_file_path}) rather"
            " than your expected root. Rather then handling this, just give this function an"
            " absolute path."
            " If you are a user seeing this, a programmer messed up somewhere, report an issue."
        )

    profiles_arguments = ""
    if profiles:
        if isinstance(profiles, str):
            profiles = [profiles]
        profiles_arguments = ['-P', f"{','.join(profiles)}"]

    try:
        sh.mvn( # pylint: disable=no-member
            'help:effective-pom',
            f'-f={pom_file_path}',
            f'-Doutput={output_path}',
            *profiles_arguments
        )
    except sh.ErrorReturnCode as error:
        raise StepRunnerException(
            f"Error generating effective pom for '{pom_file_path}' to '{output_path}': {error}"
        ) from error

    return output_path

def get_effective_pom(
    work_dir_path,
    pom_file,
    profiles
):
    """Writes the effective pom to a file if it does not already exist and returns the path.

    Parameters
    ----------
    work_dir_path : str
        Path to write the effective pom to if it does not already exist
    pom_file : str
        Path to pom file to create the effective pom for.
    profiles : [str]
        Profile(s) to use when generating the effective pom

    Returns
    -------
    str
        Path to the written effective pom generated from the 'pom-file' value.
    """
    effective_pom_path = os.path.join(work_dir_path, 'effective-pom.xml')

    if not os.path.exists(effective_pom_path):
        write_effective_pom(
            pom_file_path=pom_file,
            output_path=effective_pom_path,
            profiles=profiles
        )

    return effective_pom_path

def run_maven( #pylint: disable=too-many-arguments
    mvn_output_file_path,
    settings_file,
    pom_file,
    phases_and_goals,
    tls_verify=True,
    additional_arguments=None,
    profiles=None,
    no_transfer_progress=True
):
    """Runs maven using the given configuration.

    Parameters
    ----------
    mvn_output_file_path : str
        Path to file containing the maven stdout and stderr output.
    phases_and_goals : [str]
        List of maven phases and/or goals to execute.
    additional_arguments : [str]
        List of additional arguments to use.
    pom_file : str (path)
        pom used when executing maven.
    tls_verify : boolean
        Disables TLS Verification if set to False
    profiles : [str]
        List of maven profiles to use.
    no_transfer_progress : boolean
        `True` to suppress the transfer progress of packages maven downloads.
        `False` to have the transfer progress printed.\
        See https://maven.apache.org/ref/current/maven-embedder/cli.html
    settings_file : str (path)
        Maven settings file to use.

    Returns
    -------
    str
        Standard Out and Standard Error from running Maven.

    Raises
    ------
    StepRunnerException
        If maven returns a none 0 exit code.
    """

    if not isinstance(phases_and_goals, list):
        phases_and_goals = [phases_and_goals]

    # create profile argument
    profiles_arguments = ""
    if profiles:
        profiles_arguments = ['-P', f"{','.join(profiles)}"]

    # create no transfer progress argument
    no_transfer_progress_argument = None
    if no_transfer_progress:
        no_transfer_progress_argument = '--no-transfer-progress'

    # create tls arguments
    tls_arguments = []
    if not tls_verify:
        tls_arguments += [
            '-Dmaven.wagon.http.ssl.insecure=true',
            '-Dmaven.wagon.http.ssl.allowall=true',
            '-Dmaven.wagon.http.ssl.ignore.validity.dates=true',
        ]

    if not additional_arguments:
        additional_arguments = []

    # run maven
    try:
        with open(mvn_output_file_path, 'w', encoding='utf-8') as mvn_output_file:
            out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stdout,
                mvn_output_file
            ])
            err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stderr,
                mvn_output_file
            ])

            sh.mvn( # pylint: disable=no-member
                *phases_and_goals,
                '-f', pom_file,
                '-s', settings_file,
                *profiles_arguments,
                no_transfer_progress_argument,
                *tls_arguments,
                *additional_arguments,
                _out=out_callback,
                _err=err_callback
            )
    except sh.ErrorReturnCode as error:
        raise StepRunnerException(
            f"Error running maven. {error}"
        ) from error

def get_maven_plugin_xml_element_path(plugin_name):
    """Create XML element path for a given maven plugin.

    Parameters
    ----------
    plugin_name : str
        Maven plugin name to get the XML element path for

    Returns
    -------
    str
        XML element path for the given maven plugin.
    """
    return f'./mvn:build/mvn:plugins/mvn:plugin[mvn:artifactId="{plugin_name}"]'

def get_plugin_configuration_values(
    plugin_name,
    configuration_key,
    work_dir_path,
    pom_file,
    profiles=None,
    phases_and_goals=None,
    require_phase_execution_config=False
): # pylint: disable=too-many-arguments
    """Gets the value(s) of a given configuration key for a given maven plugin.

    Will create an effective pom out of the given pom so as to be able to inherit configuration
    from parent poms.

    Will search:
    * executions for given phase, return all matches
    * if no matching executions will search plugin non execution specific configuration

    Paramters
    ---------
    plugin_name : str
        Name of the maven plugin to get the configuration value(s) for.
    configuration_key : str
        Configuration key of the maven plugin to get the configuration value(s) for.
    work_dir_path : str
        A working path to use to write the effective pom to for searching.
    pom_file : str
        Maven pom file to create the effective pom for to then search for the plugin configuration.
    profiles : [str]
        List of maven profiles to activate when creating the effective pom to search.
    phases_and_goals : [str]
        List of phases and goals to search for specific plugin executions for for the configuration
        value(s).
    require_phase_execution_config : bool
        True if the found configuration must be in a plugin execution matching one of the given
        phases. False if the found configuration can be a default configuration.

    Raises
    ------
    RuntimeError
        If the given plugin can not be found in the effective pom.

    Returns
    -------
    [str]
        List of configuration values found, or empty list if none found.
    """
    # get effective pom
    effective_pom_file = get_effective_pom(
        work_dir_path=work_dir_path,
        pom_file=pom_file,
        profiles=profiles
    )

    # ensure plugin enabled
    plugin_xml_element_path = get_maven_plugin_xml_element_path(plugin_name)
    plugin = get_xml_element_by_path(
        effective_pom_file,
        xpath=plugin_xml_element_path,
        default_namespace='mvn'
    )
    if plugin is None:
        raise RuntimeError(
            f"Expected maven plugin ({plugin_name}) not found in "
            f" effective pom for given pom ({pom_file})."
        )

    # look for phase and/or goal specific plugin configuration
    configuration_values = []
    if phases_and_goals:
        for phase_or_goal in phases_and_goals:
            # look for phase specific plugin configuration
            # EX:
            #   <plugin>
            #     <groupId>org.apache.maven.plugins</groupId>
            #     <artifactId>maven-surefire-plugin</artifactId>
            #     <version>${surefire-plugin.version}</version>
            #     <configuration>
            #       <reportsDirectory>
            #         ${project.build.directory}/surefire-reports-unit-test
            #       </reportsDirectory>
            #     </configuration>
            #     <executions>
            #       <execution>
            #         <id>integration-tests</id>
            #         <phase>integration-test</phase> <!--NOTE: Matches on this-->
            #         <goals>
            #           <goal>test</goal>
            #         </goals>
            #         <configuration>
            #           <skipTests>${skipITs}</skipTests>
            #           <reportsDirectory>
            #             ${project.build.directory}/surefire-reports-uat <!--NOTE: selects this-->
            #           </reportsDirectory>
            #           <systemProperties>
            #             <java.util.logging.manager>
            #               org.jboss.logmanager.LogManager
            #             </java.util.logging.manager>
            #           </systemProperties>
            #           <includes>
            #             <include>**/*IT.*</include>
            #           </includes>
            #         </configuration>
            #       </execution>
            #     </executions>
            #   </plugin>
            phase_config = get_xml_element_text_by_path(
                effective_pom_file,
                xpath=f'{plugin_xml_element_path}/mvn:executions/' \
                    f'mvn:execution[mvn:phase="{phase_or_goal}"]/' \
                    f'mvn:configuration/mvn:{configuration_key}',
                default_namespace='mvn',
                find_all=True
            )
            if isinstance(phase_config, list):
                configuration_values += phase_config

            # look for goals specific plugin configuration
            # EX:
            #   <plugin>
            #     <groupId>org.apache.maven.plugins</groupId>
            #     <artifactId>maven-failsafe-plugin</artifactId>
            #     <version>2.22.2</version>
            #     <executions>
            #       <execution>
            #         <goals>
            #           <goal>integration-test</goal> <!--NOTE: Matches on this-->
            #           <goal>verify</goal>
            #         </goals>
            #         <configuration>
            #           <reportsDirectory> <!--NOTE: selects this-->
            #             ${project.build.directory}/failsafe-reports-execution
            #           </reportsDirectory>
            #         </configuration>
            #       </execution>
            #     </executions>
            #   </plugin>
            goal_config = get_xml_element_text_by_path(
                effective_pom_file,
                xpath=f'{plugin_xml_element_path}/mvn:executions/mvn:execution/' \
                    f'*[mvn:goal="{phase_or_goal}"]/../mvn:configuration/mvn:{configuration_key}',
                default_namespace='mvn',
                find_all=True
            )
            if isinstance(goal_config, list):
                configuration_values += goal_config

    # if didn't find any phase specific configuration, look for default configuration
    if not require_phase_execution_config and not configuration_values:
        default_config = get_xml_element_text_by_path(
            effective_pom_file,
            xpath=f'{plugin_xml_element_path}/mvn:configuration/mvn:{configuration_key}',
            default_namespace='mvn',
            find_all=True
        )
        if isinstance(default_config, list):
            configuration_values += default_config

    # de dup results and return
    configuration_values = list(set(configuration_values))
    configuration_values.sort()
    return configuration_values

def get_plugin_configuration_absolute_path_values(
    plugin_name,
    configuration_key,
    work_dir_path,
    pom_file,
    profiles=None,
    phases_and_goals=None,
    require_phase_execution_config=False
): # pylint: disable=too-many-arguments
    """Gets the value(s) of a given configuration key for a given maven plugin and converts
    them to absolute paths (if they arn't already), if they were relative paths, assumes,
    relative to the given pom file.

    Will create an effective pom out of the given pom so as to be able to inherit configuration
    from parent poms.

    Will search:
    * executions for given phase, return all matches
    * if no matching executions will search plugin non execution specific configuration

    Paramters
    ---------
    plugin_name : str
        Name of the maven plugin to get the configuration value(s) for.
    configuration_key : str
        Configuration key of the maven plugin to get the configuration value(s) for.
    work_dir_path : str
        A working path to use to write the effective pom to for searching.
    pom_file : str
        Maven pom file to create the effective pom for to then search for the plugin configuration.
    profiles : [str]
        List of maven profiles to activate when creating the effective pom to search.
    phases_and_goals : [str]
        List of phases and goals to search for specific plugin executions for for the configuration
        value(s).
    require_phase_execution_config : bool
        True if the found configuration must be in a plugin execution matching one of the given
        phases. False if the found configuration can be a default configuration.

    Raises
    ------
    RuntimeError
        If the given plugin can not be found in the effective pom.

    Returns
    -------
    [str]
        List of configuration values found, or empty list if none found.
    """
    absolute_path_config_values = []

    # get the configuration values
    config_values = get_plugin_configuration_values(
        plugin_name=plugin_name,
        configuration_key=configuration_key,
        work_dir_path=work_dir_path,
        pom_file=pom_file,
        profiles=profiles,
        phases_and_goals=phases_and_goals,
        require_phase_execution_config=require_phase_execution_config
    )

    # transform that configuration into absolute paths for consistency
    if config_values:
        for config_value in config_values:
            # if absolute path use as is
            # else if relative path assume its relative to the pom and calc absolute path
            if os.path.isabs(config_value):
                absolute_path_config_values.append(config_value)
            else:
                absolute_path_config_values.append(os.path.join(
                    os.path.dirname(os.path.abspath(pom_file)),
                    config_value
                ))

    return absolute_path_config_values
