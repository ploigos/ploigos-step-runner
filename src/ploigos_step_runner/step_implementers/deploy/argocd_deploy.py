"""`StepImplementer` for the `deploy` step using ArgoCD.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key                       | Required? | Default  | Description
----------------------------------------|-----------|----------|---------------------------
`argocd-username`                       | Yes       |          | Username for accessing the ArgoCD API
`argocd-password`                       | Yes       |          | Password for accessing the ArgoCD API
`argocd-api`                            | Yes       |          | The ArgoCD API endpoint
`argocd-auto-sync`                      | Yes       | True     | If set to false, argo cd will sync only if \
                                                                 explicitly told to do so via the UI or CLI. \
                                                                 Otherwise it will sync if the repo contents have changed.
`argocd-skip-tls`                       | Yes       | False    | `False` to not ignore TLS issues when \
                                                                  authenticating with ArgoCD. True` to ignore TLS \
                                                                  issues when authenticating with ArgoCD.
`argocd-sync-timeout-seconds`           | Yes       | 60       | Number of seconds to wait for argocd to sync updates
`argocd-sync-retry-limit`               | No        | 3        | Value to pass to retry limit flag for argo sync
`argocd-sync-prune`                     | No        | True     |
`argocd-project`                        | Yes       | default  | ArgoCD Project to create/update the ArgoCD Application in
`argocd-add-or-update-target-cluster`   | No        | True     | `True` to automatically add or update target cluster information.\
                                                                 `False` to assume target cluster already in place.
`deployment-namespace`                  | No        |          | If not provided namespace name will be automatically generated
`deployment-config-repo`                | Yes       |          | The repo containing the helm chart definition
`deployment-config-helm-chart-path`     | Yes       | ./       | Directory containing the helm chart definition
`deployment-config-helm-chart-environment-values-file` \
                                        | No        | values-{ENV}.yaml \
                                                               | File to update with environment deployment specific information. \
                                                                 <br/>\
                                                                 Default value uses `environment` configuration option to calculate file name.
`deployment-config-helm-chart-additional-values-files` \
                                        | No        |          | Array of additional values files. \
                                                                 Paths must be relative to the given Helm Chart path (`deployment-config-helm-chart-path`). \
                                                                 <br/>\
                                                                 Does not need to include `deployment-config-helm-chart-environment-values-file` \
                                                                 as it will be automatically included as the last `--values` flag.
                                                                 <br/>\
                                                                 Used when createing the ArgoCD Application.\
                                                                 <br/><br/>\
                                                                 **NOTE:** Helm will always pick up `values.yaml`\
                                                                 by default whether or not additional values \
                                                                 files are provided, therefor no need to \
                                                                 explicitly provide.
`[deployment-config-helm-chart-values-file-container-image-address-yq-path, \
  deployment-config-helm-chart-values-file-image-tag-yq-path]` \
                                        | Yes       | `image` | YQ path to value in `deployment-config-helm-chart-environment-values-file` \
                                                                to update with the latest container image address before deployment. \
                                                                <br/>\
                                                                **SEE:**: https://github.com/mikefarah/yq for documentation on valid yq paths.
`kube-api-uri`                          | Yes       | https://kubernetes.default.svc | k8s API endpoint
`kube-api-token`                        | No        |          | k8s API token. This is used to add an external \
                                                                 k8s cluster into argocd. It is required if the \
                                                                 cluster has not already been added to ArgoCD. \
                                                                 The token should be persistent \
                                                                 (.e.g, a service account token) and have cluster \
                                                                 admin access.
`kube-api-skip-tls`                     | Yes       | False    | Whether or not to skip tls verification when \
                                                                 authenticating to an external k8s cluster. \
                                                                 Used when a new cluster is registered with \
                                                                 argocd.
`git-email`                             | Yes       |          | Git email for commit
`git-name`                              | Yes       | `Ploigos Robot` | Git name for commit
`git-username`                          | No        |          | If the helm config repo s accessed via http(s) this must be supplied
`git-password`                          | No        |          | If the helm config repo is accessed via http(s) this must be supplied
`tag`                                   | No        | latest   | The git tag to apply to the config repo. \
                                                                 If not supplied `version` will be used. \
                                                                 If `version` not supplied `latest` will be used.
`version`                               | No        | latest   | Ignored if `tag` is provided. \
                                                                 The git tag to apply to the config repo if `tag` is not supplied. \
                                                                 If `tag` and `version` not supplied `latest` will be used.
`force-push-tags`                       | No        | False    | Force push Git Tags
`additional-helm-values-files`          | No        | []       | Array of value files to add to argocd app for helm use
`[container-image-pull-registry, \
  container-image-push-registry, \
  container-image-registry]`            | Maybe     |          | If `use-container-image-short-addres` is `True`, \
                                                                 container image registry to pull container image from when deploying.

`[container-image-pull-repository, \
  container-image-push-repository, \
  container-image-repository]`          | Yes       |          | Container image repository within the given container image registry \
                                                                 to pull container image from when deploying.
`[container-image-pull-digest,
  container-image-push-digest,
  container-image-digest]               | Maybe     |          | If `use-container-image-digest` is `True`,
                                                                 container image digest to pull container image with when deploying.
`[container-image-pull-tag,
  container-image-push-tag,
  container-image-tag]                  | Maybe     |          | If `use-container-image-digest` is `False`,
                                                                 container image tag to pull container image with when deploying.
`use-container-image-short-addres`      | No        | `False`  | If `True` then use container image short address (no registry).\
                                                                 If `False` then use container image full address (including registry).
`use-container-image-digest`            | No        | `True`   | If `True` then use container image digest in container image address when \
                                                                 pulling container image for deployment.<br/>\
                                                                 If `False` then use container image tag in container image address when \
                                                                 pulling container image for deployment.
`organization`                          | Yes       |          | Used to build ArgoCD application name.
`application-name`                      | Yes       |          | Used to build ArgoCD application name.
`service-name`                          | Yes       |          | Used to build ArgoCD application name.
`branch`                                | Yes       |          | Used to build ArgoCD application name.

Results
-------
Results output by this step.

Result Key                         | Description
-----------------------------------|------------
`argocd-app-name`                  | The argocd app name that was created or updated
`deployed-host-urls`               | The host URLs deployed by ArgoCD (Ingress/Route resources)
`config-repo-git-tag`              | The git tag applied to the configuration repo for deployment
`argocd-deployed-manifest`         | The generated yml file used for deployment.
`container-image-deployed-address` | Container image address that was deployed.
"""# pylint: disable=line-too-long
import os
import re

from ploigos_step_runner import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared import (ArgoCDGeneric,
                                                          ContainerDeployMixin)

DEFAULT_CONFIG = {
    'argocd-sync-timeout-seconds': 60,
    'argocd-sync-retry-limit': 3,
    'argocd-auto-sync': True,
    'argocd-skip-tls' : False,
    'argocd-sync-prune': True,
    'argocd-project': 'default',
    'deployment-config-helm-chart-path': './',
    'deployment-config-helm-chart-additional-values-files': [],
    'additional-helm-values-files': [],
    'deployment-config-helm-chart-values-file-container-image-address-yq-path': 'image',
    'force-push-tags': False,
    'kube-api-skip-tls': False,
    'kube-api-uri': 'https://kubernetes.default.svc',
    'git-name': 'Ploigos Robot',
    'argocd-add-or-update-target-cluster': True
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'argocd-username',
    'argocd-password',
    'argocd-api',
    'argocd-skip-tls',
    'argocd-project',
    'deployment-config-repo',
    'deployment-config-helm-chart-path',
    [
        'deployment-config-helm-chart-values-file-container-image-address-yq-path',
        'deployment-config-helm-chart-values-file-image-tag-yq-path'
    ],
    'git-email',
    'git-name',
    'organization',
    'application-name',
    'service-name',
    'branch'
]

GIT_AUTHENTICATION_CONFIG = {
    'git-username': None,
    'git-password': None
}

class ArgoCDDeploy(ContainerDeployMixin, ArgoCDGeneric):
    """`StepImplementer` for the `deploy` step using ArgoCD.
    """

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
        return {**ContainerDeployMixin.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS + \
            ContainerDeployMixin._required_config_or_result_keys()

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

    def _run_step(self):  # pylint: disable=too-many-locals, too-many-statements
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # get input
        deployment_config_repo = self.get_value('deployment-config-repo')
        deployment_config_repo_branch = self._get_repo_branch()
        deployment_config_helm_chart_path = self.get_value('deployment-config-helm-chart-path')
        deployment_config_destination_cluster_uri = self.get_value('kube-api-uri')
        deployment_config_destination_cluster_token = self.get_value('kube-api-token')
        deployment_config_helm_chart_environment_values_file = \
            self._get_deployment_config_helm_chart_environment_values_file()
        deployment_config_helm_chart_values_file_container_image_address_yq_path = self.get_value([
            'deployment-config-helm-chart-values-file-container-image-address-yq-path',
            'deployment-config-helm-chart-values-file-image-tag-yq-path'
        ])
        deployment_config_helm_chart_additional_value_files = \
            self.get_value('deployment-config-helm-chart-additional-values-files')
        force_push_tags = self.get_value('force-push-tags')
        additional_helm_values_files = self.get_value('additional-helm-values-files')

        try:
            argocd_app_name = self._get_app_name()
            step_result.add_artifact(
                name='argocd-app-name',
                value=argocd_app_name
            )

            # clone the configuration repository
            print("Clone the configuration repository")
            clone_repo_dir_name = 'deployment-config-repo'
            deployment_config_repo_dir = self._clone_repo(
                repo_dir=self.create_working_dir_sub_dir(clone_repo_dir_name),
                repo_url=deployment_config_repo,
                repo_branch=deployment_config_repo_branch,
                git_email=self.get_value('git-email'),
                git_name=self.get_value('git-name'),
                username = self.get_value('git-username'),
                password = self.get_value('git-password')
            )

            # update values file, commit it, push it, and tag it
            print("Update the environment values file")
            deployment_config_helm_chart_environment_values_file_path = os.path.join(
                deployment_config_repo_dir,
                deployment_config_helm_chart_path,
                deployment_config_helm_chart_environment_values_file
            )
            container_image_address = self._get_deploy_time_container_image_address()
            self._update_yaml_file_value(
                file=deployment_config_helm_chart_environment_values_file_path,
                yq_path=deployment_config_helm_chart_values_file_container_image_address_yq_path,
                value=container_image_address
            )
            step_result.add_artifact(
                name='container-image-deployed-address',
                value=container_image_address,
                description='Container image address used to deploy the container.'
            )

            print("Commit the updated environment values file")
            self._git_commit_file(
                git_commit_message=f'Updating values for deployment to {self.environment}',
                file_path=os.path.join(
                    deployment_config_helm_chart_path,
                    deployment_config_helm_chart_environment_values_file
                ),
                repo_dir=deployment_config_repo_dir
            )
            print("Tag and push the updated environment values file")
            deployment_config_repo_tag = self._get_deployment_config_repo_tag()
            self._git_tag_and_push_deployment_config_repo(
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
            self._argocd_sign_in(
                argocd_api=self.get_value('argocd-api'),
                username=self.get_value('argocd-username'),
                password=self.get_value('argocd-password'),
                insecure=self.get_value('argocd-skip-tls')
            )

            add_or_update_target_cluster = self.get_value('argocd-add-or-update-target-cluster')
            if add_or_update_target_cluster:
                print("Add target cluster to ArgoCD")
                self._argocd_add_target_cluster(
                    kube_api=deployment_config_destination_cluster_uri,
                    kube_api_token=deployment_config_destination_cluster_token,
                    kube_api_skip_tls=self.get_value('kube-api-skip-tls')
                )

            print("Determine deployment namespace")
            deployment_namespace = self.get_value('deployment-namespace')
            if deployment_namespace:
                print(f"  Using user provided namespace name: {deployment_namespace}")
            else:
                deployment_namespace = argocd_app_name
                print(f"  Using auto generated namespace name: {deployment_namespace}")

            print(f"Create or update ArgoCD Application ({argocd_app_name})")
            argocd_values_files = []
            argocd_values_files += deployment_config_helm_chart_additional_value_files
            argocd_values_files += [deployment_config_helm_chart_environment_values_file]
            argocd_values_files += additional_helm_values_files
            self._argocd_app_create_or_update(
                argocd_app_name=argocd_app_name,
                repo=deployment_config_repo,
                revision=deployment_config_repo_tag,
                path=deployment_config_helm_chart_path,
                dest_server=deployment_config_destination_cluster_uri,
                dest_namespace=deployment_namespace,
                auto_sync=self.get_value('argocd-auto-sync'),
                values_files=argocd_values_files,
                project=self.get_value('argocd-project')
            )

            # sync and wait for the sync of the ArgoCD app
            print(f"Sync (and wait for) ArgoCD Application ({argocd_app_name})")
            self._argocd_app_sync(
                argocd_app_name=argocd_app_name,
                argocd_sync_timeout_seconds=self.get_value('argocd-sync-timeout-seconds'),
                argocd_sync_retry_limit=self.get_value('argocd-sync-retry-limit'),
                argocd_sync_prune=self.get_value('argocd-sync-prune')
            )

            # get the ArgoCD app manifest that was synced
            print(f"Get ArgoCD Application ({argocd_app_name}) synced manifest")
            argocd_app_manifest_file = self._argocd_get_app_manifest(
                argocd_app_name=argocd_app_name
            )
            step_result.add_artifact(
                name='argocd-deployed-manifest',
                value=argocd_app_manifest_file
            )

            # determine the deployed host URLs
            print(
                "Determine the deployed host URLs for the synced"
                f" ArgoCD Application (({argocd_app_name})"
            )
            deployed_host_urls = self._get_deployed_host_urls(
                manifest_path=argocd_app_manifest_file
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
