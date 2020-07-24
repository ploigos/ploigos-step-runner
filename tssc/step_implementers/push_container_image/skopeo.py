"""Step Implementer for the create-container-image step for Skopeo.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default | Description
|-------------------|-----------|---------|-----------
| `TODO`            | True      |         |

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

| Step Name | Result Key | Description
|-----------|------------|------------
| `TODO`    | `TODO`     | TODO

Results
-------

Results output by this step.

| Result Key | Description
|------------|------------
| `TODO`     | TODO


**Example**

    'tssc-results': {
        'TODO': {
            'TODO': ''
        }
    }
"""
import sys
import sh
from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {
    'src-tls-verify': 'true',
    'dest-tls-verify': 'true',
}

REQUIRED_ARGS = {
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

    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, DEFAULT_ARGS)

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

        all_required_args = {**DEFAULT_ARGS, **REQUIRED_ARGS}

        for config_name in all_required_args:
            if config_name not in step_config or not step_config[config_name]:
                raise ValueError('Key (' + config_name + ') must have non-empty value in the step '
                                 'configuration')

    def _run_step(self, runtime_step_config):

        version = "latest"
        if(self.get_step_results('generate-metadata') and \
          self.get_step_results('generate-metadata').get('image-tag')):
            version = self.get_step_results('generate-metadata')['image-tag']
        else:
            print('No version found in metadata. Using latest')

        image_tar_file = ''
        if(self.get_step_results(DefaultSteps.CREATE_CONTAINER_IMAGE) and \
          self.get_step_results(DefaultSteps.CREATE_CONTAINER_IMAGE).get('image_tar_file')):
            image_tar_file = self.\
            get_step_results(DefaultSteps.CREATE_CONTAINER_IMAGE)['image_tar_file']
        else:
            raise RuntimeError('Missing image tar file from ' + DefaultSteps.CREATE_CONTAINER_IMAGE)

        destination_with_version = runtime_step_config['destination'] + ':' + (version).lower()
        try:
            print(
                sh.skopeo.copy( #pylint: disable=no-member
                    '--src-tls-verify=' + runtime_step_config['src-tls-verify'],
                    '--dest-tls-verify=' + runtime_step_config['dest-tls-verify'],
                    'docker-archive:' + image_tar_file,
                    destination_with_version, _out=sys.stdout
                )
            )
        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking skopeo: {error}'.format(error=error))

        results = {
            'image_tag' : destination_with_version
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(Skopeo, True)
