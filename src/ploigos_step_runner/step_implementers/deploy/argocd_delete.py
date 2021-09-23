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
`argocd-cascade`            | No        | True       | Perform a cascaded deletion \
                                                       of all application resources
`argocd-propagation-policy` | No        | foreground | Policy for deletion of application's \
                                                       resources. One of: foreground|background
"""

import sys
import sh
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.shared.argocd_generic import ArgoCDGeneric

DEFAULT_CONFIG = {
    'argocd-cascade': True,
    'argocd-propagation-policy': 'foreground'
}

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
        return {**ArgoCDGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

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
                name='argocd-app-name',
                value = argocd_app_name
            )

            print("Sign into ArgoCD")
            self._argocd_sign_in(
                argocd_api = self._get_argocd_api(),
                username = self._get_argocd_username(),
                password = self._get_argocd_password(),
                insecure = self._get_argocd_skip_tls()
            )

            print("Add target cluster to ArgoCD")
            self._argocd_add_target_cluster(
                kube_api = self._get_kube_api_uri(),
                kube_api_token = self._get_kube_api_token(),
                kube_api_skip_tls = self._get_kube_api_skip_tls()
            )

            print(f"Delete ArgoCD Application ({argocd_app_name})")

            self._argocd_app_delete(
                argocd_app_name,
                argocd_cascade = self._get_argocd_cascade(),
                argocd_propagation_policy = self._get_argocd_propagation_policy()
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

    def _get_argocd_cascade(self):
        """
        :return: true if cascaded deletion of all application resources
        """
        return self.get_value('argocd-cascade')

    def _get_argocd_propagation_policy(self):
        """
        :return: true if cascaded deletion of all application resources
        """
        return self.get_value('argocd-propagation-policy')
