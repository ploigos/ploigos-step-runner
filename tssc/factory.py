"""
Factory for creating TSSC workflow and running steps.
"""

from .config import TSSCConfig
from .exceptions import TSSCException

_IS_DEFAULT_KEY = 'is_default'
_CLAZZ_KEY = 'clazz'

class TSSCFactory:
    """
    Enables the running of arbitrary TSSC steps via TSSC step implementers.

    Parameters
    ----------
    config : TSSCConfig, dict, list, str (file or directory)
        A TSSCConfig object,
        a dictionary that is a valid TSSC configuration,
        a string that is a path to a YAML or JSON file that is
        a valid TSSC configuration,
        a string that is a path to a directory containing one or more
        files that are valid YAML or JSON files that are valid
        configurations,
        or a list of any of the former.
    results_dir_path : str, optional
        Path to the folder for steps to write their results to
        Default: tssc-results
    results_file_name : str, optional
        Path to the file for steps to write their results to
        Default: tssc-results.yml
    work_dir_path : str, optional
        Path to the working folder for step_implementers for runtime files
        Default: tssc-working

    Raises
    ------
    ValueError
        If given config is not of expected type.
    AssertionError
        If given config contains any invalid TSSC configurations.
    """

    _step_implementers = {}

    def __init__(
            self,
            config,
            results_dir_path='tssc-results', \
            results_file_name='tssc-results.yml', \
            work_dir_path='tssc-working'):

        if isinstance(config, TSSCConfig):
            self.__config = config
        else:
            self.__config = TSSCConfig(config)

        self.results_dir_path = results_dir_path
        self.results_file_name = results_file_name
        self.work_dir_path = work_dir_path

    @staticmethod
    def register_step_implementer(implementer_class, is_default=False):
        """
        Register a Step Implementer.

        Parameters
        ----------
        implementer_class : class
            Class implimenting the step.
        is_default : bool, optional
            True if this should be the default implementer for this step, False other wise.
            If more then one step implementer is registered as the default for for the
            same step then the last one to register will win and be the default.
        """

        step_name = implementer_class.step_name()
        if step_name not in TSSCFactory._step_implementers:
            TSSCFactory._step_implementers[step_name] = {}

        # if this is the default, unset any other implimenters of this step as default
        # NOTE: last one to register as default wins, deal with it
        if is_default:
            for step_implementer in \
                    TSSCFactory._step_implementers[step_name].values():
                step_implementer[_IS_DEFAULT_KEY] = False

        TSSCFactory._step_implementers[step_name][implementer_class.__name__] = {
            _CLAZZ_KEY: implementer_class,
            _IS_DEFAULT_KEY: is_default
        }

    @property
    def config(self):
        """
        Returns
        -------
        TSSCConfig
            Configuration used by this factory.
        """
        return self.__config

    def run_step(self, step_name, environment=None):
        """
        Call the given step.

        Parameters
        ----------
        step_name : str
            TSSC step to run.
        environment : str, optional
            Name of the environment the step is being run in. Used to determine environment
            specific global defaults and step configuration.

        Raises
        ------
        TSSCException
            If no StepImplementers have been registered for the given step_name
            If no specific StepImplementer name specified in sub step config
                and no default StepImplementer registered for given step_name.
            If no StepImplementer registered for given step with given implementer name.
        """

        sub_step_configs = self.config.get_sub_step_configs(step_name)
        assert len(sub_step_configs) != 0, \
            f"Can not run step ({step_name}) because no step configuration provided."

        assert step_name in TSSCFactory._step_implementers, \
            f"No implementers registered for step ({step_name})."
        step_implementers = TSSCFactory._step_implementers[step_name]
        for sub_step_config in sub_step_configs:
            sub_step_implementer_name = sub_step_config.sub_step_implementer_name

            if sub_step_implementer_name in step_implementers:
                # create the StepImplementer instance
                sub_step = step_implementers[sub_step_implementer_name][_CLAZZ_KEY](
                    results_dir_path=self.results_dir_path,
                    results_file_name=self.results_file_name,
                    work_dir_path=self.work_dir_path,
                    config=sub_step_config,
                    environment=environment
                )

                # run the step
                sub_step.run_step()
            else:
                raise TSSCException(
                    'No StepImplementer for step'
                    + ' (' + step_name + ')'
                    + ' with TSSC config specified implementer name'
                    + ' (' + sub_step_implementer_name + ')'
                )
