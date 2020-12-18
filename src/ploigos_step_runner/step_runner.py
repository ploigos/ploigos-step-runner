"""Constructs a given named StepImplementer using a given configuration, and runs it.
"""
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.config.config import Config
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.reflection import import_and_get_class


class StepRunner:
    """Enables the running of arbitrary Ploigos steps via StepImplementers.

    Parameters
    ----------
    config : Config, dict, list, str (file or directory)
        A Config object,
        or a dictionary that is a valid step runner configuration,
        or a string that is a path to a YAML or JSON file that is
        a valid step runner configuration,
        or a string that is a path to a directory containing one or more
        files that are valid YAML or JSON files that are valid
        configurations,
        or a list of any of the former.
    results_dir_path : str, optional
        Path to the folder for steps to write their results to
        Default: step-runner-results
    results_file_name : str, optional
        Path to the file for steps to write their results to
        Default: step-runner-results.yml
    work_dir_path : str, optional
        Path to the working folder for step_implementers for runtime files
        Default: step-runner-working

    Raises
    ------
    ValueError
        If given config is not of expected type.
    AssertionError
        If given config contains any invalid configurations.

    Returns
    -------
    Bool
        True if step completed successfully
        False if step returned an error message
    """

    __DEFAULT_MODULE = 'ploigos_step_runner.step_implementers'

    def __init__(
            self,
            config,
            results_dir_path='step-runner-results',
            results_file_name='step-runner-results.yml',
            work_dir_path='step-runner-working'):

        if isinstance(config, Config):
            self.__config = config
        else:
            self.__config = Config(config)

        self.results_dir_path = results_dir_path
        self.results_file_name = results_file_name
        self.work_dir_path = work_dir_path

    @property
    def config(self):
        """
        Returns
        -------
        Config
            Configuration used by this factory.
        """
        return self.__config

    def run_step(self, step_name, environment=None):
        """
        Call the given step.

        Parameters
        ----------
        step_name : str
            Ploigos step to run.
        environment : str, optional
            Name of the environment the step is being run in. Used to determine environment
            specific global defaults and step configuration.

        Raises
        ------
        # todo: doc needs to be updated
        StepRunnerException
            If no StepImplementers have been registered for the given step_name
            If no specific StepImplementer name specified in sub step config
                and no default StepImplementer registered for given step_name.
            If no StepImplementer registered for given step with given implementer name.
        Returns
        -------
        Bool
           True if step completed successfully
           False if step returned an error message
        """

        sub_step_configs = self.config.get_sub_step_configs(step_name)
        assert len(sub_step_configs) != 0, \
            f"Can not run step ({step_name}) because no step configuration provided."

        # for each sub step in the step config get the step implementer and run it
        for sub_step_config in sub_step_configs:
            sub_step_implementer_name = sub_step_config.sub_step_implementer_name

            step_implementer_class = StepRunner.__get_step_implementer_class(
                step_name,
                sub_step_implementer_name)

            # create the StepImplementer instance
            sub_step = step_implementer_class(
                results_dir_path=self.results_dir_path,
                results_file_name=self.results_file_name,
                work_dir_path=self.work_dir_path,
                config=sub_step_config,
                environment=environment
            )

            # run the step
            if not sub_step.run_step():
                return False

        return True

    @staticmethod
    def __get_step_implementer_class(step_name, step_implementer_name):
        """Given a step name and a step implementer name dynamically loads the Class.

        Parameters
        ----------
        step_name : str
            Name of the step to load the given step implementer for.
            This is only used if the given step_implementer_name does not include
            a module path.
        step_implementer_name : str
            Either the short name of a StepImplementer class which will be dynamically
            loaded from the 'ploigos_step_runner.step_implementers.{step_name}' module or
            A class name that includes a dot seperated module name to load the Class from.

        Returns
        -------
        StepImplementer
            Dynamically loaded subclass of StepImplementer for given step name with
            given step implementer name.

        Raises
        ------
        StepRunnerException
            If could not find class to load
            If loaded class is not a subclass of StepImplementer
        """
        parts = step_implementer_name.split('.')
        class_name = parts.pop()
        module_name = '.'.join(parts)

        if not module_name:
            step_module_part = step_name.replace('-', '_')
            module_name = f"{StepRunner.__DEFAULT_MODULE}.{step_module_part}"

        clazz = import_and_get_class(module_name, class_name)
        if not clazz:
            raise StepRunnerException(
                f"Could not dynamically load step ({step_name}) step implementer" +
                f" ({step_implementer_name}) from module ({module_name})" +
                f" with class name ({class_name})"
            )
        if not issubclass(clazz, StepImplementer):
            raise StepRunnerException(
                f"Step ({step_name}) is configured to use step implementer" +
                f" ({step_implementer_name}) from module ({module_name}) with" +
                f" class name ({class_name}), and dynamically loads as class ({clazz})" +
                f" which is not a subclass of required parent class ({StepImplementer}).")

        return clazz
