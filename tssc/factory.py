"""
Factory for creating TSSC workflow and running steps.
"""
from .exceptions import TSSCException

_TSSC_CONFIG_KEY = 'tssc-config'
_IS_DEFAULT_KEY = 'is_default'
_CLAZZ_KEY = 'clazz'
_IMPLEMENTER_KEY = 'implementer'
_SUB_STEP_CONFIG_KEY = 'config'

class TSSCFactory:
    """
    Enables the running of arbitrary TSSC steps via TSSC step implementers.

    Parameters
    ----------
    config : dict
        TSSC configuration represented as a dictionary with a key of 'tssc-config'
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
        If given config does not contain 'tssc-config' key
    """
    _step_implementers = {}

    def __init__(self, config, results_dir_path='tssc-results', \
            results_file_name='tssc-results.yml', \
            work_dir_path='tssc-working'):
        if _TSSC_CONFIG_KEY in config:
            self.config = config[_TSSC_CONFIG_KEY]
        else:
            raise ValueError('config must contain key: ' + _TSSC_CONFIG_KEY)

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

    def run_step(self, step_name, runtime_step_config=None): # pylint: disable=too-many-branches
        """
        Call the given step.

        Parameters
        ----------
        step_name : str
            TSSC step to run.
        runtime_step_config
            TODO

        Raises
        ------
        TSSCException
            If no StepImplementers have been registered for the given step_name
            If no specific StepImplementer name specified in sub step config
                and no default StepImplementer registered for given step_name.
            If no StepImplementer registered for given step with given implementer name.
        """

        if not runtime_step_config:
            runtime_step_config = {}

        # verify that there is registered implementers for the given step
        if not step_name in TSSCFactory._step_implementers or \
                not TSSCFactory._step_implementers[step_name]:
            raise TSSCException('No implementers registered for step: ' + step_name)

        step_implementers = TSSCFactory._step_implementers[step_name]

        global_step_config_defaults = {}
        if 'global-defaults' in self.config:
            global_step_config_defaults = self.config['global-defaults']
        # get step configuration if there is any
        step_config = {}
        if step_name in self.config:
            step_config = self.config[step_name]
            if isinstance(step_config, dict):
                step_config = [step_config]
            for sub_step in step_config:
                sub_step_implementer_name = sub_step[_IMPLEMENTER_KEY]

                if sub_step_implementer_name in step_implementers:
                    if _SUB_STEP_CONFIG_KEY in sub_step:
                        sub_step_config = sub_step[_SUB_STEP_CONFIG_KEY]
                    else:
                        sub_step_config = {}
                    # create the StepImplementer instance
                    sub_step = step_implementers[sub_step_implementer_name][_CLAZZ_KEY](
                        sub_step_config,
                        self.results_dir_path,
                        self.results_file_name,
                        self.work_dir_path
                    )
                    sub_step.run_step(global_step_config_defaults, **runtime_step_config)
                else:
                    raise TSSCException(
                        'No StepImplementer for step'
                        + ' (' + step_name + ')'
                        + ' with TSSC config specified implementer name'
                        + ' (' + sub_step_implementer_name + ')'
                    )

        else:
            default_step_implementer = None
            for sub_step_implementer_name, step_implementer_config in step_implementers.items():
                if step_implementer_config[_IS_DEFAULT_KEY]:
                    default_step_implementer = step_implementer_config

            if default_step_implementer:
                # create the default StepImplementer instance
                sub_step = default_step_implementer[_CLAZZ_KEY](
                    {},
                    self.results_dir_path,
                    self.results_file_name,
                    self.work_dir_path
                )
                sub_step.run_step(global_step_config_defaults, **runtime_step_config)
            else:
                raise TSSCException(
                    'No implimenter specified for step'
                    + '(' + step_name + ')'
                    + ' in config'
                    + '(' + str(self.config) + ')'
                    + ' and no default step implementer registered in step implimenters'
                    + '(' + str(step_implementers) + ')'
                )
