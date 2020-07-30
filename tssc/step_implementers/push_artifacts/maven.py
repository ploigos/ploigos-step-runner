"""Step Implementer for the push-artifacts step for Maven.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default | Description
|-------------------|-----------|---------|-----------
| `url`             | True      |         | URL to the artifact repository to push the artifact to.
| `user`            | False     |         | User to authenticate with the artifact repository.
| `password`        | False     |         | Password to authenticate with the artifact repository.


Expected Previous Step Results
------------------------------

Results expected from previous steps that this step requires.

| Step Name           | Result Key  | Description
|---------------------|-------------|------------
| `generate-metadata` | `version`   | TODO
| `package`           | `artifacts` |

Results
-------

Results output by this step.

| Result Key  | Description
|-------------|------------
| `artifacts` | An array of dictionaries with information on the pushed artifacts.

**artifacts**
Keys in the dictionary elements in the `artifacts` array in the step results.

| `artifacts`Key | Description
|----------------|------------
| `url`          | URL to the artifact pushed to the artifact repository
| `path`         | Absolute path to the artifact pushed to the artifact repository
| `artifact-id`  | Maven artifact ID pushed to the artifact repository
| `group-id`     | Maven group ID pushed to the artifact repository
| `version`      | Version pushed to the artifact repository
"""
import re
import sh

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {}
OPTIONAL_ARGS = {
    'user': None,
    'password': None
}

class Maven(StepImplementer):
    """
    StepImplementer for the push-artifacts step for Maven.
    """

    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.PUSH_ARTIFACTS

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """
        if 'url' not in step_config or not step_config['url']:
            raise ValueError('url must have none empty value in the step configuration')

    @staticmethod
    def _validate_runtime_step_config(runtime_step_config):
        if not all(element in runtime_step_config for element in OPTIONAL_ARGS) \
          and any(element in runtime_step_config for element in OPTIONAL_ARGS):
            raise ValueError('Either user or password is not set. Neither ' \
              'or both must be set.')

    def _run_step(self, runtime_step_config):
        user = ''
        password = ''

        url = runtime_step_config['url']

        if any(element in runtime_step_config for element in OPTIONAL_ARGS):
            if(runtime_step_config.get('user') \
              and runtime_step_config.get('password')):
                user = runtime_step_config.get('user')
                password = runtime_step_config.get('password')

        # ----- get generate-metadata items
        # Required: Get the generate-metadata.version
        if(self.get_step_results('generate-metadata') and \
          self.get_step_results('generate-metadata').get('version')):
            version = self.get_step_results('generate-metadata')['version']
        else:
            raise ValueError('Severe error: Generate-metadata does not have a version')

        # ----- get package items this will change
        # Required: Get the package.artifacts
        if(self.get_step_results('package') and \
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
            'artifacts' : []
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
                    sh.mvn('deploy:deploy-file', # pylint: disable=no-member \
                           '-Dversion='+version,\
                           '-Durl='+url,\
                           '-Dfile='+artifact_path,\
                           '-DgroupId='+group_id,\
                           '-DartifactId='+artifact_id,\
                           '-Dpackaging='+package_type,\
                           '-DrepositoryId=tssc',\
                           '-s'+settings_path\
                    )
                else:
                    sh.mvn('deploy:deploy-file', # pylint: disable=no-member \
                           '-Dversion='+version,\
                           '-Durl='+url,\
                           '-Dfile='+artifact_path,\
                           '-DgroupId='+group_id,\
                           '-DartifactId='+artifact_id,\
                           '-Dpackaging='+package_type,\
                           '-DrepositoryId=tssc',\
                           '-DrepositoryUser='+user,\
                           '-DrepositoryPassword='+password,\
                           '-s'+settings_path\
                    )

            except sh.ErrorReturnCode as error:
                raise RuntimeError("Error invoking mvn: {0}".format(str(error)))

            results['artifacts'].append({
                'url': url + '/' + \
                       re.sub(r'\.', '/', group_id) + '/' + \
                       artifact_id + '/' + \
                       version  + '/' + \
                       artifact_id + '-' + \
                       version  + '.' + \
                       package_type,
                'artifact-id' : artifact_id,
                'group-id' : group_id,
                'version' : version,
                'path' : artifact_path,
            })

        return results

# register step implementer
TSSCFactory.register_step_implementer(Maven)
