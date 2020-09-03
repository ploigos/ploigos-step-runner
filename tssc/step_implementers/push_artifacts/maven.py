"""Step Implementer for the push-artifacts step for Maven.

Step Configuration
------------------

Step configuration key(s) for this step:

| Key                 | Required | Default | Description
|---------------------|----------|---------|------------
| `url`               | True     | N/A     | URL to the artifact repository
| `user`              | False    | N/A     | Repository user for authenication
| `password`          | False    | N/A     | Resository password for authentication

`user` and `password` can be specifed as runtime arguments.

Expected Previous Step Results
------------------------------

Results expected from previous steps:

| Step Name           |  Key               | Description
|---------------------|--------------------|------------
| `generate-metadata` | `version`          | The version to be used to deploy to artifactory.
| `package`           | `artifacts`        | Artifacts is an array of `artifact`.
|                     |                    | Each element of an `artifact` will be used
|                     |                    | as a parameter to deploy to artifactory:
|                     |                    | * artifact.group-id
|                     |                    | * artifact.artifact-id
|                     |                    | * artifact.path
|                     |                    | * artifact.package-type

Results
-------

Results output by this step:

| Key             | Description
|-----------------|------------
| `artifacts`     | An array of dictionaries describing the push results

Elements in the `artifacts` dictionary:

| Elements        | Description
|-----------------|------------
| `url`           | URL to the artifact pushed to the artifact repository
| `path`          | Absolute path to the artifact pushed to the artifact repository
| `artifact-id`   | Maven artifact ID pushed to the artifact repository
| `group-id`      | Maven group ID pushed to the artifact repository
| `version`       | Version pushed to the artifact repository

Examples
--------

Example: Step Configuration (minimal)

    push-artifacts:
    - implementer: Maven
      config:
        url: http://artifactory.company.com/repo

Example: Generated Maven Deploy (uses both step configuration and previous results)

    mvn
      deploy:deploy-file'
      -Durl=url
      -Dversion=generate-metadata.version
      -DgroupId=package.artifact.group-id
      -DartifactId=package.artifact.artifact-id
      -Dfile=package.artifact.path
      -Dpackaging=package.artifact.package-type

Example: Results

    'tssc-results': {
        'artifacts': [
             {
             'path':''
             'artifact-id': ''
             'group-id': ''
             'package-type': ''
             'version': ''
             }
        ]
    }

"""
import re
import sys
import sh

from tssc import StepImplementer

DEFAULT_CONFIG = {}
AUTHENTICATION_CONFIG = {
    'user': None,
    'password': None
}
REQUIRED_CONFIG_KEYS = [
    'url'
]


class Maven(StepImplementer):
    """
    StepImplementer for the push-artifacts step for Maven.
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

    def _validate_runtime_step_config(self, runtime_step_config):
        """
        Validates the given `runtime_step_config` against the required step configuration keys.

        Parameters
        ----------
        runtime_step_config : dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.

        Raises
        ------
        AssertionError
            If the given `runtime_step_config` is not valid with a message as to why.
        """
        super()._validate_runtime_step_config(runtime_step_config) #pylint: disable=protected-access

        assert ( \
            all(element in runtime_step_config for element in AUTHENTICATION_CONFIG) or \
            not any(element in runtime_step_config for element in AUTHENTICATION_CONFIG) \
        ), 'Either username or password is not set. Neither or both must be set.'

    def _run_step(self):
        """Runs the TSSC step implemented by this StepImplementer.

        Returns
        -------
        dict
            Results of running this step.
        """
        user = ''
        password = ''

        url = self.get_config_value('url')

        if self.has_config_value(AUTHENTICATION_CONFIG):
            if(self.get_config_value('user') and self.get_config_value('password')):
                user = self.get_config_value('user')
                password = self.get_config_value('password')

        # ----- get generate-metadata items
        # Required: Get the generate-metadata.version
        if (self.get_step_results('generate-metadata') and
                self.get_step_results('generate-metadata').get('version')):
            version = self.get_step_results('generate-metadata')['version']
        else:
            raise ValueError('Severe error: Generate-metadata does not have a version')

        # ----- get package items this will change
        # Required: Get the package.artifacts
        if (self.get_step_results('package') and
                self.get_step_results('package').get('artifacts')):
            artifacts = self.get_step_results('package')['artifacts']
        else:
            raise ValueError('Severe error: Package does not have artifacts')

        # Build a temporary settings.xml file for the mvn user/pass
        settings_path = self.write_temp_file('ci-settings.xml', b'''
        <settings>
              <servers>
                  <server>
                          <id>${repositoryId}</id>
                          <username>${repositoryUser}</username>
                          <password>${repositoryPassword}</password>
                  </server>
              </servers>
        </settings>''')

        results = {
            'artifacts': []
        }

        for artifact in artifacts:
            artifact_path = artifact['path']
            group_id = artifact['group-id']
            artifact_id = artifact['artifact-id']
            package_type = artifact['package-type']

            try:
                # Build the mvn command, settings is required even if no user/password
                # The settings file is required, need to deal with empty userid,password
                # https://maven.apache.org/plugins/maven-deploy-plugin/deploy-file-mojo.html

                if user == '':
                    sh.mvn(  # pylint: disable=no-member
                        'deploy:deploy-file',
                        '-Dversion=' + version,
                        '-Durl=' + url,
                        '-Dfile=' + artifact_path,
                        '-DgroupId=' + group_id,
                        '-DartifactId=' + artifact_id,
                        '-Dpackaging=' + package_type,
                        '-DrepositoryId=tssc',
                        '-s' + settings_path,
                        _out=sys.stdout
                    )
                else:
                    sh.mvn(  # pylint: disable=no-member
                        'deploy:deploy-file',
                        '-Dversion=' + version,
                        '-Durl=' + url,
                        '-Dfile=' + artifact_path,
                        '-DgroupId=' + group_id,
                        '-DartifactId=' + artifact_id,
                        '-Dpackaging=' + package_type,
                        '-DrepositoryId=tssc',
                        '-DrepositoryUser=' + user,
                        '-DrepositoryPassword=' + password,
                        '-s' + settings_path,
                        _out=sys.stdout
                    )

            except sh.ErrorReturnCode as error:
                raise RuntimeError("Error invoking mvn: {all}".format(all=error)) from error

            results['artifacts'].append({
                'url': url + '/' +
                       re.sub(r'\.', '/', group_id) + '/' +
                       artifact_id + '/' +
                       version + '/' +
                       artifact_id + '-' +
                       version + '.' +
                       package_type,
                'artifact-id': artifact_id,
                'group-id': group_id,
                'version': version,
                'path': artifact_path,
            })

        return results
