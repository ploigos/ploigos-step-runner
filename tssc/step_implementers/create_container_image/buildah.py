"""
Step Implementer for the package step for Maven.
"""
import os
import subprocess

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {
    # Image specification file name
    'imagespecfile': 'Dockerfile',

    # Path to the image specification file
    'context': '.',

    # Verify TLS Certs?
    'tlsverify': 'true',

    # Format of the produced image
    'format': 'oci'

}

class Buildah(StepImplementer):
    """
    StepImplementer for the build container step for Buildah.

    Raises
    ------
    ValueError
        If image specification file does not exist
    """

    def __init__(self, config, results_file):
        super().__init__(config, results_file, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.CREATE_CONTAINER_IMAGE

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """
        print(step_config)

        for config_name in step_config:
            if config_name not in step_config or not step_config[config_name]:
                raise ValueError('Key (' + config_name + ') must have non-empty value in the step '
                    'configuration')

        if 'tag' not in step_config or not step_config['tag']:
            raise ValueError('Key (tag) must have non-empty value in the step configuration')

    def _run_step(self, runtime_step_config):

        context = runtime_step_config['context']
        image_spec_file = runtime_step_config['imagespecfile']
        image_spec_file_location = context + '/' + image_spec_file
        tag = runtime_step_config['tag']

        if not os.path.exists(image_spec_file_location):
            raise ValueError('Image specification file does not exist in location: ' \
            + image_spec_file_location)

        process_args = 'buildah bud' + \
            ' --format=' + runtime_step_config['format'] + \
            ' --tls-verify=' + runtime_step_config['tlsverify'] + \
            ' --layers -f ' + image_spec_file + \
            ' -t' + tag + \
            ' ' + context

        return_code = 1

        return_code = subprocess.call(process_args, shell=True)
        if return_code:
            raise ValueError('Issue invoking ' + str(process_args) + \
              ' with given image specification file (' + image_spec_file + ')')

        results = {
            'image_tag' : tag
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(Buildah, True)
