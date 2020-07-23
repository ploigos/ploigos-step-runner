"""
Step Implementer for the create-container-image step for Buildah.
"""
import os
import sys
import sh
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
    StepImplementer for the create-container-image step for Buildah.

    Raises
    ------
    ValueError
        If image specification file does not exist
        If tag is not specified (not defaulted)
    RuntimeError
        buildah command fails for any reason
    """

    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, DEFAULT_ARGS)

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

        for config_name in DEFAULT_ARGS:
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
            raise ValueError('Image specification file does not exist in location: '
                             + image_spec_file_location)

        buildah_bud = sh.buildah.bake("bud")  # pylint: disable=no-member

        try:
            print(buildah_bud(
                '--format=' + runtime_step_config['format'],
                '--tls-verify=' + runtime_step_config['tlsverify'],
                '--layers', '-f', image_spec_file,
                '-t', tag,
                context,
                _out=sys.stdout
            ))
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Issue invoking buildah bud  with given image '
                               'specification file (' + image_spec_file + ')')

        results = {
            'image_tag' : tag
        }

        if 'image_tar_file' in runtime_step_config and runtime_step_config['image_tar_file']:

            image_tar_file = runtime_step_config['image_tar_file']
            rm_f = sh.rm.bake("-f") # pylint: disable=no-member
            print(rm_f(image_tar_file))

            buildah_push = sh.buildah.bake("push") # pylint: disable=no-member
            try:
                print(buildah_push(
                    tag,
                    "docker-archive:" + image_tar_file,
                    _out=sys.stdout
                ))
            except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
                raise RuntimeError('Issue invoking buildah push to tar file ' + image_tar_file)

            results.update({'image_tar_file' : image_tar_file})

        return results

# register step implementer
TSSCFactory.register_step_implementer(Buildah, True)
