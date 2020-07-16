"""
Step Implementer for the create-container-image step for Buildah.
"""
import sh
from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {
    'src-tls-verify': 'true',
    'dest-tls-verify': 'true',
}

REQUIRED_ARGS = {
    'source': None,
    'destination': None
}

class Skopeo(StepImplementer):
    """
    StepImplementer for the push-container-image step for Skopeo.

    Raises
    ------
    ValueError
        If a required parameter is unspecified
    RuntimeError
        If skopeo command fails for any reason
    """

    def __init__(self, config, results_file):
        super().__init__(config, results_file, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.PUSH_CONTAINER_IMAGE

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """
        print(step_config)

        all_required_args = {}
        all_required_args.update(DEFAULT_ARGS)
        all_required_args.update(REQUIRED_ARGS)

        for config_name in all_required_args:
            if config_name not in step_config or not step_config[config_name]:
                raise ValueError('Key (' + config_name + ') must have non-empty value in the step '
                                 'configuration')

    def _run_step(self, runtime_step_config):

        version = "latest"
        try:
            version = self.current_results()['tssc-results']['generate-metadata']['image-tag']
        except KeyError:
            print('No version found in metadata. Using latest')

        destination = runtime_step_config['destination']
        skopeo_copy = sh.skopeo.bake("copy") # pylint: disable=no-member
        try:
            print(skopeo_copy(
                '--src-tls-verify=' + runtime_step_config['src-tls-verify'],
                '--dest-tls-verify=' + runtime_step_config['dest-tls-verify'],
                runtime_step_config['source'],
                destination + ':' + version))
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking skopeo')

        results = {
            'image_tag' : destination + ':' + version
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(Skopeo, True)
