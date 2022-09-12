import os
from io import StringIO
from unittest.mock import patch

import sh
from ploigos_step_runner.results import StepResultArtifact
from ploigos_step_runner.step_implementers.shared import AdHoc
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any


class TestAdHocPackage__run_step(BaseStepImplementerTestCase):
    # Given a shell command, 'npm'
    @patch('sh.bash', create=True)
    def test_run_shell_command(self, bash_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            config = {
                'command': 'echo Hello World!'
            }

            # Given an NpmPackage step implementer
            ad_hoc_test = self.create_given_step_implementer(
                AdHoc,
                step_config=config,
                parent_work_dir_path=working_dir_path
            )

            # When I run the step
            ad_hoc_test.run_step()

            # Then it should run a shell command, 'npm test'
            bash_shell_command_mock.assert_any_call(
                '-c',
                'echo Hello World!',
                _out=Any(StringIO),
                _err=Any(StringIO)
            )
