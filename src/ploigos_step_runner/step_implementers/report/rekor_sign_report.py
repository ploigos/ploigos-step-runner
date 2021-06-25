"""Implementation of RekorGeneric in the Report step.

artifact_to_sign_uri_config_key is set to `results-archive-uri` as
this is the key used to obtain the artifact that needs to be
signed by rekor.

"""

from ploigos_step_runner.step_implementers.shared.rekor_sign_generic import RekorSignGeneric

class RekorSignReport(RekorSignGeneric):
    """ Rekor implementation specific to report
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
            environment=environment,
            artifact_to_sign_uri_config_key='results-archive-uri'
        )
