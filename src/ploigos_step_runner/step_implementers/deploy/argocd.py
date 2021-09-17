"""DEPRECATED: use ploigos_step_runner.step_implementers.deploy.ArgoCDDeploy instead.

This is an alias to ArgoCDDeploy so as to keep things backwards compatible,
but eventually should/can will be removed.
"""

from ploigos_step_runner.step_implementers.deploy.argocd_deploy import ArgoCDDeploy

class ArgoCD(ArgoCDDeploy):
    """DEPRECATED: use ploigos_step_runner.step_implementers.deploy.ArgoCDDeploy instead.

    This is an alias to ArgoCDDeploy so as to keep things backwards compatible,
    but eventually should/can will be removed.
    """
    def __init__(  # pylint: disable=too-many-arguments
            self,
            workflow_result,
            parent_work_dir_path,
            config,
            environment=None
    ):
        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment
        )

        print("DEPRECATED: use ploigos_step_runner.step_implementers.deploy.ArgoCDDeploy instead.")
