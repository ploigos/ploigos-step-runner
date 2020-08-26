"""
Step Implementer for the deploy step for ArgoCD.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key         | Required?          | Default              | Description
|---------------------------|--------------------|----------------------|---------------------------
| `argocd-username`         | True               |                      | Username for accessing the
                                                                          ArgoCD API
| `argocd-password`         | True               |                      | Password for accessing the
                                                                          ArgoCD API
| `argocd-api`              | True               |                      | The ArgoCD API endpoint
| `argocd-auto-sync`        | True               | 'false'              | If set to false, argo cd
                                                                          will sync only if
                                                                          explicitly told to do so
                                                                          via the UI or CLI.
                                                                          Otherwise it will sync if
                                                                          the repo contents have
                                                                          changed
| `helm-config-repo`        | True               |                      | The repo containing the
                                                                          helm chart definiton
| `values-yaml-directory`   | True               | ./cicd/Deployment/   | Directory containing jinja
                                                                          templates
| `value-yaml-template`     | True               | values.yaml.j2       | Name of the values yaml
                                                                          jinja file
| `argocd-sync-timeout-`    | True               | 60                   | Number of seconds to wait
  `seconds`                                                               for argocd to sync updates
| `kube-api-uri`            | True               | https://kubernetes.  | k8s API endpoint
                                                   default.svc
| `kube-api-token`          | False              |                      | k8s API token. This is
                                                                          used to add an external
                                                                          k8s cluster into argocd.
                                                                          It is required if the
                                                                          cluster has not already
                                                                          been added to ArgoCD. The
                                                                          token should be persistent
                                                                          (.e.g, a service account
                                                                          token) and have cluster
                                                                          admin access.
| `argocd-helm-chart-path`  | True               | ./                   | Directory containing the
                                                                          helm chart definition
| `git-email`               | True               |                      | Git email for commit
| `git-friendly-name`       | True               | TSSC                 | Git name for commit
| `git-username`            | False              |                      | If the helm config repo
                                                                          is accessed via http(s)
                                                                          this must be supplied
| `git-password`            | False              |                      | If the helm config repo
                                                                          is accessed via http(s)
                                                                          this must be supplied

Expected Previous Step Results
------------------------------

Results expected from previous steps that this step may require.

| Step Name              | Result Key      | Description
|------------------------|-----------------|------------
| `tag-source`           | `tag`           | The git tag to apply to the config repo
| `push-container-image` | `image-url`     | The image url to use in the deployment
| `push-container-image` | `image-version` | The image version use in the deployment

Results
-------

Results output by this step.

| Result Key            | Description
|-----------------------|------------
| `argocd-app-name`     | The argocd app name that was created or updated
| `config-repo-git-tag` | The git tag applied to the configuration repo for deployment


**Example**

    'tssc-results': {
        'deploy': {
            'argocd-app-name': 'acme-myapp-frontend',
            'config-repo-git-tag': 'value'
        }
    }
"""
import sys
import tempfile
from datetime import datetime
import shutil
import sh
from jinja2 import Environment, FileSystemLoader
from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_CONFIG = {
    'values-yaml-directory': './cicd/Deployment',
    'values-yaml-template': 'values.yaml.j2',
    'argocd-sync-timeout-seconds': 60,
    'argocd-auto-sync': 'false',
    'kube-api-uri': 'https://kubernetes.default.svc',
    'argocd-helm-chart-path': './',
    'git-friendly-name': 'TSSC'
}

REQUIRED_CONFIG_KEYS = [
    'argocd-username',
    'argocd-password',
    'argocd-api',
    'helm-config-repo',
    'git-email'
]

GIT_AUTHENTICATION_CONFIG = {
    'git-username': None,
    'git-password': None
}

class ArgoCD(StepImplementer):
    """ StepImplementer for the deploy step for ArgoCD.

    """
    @staticmethod
    def step_name():
        """
        Getter for the TSSC Step name implemented by this step.

        Returns
        -------
        str
            TSSC step name implemented by this step.
        """
        return DefaultSteps.DEPLOY

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
            all(element in runtime_step_config for element in GIT_AUTHENTICATION_CONFIG) or \
            not any(element in runtime_step_config for element in GIT_AUTHENTICATION_CONFIG) \
        ), 'Either username or password is not set. Neither or both must be set.'

    def _run_step(self, runtime_step_config):
        """
        Runs the TSSC step implemented by this StepImplementer.

        Parameters
        ----------
        runtime_step_config : dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.

        Returns
        -------
        dict
            Results of running this step.
        """

        try:
            sh.argocd.login( # pylint: disable=no-member
                runtime_step_config['argocd-api'],
                '--username=' + runtime_step_config['argocd-username'],
                '--password=' + runtime_step_config['argocd-password'],
                '--insecure', _out=sys.stdout)
        except sh.ErrorReturnCode as error:
            raise RuntimeError("Error logging in to ArgoCD: {all}".format(all=error)) from error

        kube_api = runtime_step_config['kube-api-uri']
        # If the cluster is an external cluster and an api token was provided,
        # add the cluster to ArgoCD
        if  kube_api != DEFAULT_CONFIG['kube-api-uri'] and \
            runtime_step_config.get('kube-api-token'):

            context_name = '{server}-context'.format(server=kube_api)

            kubeconfig = """
current-context: {context}
apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: {kube_api}
  name: default-cluster

contexts:
- context:
    cluster: default-cluster
    user: default-user
  name: {context}

kind: Config
preferences:
users:
- name: default-user
  user:
    token: {kube_token}
            """.format(context=context_name,
                       kube_api=kube_api,
                       kube_token=runtime_step_config['kube-api-token'])

            with tempfile.NamedTemporaryFile(buffering=0) as temp_file:
                temp_file.write(bytes(kubeconfig, 'utf-8'))
                try:
                    sh.argocd.cluster.add( # pylint: disable=no-member
                        '--kubeconfig',
                        temp_file.name,
                        context_name,
                        _out=sys.stdout
                    )
                except sh.ErrorReturnCode as error:
                    raise RuntimeError("Error adding cluster to ArgoCD: {cluster}".format(
                        cluster=kube_api)) from error

        values_file_name = 'values-{env}.yaml'.format(env=runtime_step_config['environment-name']) \
            if runtime_step_config.get('environment-name') else 'values.yaml'

        # NOTE: In this block the reference app config repo is cloned and checked out to a temp
        #       directory so that it can update the values.yml based on values.yaml.j2 template.
        #       It then pushes these changes to a respective branch that has the same name as the
        #       reference app as well as tags the branch.
        with tempfile.TemporaryDirectory() as repo_directory:

            results = {}

            try:
                git_url = runtime_step_config.get('helm-config-repo')
                repo_branch = self._get_repo_branch()
                sh.git.clone(runtime_step_config['helm-config-repo'], repo_directory,
                             _out=sys.stdout)

                try:
                    sh.git.checkout(repo_branch, _cwd=repo_directory, _out=sys.stdout)

                except sh.ErrorReturnCode:
                    sh.git.checkout('-b', repo_branch, _cwd=repo_directory, _out=sys.stdout)

                self._update_values_yaml(repo_directory, runtime_step_config, values_file_name)

                git_commit_msg = 'Configuration Change from TSSC Pipeline. Repository: ' +\
                                 '{repo}'.format(repo=git_url)

                sh.git.config('--global', 'user.email', runtime_step_config['git-email'],
                              _out=sys.stdout)

                sh.git.config('--global', 'user.name',
                              runtime_step_config['git-friendly-name'],
                              _out=sys.stdout)

                sh.git.add(values_file_name, _cwd=repo_directory,
                           _out=sys.stdout)

                sh.git.commit('-am', git_commit_msg, _cwd=repo_directory,
                              _out=sys.stdout)

                sh.git.status(_cwd=repo_directory,
                              _out=sys.stdout)

            except sh.ErrorReturnCode as error: # pylint: disable=undefined-variable
                raise RuntimeError("Error invoking git: {all}".format(all=error)) from error

            self._git_tag_and_push(repo_directory, runtime_step_config)

            argocd_app_name = self._get_app_name(runtime_step_config)

            try:
                sh.argocd.app.get(argocd_app_name, _out=sys.stdout) # pylint: disable=no-member
            except sh.ErrorReturnCode_1:  # pylint: disable=undefined-variable, no-member
                print('No app found, creating a new app...')

            repo_branch = self._get_repo_branch()

            sync_policy = 'automated' if str(
                runtime_step_config['argocd-auto-sync']).lower() == 'true' else 'none'

            sh.argocd.app.create( # pylint: disable=no-member
                argocd_app_name,
                '--repo=' + runtime_step_config['helm-config-repo'],
                '--revision=' + repo_branch,
                '--path=' + runtime_step_config['argocd-helm-chart-path'],
                '--dest-server=' + runtime_step_config['kube-api-uri'],
                '--dest-namespace=' + argocd_app_name,
                '--sync-policy=' + sync_policy,
                '--values=' + values_file_name,
                _out=sys.stdout
            )

            sh.argocd.app.sync('--timeout', runtime_step_config['argocd-sync-timeout-seconds'], # pylint: disable=no-member
                               argocd_app_name,
                               _out=sys.stdout)

            results = {
                'argocd-app-name': argocd_app_name,
                'config-repo-git-tag' : self._get_tag(repo_directory)
            }

        return results

    def _get_image_url(self, runtime_step_config):
        image_url = None

        if runtime_step_config.get('image-url'):
            image_url = runtime_step_config.get('image-url')
        else:
            if(self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE) \
            and self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).get('image-url')):
                image_url = self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).\
                            get('image-url')
            else:
                print('No image url found in metadata.')
                raise ValueError('No image url was specified')
        return image_url

    def _get_image_version(self, runtime_step_config):
        image_version = 'latest'

        if runtime_step_config.get('image-version'):
            image_version = runtime_step_config.get('image-version')
        else:
            if(self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE) \
            and self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).get('image-version')):
                image_version = self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).\
                                get('image-version')
            else:
                print('No image version found in metadata, using \"latest\"')
        return image_version

    def _update_values_yaml(self, repo_directory, runtime_step_config, values_file_name):
        env = Environment(loader=FileSystemLoader(runtime_step_config['values-yaml-directory']),
                          trim_blocks=True, lstrip_blocks=True)

        argocd_app_name = self._get_app_name(runtime_step_config)
        version = self._get_image_version(runtime_step_config)
        url = self._get_image_url(runtime_step_config)
        timestamp = str(datetime.now())
        repo_branch = self._get_repo_branch()

        jinja_runtime_step_config = {'image_url' : url,
                                     'image_version' : version,
                                     'timestamp' : timestamp,
                                     'repo_branch' : repo_branch,
                                     'deployment_namespace' : argocd_app_name}

        for key in runtime_step_config:
            jinja_runtime_step_config[key.replace('-', '_')] = runtime_step_config[key]

        template = env.get_template(runtime_step_config['values-yaml-template'])

        rendered_values_file = self.write_temp_file(
            'values.yml',
            bytes(template.render(jinja_runtime_step_config), 'utf-8')
        )

        try:
            shutil.copyfile(rendered_values_file, repo_directory + '/' + values_file_name)
        except (shutil.SameFileError, OSError, IOError) as error:
            raise RuntimeError("Error copying {values_file} file: {all}".format(
                values_file=values_file_name, all=error)) from error

    def _get_tag(self, repo_directory):

        tag = 'latest'
        if(self.get_step_results(DefaultSteps.TAG_SOURCE) \
          and self.get_step_results(DefaultSteps.TAG_SOURCE).get('tag')):
            tag = self.get_step_results(DefaultSteps.TAG_SOURCE).get('tag')
        else:
            print('No version found in metadata. Using latest')

        commit_tag = sh.git('rev-parse', '--short', 'HEAD', _cwd=repo_directory).rstrip() # pylint: disable=too-many-function-args, unexpected-keyword-arg

        full_tag = "{tag}.{commit_tag}".format(tag=tag, commit_tag=commit_tag)

        return full_tag

    def _git_tag_and_push(self, repo_directory, runtime_step_config):
        username = None
        password = None

        if any(element in runtime_step_config for element in GIT_AUTHENTICATION_CONFIG):
            if(runtime_step_config.get('git-username') \
            and runtime_step_config.get('git-password')):
                username = runtime_step_config.get('git-username')
                password = runtime_step_config.get('git-password')
            else:
                raise ValueError(
                    'Both username and password must have ' \
                    'non-empty value in the runtime step configuration'
                )
        else:
            print('No username/password found, assuming ssh')
        git_url = runtime_step_config.get('helm-config-repo')
        if git_url.startswith('http://'):
            if username and password:
                self._git_push(repo_directory,
                               'http://{username}:{password}@{url}'.format(
                                   username=username,
                                   password=password,
                                   url=git_url[7:]))
            else:
                raise ValueError(
                    'For a http:// git url, you need to also provide ' \
                    'username/password pair'
                )
        elif git_url.startswith('https://'):
            if username and password:
                self._git_push(repo_directory,
                               'http://{username}:{password}@{url}'.format(
                                   username=username,
                                   password=password,
                                   url=git_url[8:]))

            else:
                raise ValueError(
                    'For a https:// git url, you need to also provide ' \
                    'username/password pair'
                )
        else:
            self._git_push(repo_directory, None)

    def _git_push(self, repo_directory, url=None):

        git_push = sh.git.push.bake(url) if url else sh.git.push

        try:
            git_push(
                _out=sys.stdout,
                _cwd=repo_directory
            )

            tag = self._get_tag(repo_directory)
            self._git_tag(repo_directory, tag)

            git_push(
                '--tag',
                _out=sys.stdout,
                _cwd=repo_directory
            )

        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking git push and argocd sync') from error

    @staticmethod
    def _git_tag(repo_directory, git_tag_value):  # pragma: no cover
        try:
            # NOTE:
            # this force is only needed locally in case of a re-reun of the same pipeline
            # without a fresh check out. You will notice there is no force on the push
            # making this an acceptable work around to the issue since on the off chance
            # actually overwriting a tag with a different comment, the push will fail
            # because the tag will be attached to a different git hash.
            sh.git.tag(  # pylint: disable=no-member
                git_tag_value,
                '-f',
                _out=sys.stdout,
                _cwd=repo_directory
            )
        except sh.ErrorReturnCode as error:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking git tag ' + git_tag_value) from error

    def _get_app_name(self, runtime_step_config):
        repo_branch = self._get_repo_branch()
        app_name = "{organization}-{application}-{service}-{repo_branch}".\
                   format(organization=runtime_step_config['organization'],
                          application=runtime_step_config['application-name'],
                          service=runtime_step_config['service-name'],
                          repo_branch=repo_branch)

        if runtime_step_config.get('environment-name'):
            app_name = app_name + '-' + runtime_step_config.get('environment-name')

        return app_name.lower().replace('/', '-').replace('_', '-').replace('.', '-')

    @staticmethod
    def _get_repo_branch():
        return sh.git('rev-parse', '--abbrev-ref', 'HEAD').rstrip() # pylint: disable=too-many-function-args

# register step implementer
TSSCFactory.register_step_implementer(ArgoCD, True)
