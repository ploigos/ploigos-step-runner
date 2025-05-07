"""Shared utils for gradle operations.
"""

import re
import sys
import os
from io import StringIO

import sh
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback


class GradleGroovyParserException(Exception):
    """An exception dedicated to gradle's groovy DSL parsing.

    Parameters
    ----------
    file_name : str
        Path to the file that is being parsed.
    message : str, 
        The message detailing the exception.

    Returns
    -------
    Str
        String with the file name and message detailing the exception.
    """
    def __init__(self, file_name, message):
        self.file_name = file_name
        self.message = message

    def __str__(self):
        return "%s file: %s" % (self.file_name, self.message)


class GradleGroovyParser:
    """A gradle groovy build file parser. 

    Parameters
    ----------
    file_name : str
        Path to the gradle build file.

    Raises
    ------
    FileNotFoundError
        Unable to find gradle build file.    
    OSError
        Unable to open gradle build file.

    Returns
    -------
    Bool
        True if step completed successfully
        False if step returned an error message

    """
    file_name = ""
    raw_file = None

    def __init__(self, file_name):
        self.file_name = file_name
        with open(file_name, encoding='utf-8') as f:
            self.raw_file = f.read()


    def get_version(self):
        """Gets the project version from a gradle groovy build file.

        Returns
        -------
        str
            Version of the project. If no version is found an empty string is returned.

        Raises
        ------
        GradleGroovyParserException
            If multiple project versions are found in the build file.
        """
        version = None
        tokens = re.findall("^[ \t]*version[ \t]+[\'\"](.+)[\'\"][ \t]*$(?![^{]*})", self.raw_file, re.MULTILINE)
        if len(tokens) == 1:
            version = tokens[0].strip()
        elif len(tokens) > 1:

            raise GradleGroovyParserException(self.file_name, "More than one version found. " + str(tokens) )
        return version


def run_gradle( #pylint: disable=too-many-arguments, too-many-locals
    gradle_output_file_path,
    build_file,
    tasks,
    additional_arguments=None,

    console_plain=True

):
    """Runs gradle using the given configuration.

    Parameters
    ----------
    gradle_output_file_path : str
        Path to file containing the gradle stdout and stderr output.
    build_file : str (path)
        build file used when executing gradle.
    tasks : [str]
        List of gradle tasks to execute.
    additional_arguments : [str]
        List of additional arguments to use.
    console_plain : boolean
        `True` use old append style log output.
        `False` use new fancy screen redraw log output.\
    

    Returns
    -------
    str
        Standard Out from running gradle.

    Raises
    ------
    StepRunnerException
        If gradle returns a none 0 exit code.
    """


    if not isinstance(tasks, list):
        tasks = [tasks]

    # create console plain argument
    console_plain_argument = None
    if console_plain:
        console_plain_argument = '--console=plain'


    if not additional_arguments:
        additional_arguments = []


    # run gradle
    gradle_output_buff = StringIO()
    try:
        with open(gradle_output_file_path, 'w', encoding='utf-8') as gradle_output_file:
            out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stdout,
                gradle_output_file,
                gradle_output_buff
            ])
            err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                sys.stderr,
                gradle_output_file
            ])

            sh.gradle( # pylint: disable=no-member
                '-b', build_file,
                console_plain_argument,
                *additional_arguments,
                tasks,
                _out=out_callback,
                _err=err_callback
            )
    except sh.ErrorReturnCode as error:
        raise StepRunnerException(
            f"Error running gradle. {error}"
        ) from error

    # remove ansi escape charaters from output before returning
    gradle_output = gradle_output_buff.getvalue().rstrip()
    gradle_output_stripped_ansi = re.compile(r'\x1b[^m]*m').sub('', gradle_output)

    return gradle_output_stripped_ansi


def get_plugin_configuration_values(
    plugin_name,
    configuration_key,
    work_dir_path,
    build_file,
    profiles=None,
    phases_and_goals=None,
    require_phase_execution_config=None
): # pylint: disable=too-many-arguments
    """Gets the value(s) of a given configuration key for a given gradle plugin.
    """

    configuration_values = {'build': None, '/tmp/gradle.build': None}

    print(plugin_name)
    print(configuration_key)
    print(work_dir_path)
    print(build_file)
    print(profiles)
    print(phases_and_goals)
    print(require_phase_execution_config)

    configuration_values = list(set(configuration_values))
    configuration_values.sort()
    return configuration_values

def get_plugin_configuration_absolute_path_values(
    plugin_name,
    configuration_key,
    work_dir_path,
    build_file,
    profiles=None,
    phases_and_goals=None,
    require_phase_execution_config=None
): # pylint: disable=too-many-arguments
    """Gets the value(s) of a given configuration key for a given gradle plugin and converts
    them to absolute paths (if they arn't already), if they were relative paths, assumes,
    relative to the given build.gradle file.
    """

    absolute_path_config_values = []

    if plugin_name is None:
        raise RuntimeError(
            f"Expected gradle plugin ({plugin_name}) not found."
        )

    config_values = get_plugin_configuration_values(
        plugin_name=plugin_name,
        configuration_key=configuration_key,
        work_dir_path=work_dir_path,
        build_file=build_file,
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
                    os.path.dirname(os.path.abspath(build_file)),
                    config_value
                ))

    return absolute_path_config_values
