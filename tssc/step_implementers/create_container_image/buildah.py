"""Step Implementer for the create-container-image step for Buildah.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default        | Description
|-------------------|-----------|----------------|-----------
| `imagespecfile`   | True      | `'Dockerfile'` | TODO
| `context`         | True      | `'.'`          | TODO
| `tlsverify`       | True      | `'true'`       | TODO
| `format`          | True      | `'oci'`        | TODO

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

| Step Name | Result Key | Description
|-----------|------------|------------
| `TODO`    | `TODO`     | TODO

Results
-------

Results output by this step.

| Result Key       | Description
|------------------|------------
| `image_tag`      | TODO
| `image_tar_file` | TODO


** Example **

`image_tar_file` step configuration specified.

    'tssc-results': {
        'create-container-image': {
            'image_tag': '',
            'image_tar_file' : ''
        }
    }

"""
import os
import sys
import uuid
import sh
from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {
    # Image specification file name
    'imagespecfile': 'Dockerfile',

    # Parent path to the image specification file
    'context': '.',

    # Verify TLS Certs?
    'tlsverify': 'true',

    # Format of the produced image
    'format': 'oci'
}

REQUIRED_ARGS = {
    # Image destination, without version
    'destination' : None
}
class Buildah(StepImplementer):
    """
    StepImplementer for the create-container-image step for Buildah.

    Raises
    ------
    ValueError
        If image specification file does not exist
        If destination is not specified (not defaulted)
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

        if 'destination' not in step_config or not step_config['destination']:
            raise ValueError('Key (destination) must have non-empty value in the step '
                             'configuration')

    def _run_step(self, runtime_step_config):

        context = runtime_step_config['context']
        image_spec_file = runtime_step_config['imagespecfile']
        image_spec_file_location = context + '/' + image_spec_file
        destination = runtime_step_config['destination']

        if not os.path.exists(image_spec_file_location):
            raise ValueError('Image specification file does not exist in location: '
                             + image_spec_file_location)

        version = "latest"
        if(self.get_step_results('generate-metadata') and \
          self.get_step_results('generate-metadata').get('image-tag')):
            version = self.get_step_results('generate-metadata')['image-tag']
        else:
            print('No version found in metadata. Using latest')

        tag = destination + ':' + version

        try:
            print(sh.buildah.bud( #pylint: disable=no-member
                '--format=' + runtime_step_config['format'],
                '--tls-verify=' + runtime_step_config['tlsverify'],
                '--layers', '-f', image_spec_file,
                '-t', tag,
                context,
                _out=sys.stdout
            ))
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Issue invoking buildah bud with given image '
                               'specification file (' + image_spec_file + ')')

        image_tar_file = 'image-{guid}.tar'.format(guid=uuid.uuid4())

        try:
            print(
                sh.buildah.push( #pylint: disable=no-member
                    tag,
                    "docker-archive:" + image_tar_file,
                    _out=sys.stdout
                )
            )
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Issue invoking buildah push to tar file ' + image_tar_file)

        results = {
            'image_tag' : tag,
            'image_tar_file' : image_tar_file
        }


        return results

# register step implementer
TSSCFactory.register_step_implementer(Buildah, True)
