
import os
from base64 import b64decode
from unittest.mock import patch

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import WorkflowResult
from ploigos_step_runner.step_implementers.push_artifacts import \
    NpmPushArtifacts
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestStepImplementerNpmPushArtifacts___init__(BaseStepImplementerTestCase):
    def test_defaults(self):

        """ Assemble """
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        step_config = {
            "npm-registry": "https://werock.com",
            "npm-user": "npm-user-name",
            "npm-password": "npm-password"
        }

        """ Act """
        step_implementer = self.create_given_step_implementer(
            step_implementer=NpmPushArtifacts,
            step_config=step_config,
            step_name='push-artifacts',
            implementer='NpmPushArtifacts',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

        """ Assert """
        self.assertIsNotNone(step_implementer)

    def test_config_registry(self):
        self.assertEqual(
            NpmPushArtifacts._required_config_or_result_keys(),
            [
                'npm-registry',
                'npm-user',
                'npm-password'
            ]
        )

    @patch('sh.npm', create=True)# Given a shell command, 'npm'
    @patch('os.path.exists', side_effect=lambda filename: filename == 'package.json')# Given that a file named package.json exists
    def test_run_publish_shell_command_successfully(self, os_path_exists_mock, npm_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            # Given an NpmTest step implementer that is configured to run 'npm install' before running the unit tests
            npm_test = self.create_given_step_implementer(
                NpmPushArtifacts,
                step_config = {
                    "npm-registry": "https://werock.com",
                    "npm-user": "npm-user-name",
                    "npm-password": "npm-password"
                },
                parent_work_dir_path=working_dir_path
            )

            # When I run the step
            step_result = npm_test.run_step()

            """ Assert """
            # Then it should run the npm shell command with "publish" as the first argument
            args, kwargs = npm_shell_command_mock.call_args
            self.assertEqual(args[0], "publish") # first positional argument to sh.npm

            self.assertTrue(step_result.success)

    @patch('sh.npm', create=True, side_effect=StepRunnerException("Test Error"))
    @patch('os.path.exists', side_effect=lambda filename: filename == 'package.json')
    def test_run_publish_shell_command_with_error(self, os_path_exists_mock, npm_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            # Given an NpmTest step implementer that is configured to run 'npm install' before running the unit tests
            npm_test = self.create_given_step_implementer(
                NpmPushArtifacts,
                step_config={
                    "npm-registry": "https://werock.com",
                    "npm-user": "npm-user-name",
                    "npm-password": "npm-password"
                },
                parent_work_dir_path=working_dir_path
            )

            # When I run the step
            step_result = npm_test.run_step()

            """ Assert """
            self.assertFalse(step_result.success)
            expected_message = "NPM publish failure.  See 'npm_publish_output.txt' report artifacts for details: Test Error"
            self.assertEqual(expected_message, step_result.message)

    @patch('sh.npm', create=True)
    @patch('os.path.exists', side_effect=lambda filename: filename == 'package.json')
    def test_run_publish_shell_command_with_environment_vars(self, os_path_exists_mock, npm_shell_command_mock):

        # Given a working directory
        with TempDirectory() as temp_dir:
            working_dir_path = os.path.join(temp_dir.path, 'working')

            # Given an NpmTest step implementer that is configured to run 'npm install' before running the unit tests
            npm_test = self.create_given_step_implementer(
                NpmPushArtifacts,
                step_config={
                    "npm-registry": "https://werock.com",
                    "npm-user": "npm-user-name",
                    "npm-password": "npm-password"
                },
                parent_work_dir_path=working_dir_path
            )

            # When I run the step
            npm_test.run_step()

            """ Assert """
            # Then it should run the npm shell command with environment variables like:
            args, kwargs = npm_shell_command_mock.call_args
            actual_env_args = kwargs['_env'] # environment vars passed to sh.npm
            self.assertEqual(actual_env_args['NPM_CONFIG_REGISTRY'],"https://werock.com")

            # Then the NPM_CONFIG__AUTH env variable should be the concatenated, base 64 encoded username & password.
            # NOTE: .encode() does not base 64 encode. It just gets the bytes so they can be bassed to b64decode().
            self.assertEqual(b64decode(actual_env_args['NPM_CONFIG__AUTH'].encode()), b'npm-user-name:npm-password')

"""
Test Cases

1) DONE - NpmPushArtifacts class can instantiate
2) DONE - NpmPushArtifacts is configured properly
 - contains a valid config value for: NPM REGISTRY
 - contains a valid config value for: NPM USER NAME
 - contains a valid config value for: NPM USER PASSWORD
 2.a)  NpmPushArtifacts is configured improperly - No registry provided
 2.b)  NpmPushArtifacts is configured improperly - No user name
 2.c)  NpmPushArtifacts is configured improperly - No user password
3) DONE - NpmPushArtifacts calls 'npm publish' successfully
    CRITERIA -
    3.a) test that there is an npm_publish_outputs.txt file
4) NpmPushArtifacts calls 'npm publish' and there is a failure
    4.a) an execption message if provided and the step result success is false

"""
