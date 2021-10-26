# pylint: disable=too-many-lines
"""Abstract parent class for StepImplementers that use ArgoCD.
"""

import re
import sys
from io import StringIO

import sh
import yaml
from ploigos_step_runner import StepImplementer
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback

KUBE_LABEL_NOT_SAFE_CHARS_REGEX = r"[^a-zA-Z0-9\-_\.]"
KUBE_LABEL_NOT_SAFE_CHARS_REGEX = r"(^[^a-z]+)|([^-a-z0-9])+|([^a-z0-9]$)+"
KUBE_LABEL_NOT_SAFE_BEGINING_END_CHARS_REGEX = r"^[^a-z]*|[^a-z0-9]*$"
KUBE_LABEL_MAX_LENGTH = 52
KUBE_LABEL_REPLACEMENT_CHAR = '-'

class ArgoCDGeneric(StepImplementer):
    """Abstract parent class for StepImplementers that use ArgoCD.
    """

    GIT_REPO_REGEX = re.compile(r"(?P<protocol>^https:\/\/|^http:\/\/)?(?P<address>.*$)")
    ARGOCD_OP_IN_PROGRESS_REGEX = re.compile(
        r'.*FailedPrecondition.*another\s+operation\s+is\s+already\s+in\s+progress',
        re.DOTALL
    )
    MAX_ATTEMPT_TO_WAIT_FOR_ARGOCD_OP_RETRIES = 2

    def _get_deployment_config_helm_chart_environment_values_file(self):
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

    def _update_yaml_file_value(self, file, yq_path, value):
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

    def _git_tag_and_push_deployment_config_repo(
        self,
        deployment_config_repo,
        deployment_config_repo_dir,
        deployment_config_repo_tag,
        force_push_tags
    ):
        deployment_config_repo_match = ArgoCDGeneric.GIT_REPO_REGEX.match(deployment_config_repo)
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
            ArgoCDGeneric._git_tag_and_push(
                repo_dir=deployment_config_repo_dir,
                tag=deployment_config_repo_tag,
                url=deployment_config_repo_with_user_pass,
                force_push_tags=force_push_tags
            )
        else:
            ArgoCDGeneric._git_tag_and_push(
                repo_dir=deployment_config_repo_dir,
                tag=deployment_config_repo_tag,
                force_push_tags=force_push_tags
            )

    def _get_app_name(self):
        repo_branch = self._get_repo_branch()
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

        # be sure app name is DNS-1035 compliant
        # first replace all not safe characters with -
        app_name = re.sub(
            KUBE_LABEL_NOT_SAFE_CHARS_REGEX,
            '-',
            app_name
        )
        # second, replace any leading or trailing - with blanks
        app_name = re.sub(
            KUBE_LABEL_NOT_SAFE_BEGINING_END_CHARS_REGEX,
            '',
            app_name
        )

        return app_name

    def _get_deployment_config_repo_tag(self):
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
    def _get_deployed_host_urls( # pylint: disable=too-many-branches,too-many-nested-blocks
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
        with open(manifest_path, encoding='utf-8') as file:
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
    def _clone_repo( # pylint: disable=too-many-arguments
        repo_dir,
        repo_url,
        repo_branch,
        git_email,
        git_name,
	  username=None,
	  password=None
    ):
        """Clones and checks out the deployment configuration repository.

        Parameters
        ----------
        repo_dir : str
            Path to where to clone the repository
        repo_uri : str
            URI of the repository to clone.
        git_email : str
            email to use when performing git operations in the cloned repository
        git_name : str
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
        repo_match = ArgoCDGeneric.GIT_REPO_REGEX.match(repo_url)
        repo_protocol = repo_match.groupdict()['protocol']
        repo_address = repo_match.groupdict()['address']
        # if deployment config repo uses http/https push using user/pass
        # else push using ssh
        if username and password and repo_protocol and re.match(
            r'^http://|^https://',
            repo_protocol
        ):
            repo_url_with_auth = \
                f"{repo_protocol}{username}:{password}" \
                f"@{repo_address}"
        else:
            repo_url_with_auth = repo_url
        try:
            sh.git.clone( # pylint: disable=no-member
                repo_url_with_auth,
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
                git_email,
                _cwd=repo_dir,
                _out=sys.stdout,
                _err=sys.stderr
            )
            sh.git.config( # pylint: disable=no-member
                'user.name',
                git_name,
                _cwd=repo_dir,
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            # NOTE: this should never happen
            raise StepRunnerException(
                f"Unexpected error configuring git user.email ({git_email})"
                f" and user.name ({git_name}) for repository ({repo_url})"
                f" in directory ({repo_dir}): {error}"
            ) from error

        return repo_dir

    def _get_repo_branch(self):
        return self.get_value('branch')

    @staticmethod
    def _git_tag_and_push(repo_dir, tag, url=None, force_push_tags=False):
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
    def _git_commit_file(git_commit_message, file_path, repo_dir):
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
    def _argocd_sign_in(
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

    def _argocd_add_target_cluster(
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
        # If the cluster not the default ArgoCD cluster installed by default
        # add the cluster to ArgoCD
        if kube_api != 'https://kubernetes.default.svc':
            context_name = f'{kube_api}-context'
            kubeconfig = f"""---
apiVersion: v1
kind: Config
current-context: {context_name}
clusters:
- cluster:
    insecure-skip-tls-verify: {str(kube_api_skip_tls).lower()}
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
    def _argocd_app_create_or_update( # pylint: disable=too-many-arguments
        argocd_app_name,
        project,
        repo,
        revision,
        path,
        dest_server,
        dest_namespace,
        auto_sync,
        values_files
    ):
        """Creates or updates an ArgoCD App.

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
                f'--dest-namespace={dest_namespace}',
                f'--sync-policy={sync_policy}',
                f'--project={project}',
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
    def _argocd_app_sync(
        argocd_app_name,
        argocd_sync_timeout_seconds,
        argocd_sync_retry_limit,
        argocd_sync_prune=True
    ): # pylint: disable=line-too-long
        # add any additional flags
        argocd_sync_additional_flags = []
        if argocd_sync_prune:
            argocd_sync_additional_flags.append('--prune')

        for wait_for_op_retry in range(ArgoCDGeneric.MAX_ATTEMPT_TO_WAIT_FOR_ARGOCD_OP_RETRIES):
            # wait for any existing operations before requesting new synchronization
            #
            # NOTE: attempted work around for 'FailedPrecondition desc = another operation is
            #       already in progress' error
            # SEE: https://github.com/argoproj/argo-cd/issues/4505
            try:
                print(
                    f"Wait for existing ArgoCD operations on app ({argocd_app_name})"
                    " before requesting synchronization."
                )
                sh.argocd.app.wait( # pylint: disable=no-member
                    argocd_app_name,
                    '--operation',
                    '--timeout', argocd_sync_timeout_seconds,
                    _out=sys.stdout,
                    _err=sys.stderr
                )
            except sh.ErrorReturnCode as error:
                raise StepRunnerException(
                    f"Error waiting for ArgoCD Application ({argocd_app_name}) existing operation"
                    f" before requesting new synchronization: {error}"
                ) from error

            # sync app
            argocd_output_buff = StringIO()
            try:
                print(f"Request synchronization of ArgoCD app ({argocd_app_name}).")
                out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stdout,
                    argocd_output_buff
                ])
                err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    sys.stderr,
                    argocd_output_buff
                ])

                sh.argocd.app.sync(  # pylint: disable=no-member
                    *argocd_sync_additional_flags,
                    '--timeout', argocd_sync_timeout_seconds,
                    '--retry-limit', argocd_sync_retry_limit,
                    argocd_app_name,
                    _out=out_callback,
                    _err=err_callback
                )

                break
            except sh.ErrorReturnCode as error:
                # if error syncing because of in progress op
                # try again to wait for in progress op and do sync again
                #
                # NOTE: this can happen if we do the wait for op, and then an op starts and then
                #       we try to do a sync
                #
                # SEE: https://github.com/argoproj/argo-cd/issues/4505
                if re.match(ArgoCDGeneric.ARGOCD_OP_IN_PROGRESS_REGEX, argocd_output_buff.getvalue()):
                    print(
                        f"ArgoCD Application ({argocd_app_name}) has an existing operation"
                        " that started after we already waited for existing operations but"
                        f" before we tried to do a sync. Try ({wait_for_op_retry}) again"
                        " to wait for the operation"
                    )
                    continue

                if not argocd_sync_prune:
                    prune_warning = ". Sync 'prune' option is disabled." \
                        " If sync error (see logs) was due to resource(s) that need to be pruned," \
                        " and the pruneable resources are intentionally there then see the ArgoCD" \
                        " documentation for instructions for argo to ignore the resource(s)." \
                        " See: https://argoproj.github.io/argo-cd/user-guide/sync-options/#no-prune-resources" \
                        " and https://argoproj.github.io/argo-cd/user-guide/compare-options/#ignoring-resources-that-are-extraneous"
                else:
                    prune_warning = ""

                raise StepRunnerException(
                    f"Error synchronization ArgoCD Application ({argocd_app_name})"
                    f"{prune_warning}: {error}"
                ) from error

        # wait for sync to finish
        try:
            print(f"Wait for synchronization of ArgoCD app ({argocd_app_name}) to finish.")
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

    def _argocd_get_app_manifest(
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
            If error getting ArgoCD manifest.
        """
        argocd_app_manifest_file = self.write_working_file('deploy_argocd_manifests.yml')
        try:
            sh.argocd.app.manifests(  # pylint: disable=no-member
                f'--source={source}',
                argocd_app_name,
                _out=argocd_app_manifest_file,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error reading ArgoCD Application ({argocd_app_name}) manifest: {error}"
            ) from error

        return argocd_app_manifest_file
