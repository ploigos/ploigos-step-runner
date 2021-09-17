"""`StepImplementer` for the `package` step using npm

"""
import os

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.shared.argocd_generic import ArgoCDGeneric

class ArgoCDDeploy(ArgoCDGeneric):
    """`StepImplementer` for the `package` step using npm.
    """

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
        deployment_config_repo_branch = self._get_repo_branch()
        deployment_config_helm_chart_path = self.get_value('deployment-config-helm-chart-path')
        deployment_config_destination_cluster_uri = self.get_value('kube-api-uri')
        deployment_config_destination_cluster_token = self.get_value('kube-api-token')
        deployment_config_helm_chart_environment_values_file = \
            self._get_deployment_config_helm_chart_environment_values_file()
        deployment_config_helm_chart_values_file_image_tag_yq_path = \
            self.get_value('deployment-config-helm-chart-values-file-image-tag-yq-path')
        deployment_config_helm_chart_additional_value_files = \
            self.get_value('deployment-config-helm-chart-additional-values-files')
        container_image_tag = self.get_value('container-image-tag')
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
            self._update_yaml_file_value(
                file=deployment_config_helm_chart_environment_values_file_path,
                yq_path=deployment_config_helm_chart_values_file_image_tag_yq_path,
                value=container_image_tag
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
            print("Add target cluster to ArgoCD")
            self._argocd_add_target_cluster(
                kube_api=deployment_config_destination_cluster_uri,
                kube_api_token=deployment_config_destination_cluster_token,
                kube_api_skip_tls=self.get_value('kube-api-skip-tls')
            )
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
                auto_sync=self.get_value('argocd-auto-sync'),
                values_files=argocd_values_files
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
