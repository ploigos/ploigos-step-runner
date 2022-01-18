# pylint: disable=too-many-lines
"""`StepImplementer` for the `delete` step using ArgoCD.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key           | Required? | Default    | Description
----------------------------|-----------|------------|---------------------------
`application-name`          | Yes       |            | Used to build ArgoCD application name.
`argocd-api`                | Yes       |            | The ArgoCD API endpoint
`argocd-cascade`            | Yes       | True       | Perform a cascaded deletion of all \
                                                       application resources
`argocd-password`           | Yes       |            | Password for accessing the ArgoCD API
`argocd-propagation-policy` | Yes       | foreground | Policy for deletion of application's \
                                                       resources. One of: foreground|background
`argocd-skip-tls`           | Yes       | False      | `False` to not ignore TLS issues when \
                                                       authenticating with ArgoCD. True` to \
                                                       ignore TLS issues when authenticating \
                                                       with ArgoCD.
`argocd-username`           | Yes       |            | Username for accessing the ArgoCD API
`branch`                    | Yes       |            | Used to build ArgoCD application name.
`kube-api-skip-tls`         | Yes       | False      | Whether or not to skip tls verification \
                                                       when authenticating to an external k8s \
                                                       cluster. Used when a new cluster is \
                                                       registered with argocd.
`kube-api-token`            | No        |            | k8s API token. This is used to add an \
                                                       external k8s cluster into argocd. It is \
                                                       required if the cluster has not already \
                                                       been added to ArgoCD. The token should be \
                                                       persistent (.e.g, a service account token) \
                                                       and have cluster admin access.
`kube-api-uri`              | Yes       | https://kubernetes.default.svc \
                                                     | k8s API endpoint
`organization`              | Yes       |            | Used to build ArgoCD application name.
`service-name`              | Yes       |            | Used to build ArgoCD application name.
"""

import sys
import sh
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementers.shared import ArgoCDGeneric

DEFAULT_CONFIG = {
    'argocd-cascade': True,
    'argocd-propagation-policy': 'foreground',
    'argocd-skip-tls': False,
    'kube-api-skip-tls': False,
    'kube-api-uri': 'https://kubernetes.default.svc'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'application-name',
    'argocd-api',
    'argocd-cascade',
    'argocd-password',
    'argocd-propagation-policy',
    'argocd-skip-tls',
    'argocd-username',
    'branch',
    'kube-api-skip-tls',
    'kube-api-uri',
    'organization',
    'service-name'
]

class ArgoCDDelete(ArgoCDGeneric):
    """
    `StepImplementer` for the ArgoCD delete step.
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
        return {**DEFAULT_CONFIG}

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

    def _run_step(self):  # pylint: disable=too-many-locals
        """
        Runs the step implemented by this StepImplementer to delete a ArgoCD
        application by name.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        try:
            argocd_app_name = self._get_app_name()
            step_result.add_artifact(
                name = 'argocd-app-name',
                value = argocd_app_name
            )

            print("Sign into ArgoCD")
            self._argocd_sign_in(
                argocd_api = self.argocd_api,
                username = self.argocd_username,
                password = self.argocd_password,
                insecure = self.argocd_skip_tls
            )

            print(f"Delete ArgoCD Application ({argocd_app_name})")

            self._argocd_app_delete(
                argocd_app_name,
                argocd_cascade = self.argocd_cascade,
                argocd_propagation_policy = self.argocd_propagation_policy
            )

        except StepRunnerException as error:
            step_result.success = False
            step_result.message = f"Error deleting environment ({self.environment}):" \
                                  f" {str(error)}"

        return step_result

    @classmethod
    def _argocd_app_delete( # pylint: disable=too-many-arguments
            cls,
            argocd_app_name,
            argocd_cascade,
            argocd_propagation_policy
    ):
        """Delete a ArgoCD App by name.

        Raises
        ------
        StepRunnerException
            If error deleting ArgoCD app.
        """
        try:
            sh.argocd.app.delete(  # pylint: disable=no-member
                argocd_app_name,
                f'--cascade={argocd_cascade}',
                f'--propagation-policy={argocd_propagation_policy}',
                '--yes',
                _out=sys.stdout,
                _err=sys.stderr
            )
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error deleting ArgoCD app ({argocd_app_name}): {error}"
            ) from error

    @property
    def argocd_cascade(self):
        """
        Returns
        -------
        bool
            True for cascaded deletion; False otherwise
        """
        return self.get_value('argocd-cascade')

    @property
    def argocd_propagation_policy(self):
        """
        Returns
        -------
        str
            Value for the k8s delete propagation policy: parent-first (background), parent-last \
            (foreground), or no-op (orphan)
        """
        return self.get_value('argocd-propagation-policy')
