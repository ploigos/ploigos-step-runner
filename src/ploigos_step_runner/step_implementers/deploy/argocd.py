# pylint: disable=too-many-lines
"""`StepImplementer` for the `deploy` step using ArgoCD.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key         | Required? | Default  | Description
--------------------------|-----------|----------|---------------------------
`argocd-username`         | Yes       |          | Username for accessing the ArgoCD API
`argocd-password`         | Yes       |          | Password for accessing the ArgoCD API
`argocd-api`              | Yes       |          | The ArgoCD API endpoint
`argocd-auto-sync`        | Yes       | True     | If set to false, argo cd will sync only if \
                                                   explicitly told to do so via the UI or CLI. \
                                                   Otherwise it will sync if the repo contents \
                                                   have changed
`argocd-skip-tls`         | Yes       | False    | `False` to not ignore TLS issues when \
                                                   authenticating with ArgoCD. True` to ignore TLS \
                                                   issues when authenticating with ArgoCD.
`argocd-sync-timeout-seconds` \
                          | Yes       | 60       | Number of seconds to wait for argocd to \
                                                   sync updates
`deployment-config-repo`  | Yes       |          | The repo containing the helm chart definition
`deployment-config-helm-chart-path` \
                          | Yes       | ./       | Directory containing the helm chart definition
`deployment-config-helm-chart-environment-values-file` \
                          | No        | values-{ENV}.yaml | File to update with environment \
                                                            deployment specific information. \
                                                            <br/>\
                                                            Default value uses `environment` \
                                                            configuration option to calculate file \
                                                            name.
`deployment-config-helm-chart-additional-values-files` \
                          | No        |          | Array of additional values files. \
                                                   Paths must be relative to the given \
                                                   Helm Chart path (`deployment-config-helm-chart-path`). \
                                                   <br/>\
                                                   Does not need to include \
                                                   `deployment-config-helm-chart-environment-values-file` \
                                                   as it will be automatically included as the \
                                                   last `--values` flag.
                                                   <br/>\
                                                   Used when createing the ArgoCD Application.\
                                                   <br/><br/>\
                                                   **NOTE:** Helm will always pick up `values.yaml`\
                                                   by default whether or not additional values \
                                                   files are provided, therefor no need to \
                                                   explicitly provide.
`deployment-config-helm-chart-values-file-image-tag-yq-path` \
                          | Yes       | `image_tag` | YQ path to value in `deployment-config-helm-chart-environment-values-file` \
                                                      to update with the `container-image-tag` \
                                                      before deployment. \
                                                      <br/>\
                                                      **SEE:**: https://github.com/mikefarah/yq \
                                                      for documentation on valid yq paths.
`kube-api-uri`            | Yes       | https://kubernetes.default.svc | k8s API endpoint
`kube-api-token`          | No        |          | k8s API token. This is used to add an external \
                                                   k8s cluster into argocd. It is required if the \
                                                   cluster has not already been added to ArgoCD. \
                                                   The token should be persistent \
                                                   (.e.g, a service account token) and have cluster \
                                                   admin access.
`kube-api-skip-tls`       | Yes       | False    | Whether or not to skip tls verification when \
                                                   authenticating to an external k8s cluster. \
                                                   Used when a new cluster is registered with \
                                                   argocd.
`git-email`               | Yes       |          | Git email for commit
`git-name`                | Yes       | `Ploigos Robot` | Git name for commit
`git-username`            | No        |          | If the helm config repo s accessed via http(s) \
                                                   this must be supplied
`git-password`            | No        |          | If the helm config repo is accessed via http(s) \
                                                   this must be supplied
`tag`                     | No        | latest   | The git tag to apply to the config repo. \
                                                   If not supplied `version` will be used. \
                                                   If `version` not supplied `latest` will be used.
`version`                 | No        | latest   | Ignored if `tag` is provided. \
                                                   The git tag to apply to the config repo if `tag` \
                                                   is not supplied. \
                                                   If `tag` and `version` not supplied `latest` \
                                                   will be used.
`container-image-tag`     | Yes       |          | Tag container image was pushed with. <br/>\
                                                   Takes the form of: \
                                                     "`container-image-registry-uri`\
                                                        /`container-image-registry-organization`\
                                                        /`container-image-repository`\
                                                        :`container-image-version`"
`force-push-tags`         | No        | False    | Force push Git Tags

Results
-------
Results output by this step.

Result Key                 | Description
---------------------------|------------
`argocd-app-name`          | The argocd app name that was created or updated
`deployed-host-urls`       | The host URLs deployed by ArgoCD (Ingress/Route resources)
`config-repo-git-tag`      | The git tag applied to the configuration repo for deployment
`argocd-deployed-manifest` | The generated yml file used for deployment.
""" # pylint: disable=line-too-long
import os
import re
import sys

import sh
import yaml
from ploigos_step_runner import StepImplementer
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_result import StepResult

DEFAULT_CONFIG = {
    'argocd-sync-timeout-seconds': 60,
    'argocd-auto-sync': True,
    'argocd-skip-tls' : False,
    'deployment-config-helm-chart-path': './',
    'deployment-config-helm-chart-additional-values-files': [],
    'deployment-config-helm-chart-values-file-image-tag-yq-path': 'image_tag',
    'force-push-tags': False,
    'kube-api-skip-tls': False,
    'kube-api-uri': 'https://kubernetes.default.svc',
    'git-name': 'Ploigos Robot'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'argocd-username',
    'argocd-password',
    'argocd-api',
    'argocd-skip-tls',
    'deployment-config-repo',
    'deployment-config-helm-chart-path',
    'deployment-config-helm-chart-values-file-image-tag-yq-path',
    'git-email',
    'git-name',
    'container-image-tag'
]

GIT_AUTHENTICATION_CONFIG = {
    'git-username': None,
    'git-password': None
}

KUBE_LABEL_NOT_SAFE_CHARS_REGEX = r"[^a-zA-Z0-9\-_\.]"
KUBE_LABEL_NOT_SAFE_BEGINING_END_CHARS_REGEX = r"^[^a-zA-Z0-9]*|[^a-zA-Z0-9]*$"
KUBE_LABEL_MAX_LENGTH = 52
KUBE_LABEL_REPLACEMENT_CHAR = '-'


class ArgoCD(StepImplementer):
    """`StepImplementer` for the `deploy` step using ArgoCD.
    """

    GIT_REPO_REGEX = re.compile(r"(?P<protocol>^https:\/\/|^http:\/\/)?(?P<address>.*$)")

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

        Returns
        -------
        dict
            Default values to use for step configuration values.

        Notes
        -----
        These are the lowest precedence configuration values.
        """
        return DEFAULT_CONFIG

    @staticmethod
    def _required_config_or_result_keys():
        """Getter for step configuration or previous step result artifacts that are required before
        running this step.

        See Also
        --------
        _validate_required_config_or_previous_step_result_artifact_keys

        Returns
        -------
        array_list
            Array of configuration keys or previous step result artifacts
            that are required before running the step.
        """
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * either both git-username and git-password are set or neither.

        Raises
        ------
        StepRunnerException
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # ensure either both git-username and git-password are set or neither
        runtime_auth_config = {}
        for auth_config_key in GIT_AUTHENTICATION_CONFIG:
            runtime_auth_config_value = self.get_value(auth_config_key)

            if runtime_auth_config_value is not None:
                runtime_auth_config[auth_config_key] = runtime_auth_config_value

        if (any(element in runtime_auth_config for element in GIT_AUTHENTICATION_CONFIG)) and \
                (not all(element in runtime_auth_config for element in GIT_AUTHENTICATION_CONFIG)):
            raise StepRunnerException(
                "Either 'git-username' or 'git-password 'is not set. Neither or both must be set."
            )

        # ensure if deployment config repo is using http/https that user/pass is provided
        deployment_config_repo_uri = self.get_value('deployment-config-repo')
        if re.match(r'^http://|^https://', deployment_config_repo_uri) and not runtime_auth_config:
            raise StepRunnerException(
                f"Since provided 'deployment-config-repo' ({deployment_config_repo_uri}) uses"
                f" http/https protical both 'git-username' and 'git-password' must be provided."
            )

    def _run_step(self):  # pylint: disable=too-many-locals
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # get input
        deployment_config_repo = self.get_value('deployment-config-repo')
        deployment_config_repo_branch = ArgoCD.__get_repo_branch()
        deployment_config_helm_chart_path = self.get_value('deployment-config-helm-chart-path')
        deployment_config_destination_cluster_uri = self.get_value('kube-api-uri')
        deployment_config_destination_cluster_token = self.get_value('kube-api-token')
        deployment_config_helm_chart_environment_values_file = \
            self.__get_deployment_config_helm_chart_environment_values_file()
        deployment_config_helm_chart_values_file_image_tag_yq_path = \
            self.get_value('deployment-config-helm-chart-values-file-image-tag-yq-path')
        deployment_config_helm_chart_additional_value_files = \
            self.get_value('deployment-config-helm-chart-additional-values-files')
        container_image_tag = self.get_value('container-image-tag')
        force_push_tags = self.get_value('force-push-tags')

        try:
            argocd_app_name = self.__get_app_name()
            step_result.add_artifact(
                name='argocd-app-name',
                value=argocd_app_name
            )

            # clone the configuration repository
            print("Clone the configuration repository")
            clone_repo_dir_name = 'deployment-config-repo'
            deployment_config_repo_dir = ArgoCD.__clone_repo(
                repo_dir=self.create_working_dir_sub_dir(clone_repo_dir_name),
                repo_url=deployment_config_repo,
                repo_branch=deployment_config_repo_branch,
                user_email=self.get_value('git-email'),
                user_name=self.get_value('git-name')
            )

            # update values file, commit it, push it, and tag it
            print("Update the environment values file")
            deployment_config_helm_chart_environment_values_file_path = os.path.join(
                deployment_config_repo_dir,
                deployment_config_helm_chart_path,
                deployment_config_helm_chart_environment_values_file
            )
            self.__update_yaml_file_value(
                file=deployment_config_helm_chart_environment_values_file_path,
                yq_path=deployment_config_helm_chart_values_file_image_tag_yq_path,
                value=container_image_tag
            )
            print("Commit the updated environment values file")
            ArgoCD.__git_commit_file(
                git_commit_message=f'Updating values for deployment to {self.environment}',
                file_path=os.path.join(
                    deployment_config_helm_chart_path,
                    deployment_config_helm_chart_environment_values_file
                ),
                repo_dir=deployment_config_repo_dir
            )
            print("Tag and push the updated environment values file")
            deployment_config_repo_tag = self.__get_deployment_config_repo_tag()
            self.__git_tag_and_push_deployment_config_repo(
                deployment_config_repo=deployment_config_repo,
                deployment_config_repo_dir=deployment_config_repo_dir,
                deployment_config_repo_tag=deployment_config_repo_tag,
                force_push_tags=force_push_tags
            )
            step_result.add_artifact(
                name='config-repo-git-tag',
                value=deployment_config_repo_tag
            )

            # create/update argocd app and sync it
            print("Sign into ArgoCD")
            ArgoCD.__argocd_sign_in(
                argocd_api=self.get_value('argocd-api'),
                username=self.get_value('argocd-username'),
                password=self.get_value('argocd-password'),
                insecure=self.get_value('argocd-skip-tls')
            )
            print("Add target cluster to ArgoCD")
            self.__argocd_add_target_cluster(
                kube_api=deployment_config_destination_cluster_uri,
                kube_api_token=deployment_config_destination_cluster_token,
                kube_api_skip_tls=self.get_value('kube-api-skip-tls')
            )
            print(f"Create or update ArgoCD Application ({argocd_app_name})")
            argocd_values_files = []
            argocd_values_files += deployment_config_helm_chart_additional_value_files
            argocd_values_files += [deployment_config_helm_chart_environment_values_file]
            ArgoCD.__argocd_app_create_or_update(
                argocd_app_name=argocd_app_name,
                repo=deployment_config_repo,
                revision=deployment_config_repo_branch,
                path=deployment_config_helm_chart_path,
                dest_server=deployment_config_destination_cluster_uri,
                auto_sync=self.get_value('argocd-auto-sync'),
                values_files=argocd_values_files
            )

            # sync and wait for the sync of the ArgoCD app
            print(f"Sync (and wait for) ArgoCD Application ({argocd_app_name})")
            ArgoCD.__argocd_app_sync(
                argocd_app_name=argocd_app_name,
                argocd_sync_timeout_seconds=self.get_value('argocd-sync-timeout-seconds')
            )

            # get the ArgoCD app manifest that was synced
            print(f"Get ArgoCD Application ({argocd_app_name}) synced manifest")
            arogcd_app_manifest_file = self.__argocd_get_app_manifest(
                argocd_app_name=argocd_app_name
            )
            step_result.add_artifact(
                name='argocd-deployed-manifest',
                value=arogcd_app_manifest_file
            )

            # determine the deployed host URLs
            print(
                "Determine the deployed host URLs for the synced"
                f" ArgoCD Application (({argocd_app_name})"
            )
            deployed_host_urls = ArgoCD.__get_deployed_host_urls(
                manifest_path=arogcd_app_manifest_file
            )
            step_result.add_artifact(
                name='deployed-host-urls',
                value=deployed_host_urls
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = f"Error deploying to environment ({self.environment}):" \
                f" {str(error)}"

        return step_result

    def __get_container_image_version(self):
        image_version = self.get_value('container-image-version')
        if image_version is None:
            image_version = 'latest'
            print('No image version found in metadata. Using latest.')
        return image_version


    def __get_deployment_config_helm_chart_environment_values_file(self):
        """Get the deployment configuration Helm Chart environment specific value file.

        Returns
        -------
        str
            Deployment configuration Helm Chart environment specific value file.
        """
        deployment_config_helm_chart_env_value_file = \
            self.get_value('deployment-config-helm-chart-environment-values-file')

        if not deployment_config_helm_chart_env_value_file:
            if self.environment:
                deployment_config_helm_chart_env_value_file = f'values-{self.environment}.yaml'
            else:
                deployment_config_helm_chart_env_value_file = 'values.yaml'

        return deployment_config_helm_chart_env_value_file

    def __update_yaml_file_value(self, file, yq_path, value):
        """Update a YAML file using YQ.

        Parameters
        ----------
        file : str
            Path to file to update.
        yq_path : str
            YQ path to the value to update.
        value: str
            value to update the `yq_path`

        Returns
        -------
        str
            Path to the file to update.

        Raises
        ------
        StepRunnerException
            If error updating file.
        """
        # NOTE: use a YQ script to update so that comment can be injected
        yq_script_file = self.write_working_file(
            filename='update-yaml-file-yq-script.yaml',
            contents=bytes(
                f"- command: update\n"
                f"  path: {yq_path}\n"
                f"  value:\n"
                f"    {value} # written by ploigos-step-runner\n",
                'utf-8'
            )
        )

        # inplace update the file
        try:
            sh.yq.write( # pylint: disable=no-member
                file,
                f'--script={yq_script_file}',
                '--inplace'
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error updating YAML file ({file}) target ({yq_path}) with value ({value}):"
                f" {error}"
            ) from error

        return file

    def __git_tag_and_push_deployment_config_repo(
        self,
        deployment_config_repo,
        deployment_config_repo_dir,
        deployment_config_repo_tag,
        force_push_tags
    ):
        deployment_config_repo_match = ArgoCD.GIT_REPO_REGEX.match(deployment_config_repo)
        deployment_config_repo_protocol = deployment_config_repo_match.groupdict()['protocol']
        deployment_config_repo_address = deployment_config_repo_match.groupdict()['address']

        # if deployment config repo uses http/https push using user/pass
        # else push using ssh
        if deployment_config_repo_protocol and re.match(
            r'^http://|^https://',
            deployment_config_repo_protocol
        ):
            username = self.get_value('git-username')
            password = self.get_value('git-password')

            deployment_config_repo_with_user_pass = \
                f"{deployment_config_repo_protocol}{username}:{password}" \
                f"@{deployment_config_repo_address}"
            ArgoCD.__git_tag_and_push(
                repo_dir=deployment_config_repo_dir,
                tag=deployment_config_repo_tag,
                url=deployment_config_repo_with_user_pass,
                force_push_tags=force_push_tags
            )
        else:
            ArgoCD.__git_tag_and_push(
                repo_dir=deployment_config_repo_dir,
                tag=deployment_config_repo_tag,
                force_push_tags=force_push_tags
            )

    def __get_app_name(self):
        repo_branch = ArgoCD.__get_repo_branch()
        organization = self.get_value('organization')
        application = self.get_value('application-name')
        service = self.get_value('service-name')
        app_name = f"{organization}-{application}-{service}-{repo_branch}"

        if self.environment:
            app_name = app_name + '-' + self.environment

        # replace dangerous characters in app name
        app_name = app_name.lower()
        app_name = re.sub(
            KUBE_LABEL_NOT_SAFE_CHARS_REGEX,
            KUBE_LABEL_REPLACEMENT_CHAR,
            app_name
        )

        # max length for a kube label / resource name is 63
        if len(app_name) > KUBE_LABEL_MAX_LENGTH:
            app_name = app_name[len(app_name) - KUBE_LABEL_MAX_LENGTH:]

        # be sure app name doesn't start or end with not safe chars
        app_name = re.sub(
            KUBE_LABEL_NOT_SAFE_BEGINING_END_CHARS_REGEX,
            '',
            app_name
        )

        return app_name

    def __get_deployment_config_repo_tag(self):
        """
        Returns
        -------
        str
            String to tag the deployment configuration repository with.

        Raise
        -----
        StepRunnerException
            If i
        """
        tag = self.get_value('tag')

        if tag is None:
            tag = self.get_value('version')

        if tag is None:
            tag = 'latest'
            print(
                "No specified 'tag' or 'version' using 'latest' for"
                "deployment configuration repository tag."
            )

        # need the config repo tag to be unique per environment to prevent conflicts
        if self.environment:
            tag += f".{self.environment}"

        return tag

    @staticmethod
    def __get_deployed_host_urls( # pylint: disable=too-many-branches,too-many-nested-blocks
        manifest_path
    ):
        """Gets the ingress hosts URLs from a manifest of Kubernetes resources.

        Supports:

        - route.openshift.io/v1/Route
        - networking.k8s.io/v1/Ingress

        Returns
        -------
        list of str
            Ingress hosts URLs defined in the given manifest of Kubernetes resources.

        See
        ---
        * https://docs.openshift.com/container-platform/4.6/rest_api/network_apis/ingress-networking-k8s-io-v1.html
        * https://docs.openshift.com/container-platform/4.6/rest_api/network_apis/route-route-openshift-io-v1.html
        """ # pylint: disable=line-too-long
        host_urls = []
        manifest_resources = {}
        # load the manifest
        with open(manifest_path) as file:
            manifest_resources = yaml.load_all(file, Loader=yaml.FullLoader)

            # for each resource in the manfest,
            # determine if its a known type and then attempt to get host and TLS config from it
            for manifest_resource in manifest_resources:
                if manifest_resource is None or 'kind' not in manifest_resource:
                    continue

                kind = manifest_resource['kind']
                api_version = manifest_resource['apiVersion']

                # if Route resource
                if kind == 'Route' and api_version == 'route.openshift.io/v1':
                    # get host
                    if 'host' in manifest_resource['spec']:
                        host = manifest_resource['spec']['host']

                        # determine if TLS route
                        tls = False
                        if 'tls' in manifest_resource['spec']:
                            tls_config = manifest_resource['spec']['tls']
                            if tls_config:
                                tls = True

                        # determine protocol
                        protocol = ''
                        if tls:
                            protocol = 'https://'
                        else:
                            protocol = 'http://'

                        # record the host url
                        host_urls.append(f"{protocol}{host}")

                # if Ingress resource
                if kind == 'Ingress' and api_version == 'networking.k8s.io/v1':
                    ingress_rules = manifest_resource['spec']['rules']
                    for rule in ingress_rules:
                        # get host
                        if 'host' in rule:
                            host = rule['host']

                            # determine if TLS ingress
                            tls = False
                            if 'tls' in manifest_resource['spec']:
                                for tls_config in manifest_resource['spec']['tls']:
                                    if ('hosts' in tls_config) and (host in tls_config['hosts']):
                                        tls = True
                                        break

                            # determine protocol
                            protocol = ''
                            if tls:
                                protocol = 'https://'
                            else:
                                protocol = 'http://'

                            # record the host url
                            host_urls.append(f"{protocol}{host}")

        return host_urls

    @staticmethod
    def __clone_repo(
        repo_dir,
        repo_url,
        repo_branch,
        user_email,
        user_name
    ):
        """Clones and checks out the deployment configuration repository.

        Parameters
        ----------
        repo_dir : str
            Path to where to clone the repository
        repo_uri : str
            URI of the repository to clone.
        user_email : str
            email to use when performing git operations in the cloned repository
        user_name : str
            name to use when performing git operations in the cloned repository

        Returns
        -------
        str
            Path to the directory where the deployment configuration repository was cloned
            and checked out.

        Raises
        ------
        StepRunnerException
        * if error cloning repository
        * if error checking out branch of repository
        * if error configuring repo user
        """
        try:
            sh.git.clone( # pylint: disable=no-member
                repo_url,
                repo_dir,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error cloning repository ({repo_url}): {error}"
            ) from error

        try:
            # no atomic way in git to checkout out new or existing branch,
            # so first try to check out existing, if that doesn't work try new
            try:
                sh.git.checkout(  # pylint: disable=no-member
                    repo_branch,
                    _cwd=repo_dir,
                    _out=sys.stdout,
                    _err=sys.stderr
                )
            except sh.ErrorReturnCode:
                sh.git.checkout(
                    '-b',
                    repo_branch,
                    _cwd=repo_dir,
                    _out=sys.stdout,
                    _err=sys.stderr
                )
        except sh.ErrorReturnCode as error:
            # NOTE: this should never happen
            raise StepRunnerException(
                f"Unexpected error checking out new or existing branch ({repo_branch})"
                f" from repository ({repo_url}): {error}"
            ) from error

        try:
            sh.git.config( # pylint: disable=no-member
                'user.email',
                user_email,
                _cwd=repo_dir,
                _out=sys.stdout,
                _err=sys.stderr
            )
            sh.git.config( # pylint: disable=no-member
                'user.name',
                user_name,
                _cwd=repo_dir,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            # NOTE: this should never happen
            raise StepRunnerException(
                f"Unexpected error configuring git user.email ({user_email})"
                f" and user.name ({user_name}) for repository ({repo_url})"
                f" in directory ({repo_dir}): {error}"
            ) from error

        return repo_dir

    @staticmethod
    def __get_repo_branch():
        try:
            return sh.git( # pylint: disable=no-member,too-many-function-args
                'rev-parse',
                '--abbrev-ref',
                'HEAD'
            ).rstrip()
        except sh.ErrorReturnCode as error:
            # NOTE: this should never happen
            raise StepRunnerException(
                "Unexpected error getting checkedout git repository branch"
                f" of the working directory: {error}"
            ) from error

    @staticmethod
    def __git_tag_and_push(repo_dir, tag, url=None, force_push_tags=False):
        """
        Raises
        ------
        StepRunnerException
        * if error pushing commits
        * if error tagging repository
        * if error pushing tags
        """

        git_push = sh.git.push.bake(url) if url else sh.git.push

        # push commits
        try:
            git_push(
                _cwd=repo_dir,
                _out=sys.stdout
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error pushing commits from repository directory ({repo_dir}) to"
                f" repository ({url}): {error}"
            ) from error

        # tag
        try:
            # NOTE:
            # this force is only needed locally in case of a re-run of the same pipeline
            # without a fresh check out. You will notice there is no force on the push
            # making this an acceptable work around to the issue since on the off chance
            # actually overwriting a tag with a different comment, the push will fail
            # because the tag will be attached to a different git hash.
            sh.git.tag(  # pylint: disable=no-member
                tag,
                '-f',
                _cwd=repo_dir,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error tagging repository ({repo_dir}) with tag ({tag}): {error}"
            ) from error

        git_push_additional_arguments = []
        if force_push_tags:
            git_push_additional_arguments += ["--force"]

        # push tag
        try:
            git_push(
                '--tag',
                *git_push_additional_arguments,
                _cwd=repo_dir,
                _out=sys.stdout
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error pushing tags from repository directory ({repo_dir}) to"
                f" repository ({url}): {error}"
            ) from error

    @staticmethod
    def __git_commit_file(git_commit_message, file_path, repo_dir):
        try:
            sh.git.add( # pylint: disable=no-member
                file_path,
                _cwd=repo_dir,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            # NOTE: this should never happen
            raise StepRunnerException(
                f"Unexpected error adding file ({file_path}) to commit"
                f" in git repository ({repo_dir}): {error}"
            ) from error

        try:
            sh.git.commit( # pylint: disable=no-member
                '--allow-empty',
                '--all',
                '--message', git_commit_message,
                _cwd=repo_dir,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            # NOTE: this should never happen
            raise StepRunnerException(
                f"Unexpected error commiting file ({file_path})"
                f" in git repository ({repo_dir}): {error}"
            ) from error

    @staticmethod
    def __argocd_sign_in(
        argocd_api,
        username,
        password,
        insecure=False
    ):
        """Signs into ArgoCD CLI.

        Raises
        ------
        StepRunnerException
            If error signing into ArgoCD CLI.
        """
        try:
            insecure_flag = None
            if insecure:
                insecure_flag = '--insecure'

            sh.argocd.login(  # pylint: disable=no-member
                argocd_api,
                f'--username={username}',
                f'--password={password}',
                insecure_flag,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(f"Error logging in to ArgoCD: {error}") from error

    def __argocd_add_target_cluster(
        self,
        kube_api,
        kube_api_token=None,
        kube_api_skip_tls=False
    ):
        """If the target cluster is not the default cluster then add that cluster to ArgoCD.

        **WARNING:*** have not re-integration tested this since refactor. Have a feeling that
        it does not work as expected. I have a feeling there is issues with the context names.

        Raises
        ------
        StepRunnerException
            If error adding cluster to ArgoCD
        """
        # If the cluster is an external cluster and an api token was provided,
        # add the cluster to ArgoCD
        if kube_api != DEFAULT_CONFIG['kube-api-uri']:
            context_name = f'{kube_api}-context'
            kubeconfig = f"""---
apiVersion: v1
kind: Config
current-context: {context_name}
clusters:
- cluster:
    kube-api-skip-tls: {str(kube_api_skip_tls).lower()}
    server: {kube_api}
  name: default-cluster
contexts:
- context:
    cluster: default-cluster
    user: default-user
  name: {context_name}
preferences:
users:
- name: default-user
  user:
    token: {kube_api_token}
"""

            config_argocd_cluster_context_file = self.write_working_file(
                filename='config-argocd-cluster-context.yaml',
                contents=bytes(kubeconfig, 'utf-8')
            )
            try:
                sh.argocd.cluster.add(  # pylint: disable=no-member
                    '--kubeconfig', config_argocd_cluster_context_file,
                    context_name,
                    _out=sys.stdout,
                    _err=sys.stderr
                )
            except sh.ErrorReturnCode as error:
                raise StepRunnerException(
                    f"Error adding cluster ({kube_api}) to ArgoCD: {error}"
                ) from error

    @staticmethod
    def __argocd_app_create_or_update( # pylint: disable=too-many-arguments
        argocd_app_name,
        repo,
        revision,
        path,
        dest_server,
        auto_sync,
        values_files
    ):
        """Creates or updates an ArtoCD App.

        Raises
        ------
        StepRunnerException
            If error creating or updating ArgoCD app.
        """
        try:
            if str(auto_sync).lower() == 'true':
                sync_policy = 'automated'
            else:
                sync_policy = 'none'

            values_params = None
            if values_files:
                values_params = []
                for value_file in values_files:
                    values_params += [f'--values={value_file}']

            sh.argocd.app.create(  # pylint: disable=no-member
                argocd_app_name,
                f'--repo={repo}',
                f'--revision={revision}',
                f'--path={path}',
                f'--dest-server={dest_server}',
                f'--dest-namespace={argocd_app_name}',
                f'--sync-policy={sync_policy}',
                values_params,
                '--upsert',
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error creating or updating ArgoCD app ({argocd_app_name}): {error}"
            ) from error

    @staticmethod
    def __argocd_app_sync(
        argocd_app_name,
        argocd_sync_timeout_seconds
    ):
        try:
            sh.argocd.app.sync(  # pylint: disable=no-member
                '--prune',
                '--timeout', argocd_sync_timeout_seconds,
                argocd_app_name,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error synchronization ArgoCD Application ({argocd_app_name}): {error}"
            ) from error

        try:
            sh.argocd.app.wait(  # pylint: disable=no-member
                '--timeout', argocd_sync_timeout_seconds,
                '--health',
                argocd_app_name,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error waiting for ArgoCD Application ({argocd_app_name}) synchronization: {error}"
            ) from error

    def __argocd_get_app_manifest(
        self,
        argocd_app_name,
        source='live'
    ):
        """Get ArgoCD Application manifest.

        Parameters
        ----------
        argocd_app_name : str
            Name of the ArgoCD Application to get the manifest for.
        source : str (live,git)
            Get the manifest from the 'live' version of the 'git' version.

        Returns
        -------
        str
            Path to the retrieved ArgoCD manifest file.

        Raises
        ------
        StepRunnerException
            If error getting ArogCD manifest.
        """
        arogcd_app_manifest_file = self.write_working_file('deploy_argocd_manifests.yml')
        try:
            sh.argocd.app.manifests(  # pylint: disable=no-member
                f'--source={source}',
                argocd_app_name,
                _out=arogcd_app_manifest_file,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error reading ArgoCD Application ({argocd_app_name}) manifest: {error}"
            ) from error

        return arogcd_app_manifest_file
