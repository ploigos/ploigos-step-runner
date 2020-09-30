"""Step Implementer for the container-image-static-compliance-scan step for OpenSCAP.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key           | Required? | Default | Description
|-----------------------------|-----------|---------|-----------
| `log-level`                 | True      | Info    | log level for buildah, podman
                                                      and scap utilities
| `scap-input-file`           | True      |         | Input file for scap base scan

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

| Step Name                | Result Key       | Description
|--------------------------|------------------|------------
| `create-container-image` | `image-tar-file` | Image to scan

Results
-------

Results output by this step.

| Result Key                      | Description
|---------------------------------|------------
| `compliance_scan_results_path`  | Absolute path to directory of compliance scan results

"""

import sys
import sh
from tssc import StepImplementer, DefaultSteps

DEFAULT_CONFIG = {
    'log-level': 'info'
}

REQUIRED_CONFIG_KEYS = [
    'service-name',
    'application-name',
    'organization',
    'log-level',
    'scap-input-file',
]

class OpenSCAP(StepImplementer):
    """
    StepImplementer for the container-image-static-compliance-scan step for OpenSCAP.
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

    def _run_step(self): # pylint: disable=too-many-locals
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        dict
            Results of running this step.
        """

        image_tar_file = ''
        if(self.get_step_results(DefaultSteps.CREATE_CONTAINER_IMAGE) and \
          self.get_step_results(DefaultSteps.CREATE_CONTAINER_IMAGE).get('image-tar-file')):
            image_tar_file = self.\
            get_step_results(DefaultSteps.CREATE_CONTAINER_IMAGE)['image-tar-file']
        else:
            raise RuntimeError('Missing image tar file from ' + DefaultSteps.CREATE_CONTAINER_IMAGE)

        log_level = 'info'
        if self.get_config_value('log-level'):
            log_level = self.get_config_value('log-level')

        buildah_containers_pre_import_result = sh.buildah( # pylint: disable=no-member
            '--storage-driver',
            'vfs',
            'containers',
            '-q',
            _out=sys.stdout,
            _err=sys.stderr,
            _tee=True
        )
        num_containers = buildah_containers_pre_import_result.stdout.count(b'\n')
        if num_containers > 0:
            raise ValueError('Zero vfs base containers should be running')

        try:
            # import image tar file to vfs file system
            sh.buildah( # pylint: disable=no-member
                'from',
                '--storage-driver',
                'vfs',
                '--log-level',
                log_level,
                f"docker-archive:{image_tar_file}",
                _out=sys.stdout,
                _err=sys.stderr
            )

            # get container id
            buildah_containers_result = sh.buildah( # pylint: disable=no-member
                '--storage-driver',
                'vfs',
                'containers',
                '-q',
                _out=sys.stdout,
                _err=sys.stderr,
                _tee=True
            )
            container_id = buildah_containers_result.stdout.rstrip()
            print(f"container_id to scan = {container_id}")

            # baking `buildah unshare` command to wrap other buildah commands with
            # so that container does not need to be running in a privilaged mode to be able
            # to function
            buildah_unshare_comand = sh.buildah.bake('unshare') # pylint: disable=no-member

            # mount the container filesystem and get mount path
            #
            # NOTE: run in the context of `buildah unshare` so that container does not
            #       need to be run in a privilaged mode
            buildah_mount_command = buildah_unshare_comand.bake("buildah", "mount")
            buildah_mount_result = buildah_mount_command(
                '--storage-driver', 'vfs',
                container_id,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee=True
            )
            mount_path = buildah_mount_result.stdout.rstrip()
            print(f"mount_path to scan = {mount_path}")

            # Execute scan in the context of buildah unshare
            #
            # NOTE: run in the context of `buildah unshare` so that container does not
            #       need to be run in a privilaged mode
            scan_input_file = self.get_config_value('scap-input-file').rstrip()
            scan_output_absolute_path = self.write_working_file('scap-compliance-output.txt', b'')
            scan_report_absolute_path = self.write_working_file('scap-compliance-report.html', b'')
            oscap_chroot_command = buildah_unshare_comand.bake("oscap-chroot")
            oscap_result = oscap_chroot_command(
                mount_path,
                'oval',
                'eval',
                '--report', scan_report_absolute_path,
                scan_input_file,
                _out=sys.stdout,
                _err=sys.stderr,
                _tee=True
            )

            oscap_result_file = open(scan_output_absolute_path, "w+")
            oscap_result_file.write(oscap_result.stdout.decode("utf-8"))
            oscap_result_file.close()
            print("Compliance Scan Completed.  Report found at following path: " +
                  scan_report_absolute_path)

        except sh.ErrorReturnCode as error:
            raise RuntimeError('Unexpected runtime error') from error

        results = {
            'result': {
                'success': True,
                'message': 'container-image-static-compliance-scan step completed',
            },
            'report-artifacts': [
                {
                    'name': 'container-image-static-compliance-scan result set',
                    'path': 'file://' + scan_report_absolute_path
                }
            ]
        }
        return results
