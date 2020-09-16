"""Step Implementer for the create-container-image step for Skopeo.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default  | Description
|-------------------|-----------|----------|-----------
| `destination-url` | True      |          | Container image repository destination to push image
                                             to. o not include the `docker://` prefix as it will
                                             automatically be applied
| `src-tls-verify`  | True      | `'true'` | Whether to very TLS for source of image
| `dest-tls-verify` | True      | `'true'` | Whether to verify TLS for destination of image

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

| Step Name                | Result Key       | Description
|--------------------------|------------------|------------
| `generate-metadata`      | `image-tag`      | Tag to push image with
| `create-container-image` | `image-tar-file` | Local tar file of image to push

Results
-------

Results output by this step.

| Result Key  | Description
|-------------|------------
| `image-tag` | Pushed destination image tag

"""
import sys
import sh
from tssc import StepImplementer, DefaultSteps

DEFAULT_CONFIG = {
    'src-tls-verify': 'true',
    'dest-tls-verify': 'true',
}

REQUIRED_CONFIG_KEYS = [
    'destination-url',
    'src-tls-verify',
    'dest-tls-verify',
    'service-name',
    'application-name',
    'organization'
]

class Skopeo(StepImplementer):
    """
    StepImplementer for the push-container-image step for Skopeo.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

        Notes
        -----
        These are the lowest precedence configuration values.

        Returns
        -------
        dict
            Default values to use for step configuration values.
        """
        return DEFAULT_CONFIG

    @staticmethod
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.

        See Also
        --------
        _validate_runtime_step_config

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.
        """
        return REQUIRED_CONFIG_KEYS

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        dict
            Results of running this step.
        """
        version = "latest"
        if(self.get_step_results(DefaultSteps.GENERATE_METADATA) and \
          self.get_step_results(DefaultSteps.GENERATE_METADATA).get('image-tag')):
            version = self.get_step_results(DefaultSteps.GENERATE_METADATA)['image-tag']
        else:
            print('No version found in metadata. Using latest')

        application_name = self.get_config_value('application-name')
        service_name = self.get_config_value('service-name')
        organization = self.get_config_value('organization')

        image_tar_file = ''
        if(self.get_step_results(DefaultSteps.CREATE_CONTAINER_IMAGE) and \
          self.get_step_results(DefaultSteps.CREATE_CONTAINER_IMAGE).get('image-tar-file')):
            image_tar_file = self.\
            get_step_results(DefaultSteps.CREATE_CONTAINER_IMAGE)['image-tar-file']
        else:
            raise RuntimeError('Missing image tar file from ' + DefaultSteps.CREATE_CONTAINER_IMAGE)

        destination_with_version = self.get_config_value('destination-url') + '/' + organization + \
         '/' + application_name + '-' + service_name + ':' + (version).lower()
        try:
            sh.skopeo.copy( # pylint: disable=no-member
                '--src-tls-verify=' + str(self.get_config_value('src-tls-verify')),
                '--dest-tls-verify=' + str(self.get_config_value('dest-tls-verify')),
                'docker-archive:' + image_tar_file,
                'docker://' + destination_with_version,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking skopeo: {error}'.format(error=error)) from error

        results = {
            'image-tag' : destination_with_version,
            'image-version' : (version).lower(),
            'image-url' : self.get_config_value('destination-url')
        }

        return results
