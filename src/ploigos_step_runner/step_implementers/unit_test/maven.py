"""DEPRECATED: use ploigos_step_runner.step_implementers.unit_test.MavenTest instead.

This is an alias to MavenTest so as to keep things backwards compatible,
but eventually should/can will be removed.
"""

from ploigos_step_runner.step_implementers.unit_test.maven_test import MavenTest

class Maven(MavenTest):
    """DEPRECATED: use ploigos_step_runner.step_implementers.unit_test.MavenTest instead.

    This is an alias to MavenTest so as to keep things backwards compatible,
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

        print("DEPRECATED: use ploigos_step_runner.step_implementers.unit_test.MavenTest instead.")
