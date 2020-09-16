"""Step Implementer for the create-container-image step for Buildah.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default        | Description
|-------------------|-----------|----------------|-----------
| `imagespecfile`   | True      | `'Dockerfile'` | File defining the container image
| `context`         | True      | `'.'`          | Context to build the container image in
| `tlsverify`       | True      | `'true'`       | Whether to verify TLS when pulling parent images
| `format`          | True      | `'oci'`        | format of the built image's manifest and metadata

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

| Step Name           | Result Key      | Description
|---------------------|-----------------|------------
| `generate-metadata` | `image-tag`     | Version to use when building the image

Results
-------

Results output by this step.

| Result Key       | Description
|------------------|------------
| `image-tag`      | The image ID to tag the built image with when pushing it to a local file
| `image-tar-file` | Path to the built container image as a tar file


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
import sh

from tssc import StepImplementer, DefaultSteps

DEFAULT_CONFIG = {
    # Image specification file name
    'imagespecfile': 'Dockerfile',

    # Parent path to the image specification file
    'context': '.',

    # Verify TLS Certs?
    'tlsverify': 'true',

    # Format of the produced image
    'format': 'oci'
}

REQUIRED_CONFIG_KEYS = [
    'imagespecfile',
    'context',
    'tlsverify',
    'format',
    'service-name',
    'application-name'
]

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
        context = self.get_config_value('context')
        image_spec_file = self.get_config_value('imagespecfile')
        image_spec_file_location = context + '/' + image_spec_file
        application_name = self.get_config_value('application-name')
        service_name = self.get_config_value('service-name')

        if not os.path.exists(image_spec_file_location):
            raise ValueError('Image specification file does not exist in location: '
                             + image_spec_file_location)

        if(self.get_step_results(DefaultSteps.GENERATE_METADATA) and \
          self.get_step_results(DefaultSteps.GENERATE_METADATA).get('image-tag')):
            image_tag_version = self.get_step_results(DefaultSteps.GENERATE_METADATA)['image-tag']
        else:
            image_tag_version = "latest"
            print('No image tag version found in metadata. Using latest')

        destination = "localhost/{application_name}/{service_name}".format(
            application_name=application_name,
            service_name=service_name
        )
        tag = "{destination}:{version}".format(
            destination=destination,
            version=image_tag_version
        )

        try:
            sh.buildah.bud(  # pylint: disable=no-member
                '--format=' + self.get_config_value('format'),
                '--tls-verify=' + str(self.get_config_value('tlsverify')),
                '--layers', '-f', image_spec_file,
                '-t', tag,
                context,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise RuntimeError('Issue invoking buildah bud with given image '
                               'specification file (' + image_spec_file + ')') from error

        image_tar_file = "image-{application_name}-{service_name}-{version}.tar".format(
            application_name=application_name,
            service_name=service_name,
            version=image_tag_version
        )

        try:
            # Check to see if the tar docker-archive file already exists
            #   this needs to be run as buildah does not support overwritting
            #   existing files.
            if os.path.exists(image_tar_file):
                os.remove(image_tar_file)
            sh.buildah.push( #pylint: disable=no-member
                tag,
                "docker-archive:" + image_tar_file,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise RuntimeError(
                'Issue invoking buildah push to tar file ' + image_tar_file) from error

        results = {
            'image-tag' : tag,
            'image-tar-file' : image_tar_file
        }

        return results
