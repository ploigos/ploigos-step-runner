# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
from io import IOBase
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.tag_source import Git
from ploigos_step_runner.step_result import StepResult


class TestStepImplementerTagSourceGit(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Git,
            step_config=step_config,
            step_name='tag-source',
            implementer='Git',
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

# TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = Git.step_implementer_config_defaults()
        expected_defaults = {}
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Git._required_config_or_result_keys()
        expected_required_keys = []
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
         with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_missing_git_username(self):
         with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                r"Either 'git-username' or 'git-password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_missing_git_password(self):
         with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {
                'git-username': 'git-username'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            with self.assertRaisesRegex(
                StepRunnerException,
                r"Either 'git-username' or 'git-password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()


# TESTS FOR _run_step

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_pass(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_tag_side_effect():
                return tag
            get_tag_mock.side_effect = get_tag_side_effect

            def git_url_side_effect():
                return url
            git_url_mock.side_effect = git_url_side_effect


            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            get_tag_mock.assert_called_once_with()
            git_tag_mock.assert_called_once_with(tag)
            git_url_mock.assert_called_once_with()
            git_push_mock.assert_called_once_with(None)

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_pass_http(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'http://git.ploigos.xyz/ploigos-references/ploigos-reference-app-quarkus-rest-json.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }

            artifact_config = {
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_tag_side_effect():
                return tag
            get_tag_mock.side_effect = get_tag_side_effect

            def git_url_side_effect():
                return url
            git_url_mock.side_effect = git_url_side_effect


            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            get_tag_mock.assert_called_once_with()
            git_tag_mock.assert_called_once_with(tag)
            git_url_mock.assert_called_once_with()
            git_push_mock.assert_called_once_with('http://git-username:git-password@' + url[7:])

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_pass_https(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'https://git.ploigos.xyz/ploigos-references/ploigos-reference-app-quarkus-rest-json.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_tag_side_effect():
                return tag
            get_tag_mock.side_effect = get_tag_side_effect

            def git_url_side_effect():
                return url
            git_url_mock.side_effect = git_url_side_effect


            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            get_tag_mock.assert_called_once_with()
            git_tag_mock.assert_called_once_with(tag)
            git_url_mock.assert_called_once_with()
            git_push_mock.assert_called_once_with('https://git-username:git-password@' + url[8:])

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_pass_no_username_password(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url
            }

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_tag_side_effect():
                return tag
            get_tag_mock.side_effect = get_tag_side_effect

            def git_url_side_effect():
                return url
            git_url_mock.side_effect = git_url_side_effect


            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            get_tag_mock.assert_called_once_with()
            git_tag_mock.assert_called_once_with(tag)
            git_url_mock.assert_called_once_with()
            git_push_mock.assert_called_once_with(None)

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_fail_http_no_username_password(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'http://git.ploigos.xyz/ploigos-references/ploigos-reference-app-quarkus-rest-json.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url
            }

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_tag_side_effect():
                return tag
            get_tag_mock.side_effect = get_tag_side_effect

            def git_url_side_effect():
                return url
            git_url_mock.side_effect = git_url_side_effect


            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.success = False
            expected_step_result.message = 'For a http:// git url, you need to also provide username/password pair'

            # verifying all mocks were called
            get_tag_mock.assert_called_once_with()
            git_tag_mock.assert_called_once_with(tag)
            git_url_mock.assert_called_once_with()

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_fail_https_no_username_password(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'https://git.ploigos.xyz/ploigos-references/ploigos-reference-app-quarkus-rest-json.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url
            }

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_tag_side_effect():
                return tag
            get_tag_mock.side_effect = get_tag_side_effect

            def git_url_side_effect():
                return url
            git_url_mock.side_effect = git_url_side_effect

            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.success = False
            expected_step_result.message = 'For a https:// git url, you need to also provide username/password pair'

            # verifying all mocks were called
            get_tag_mock.assert_called_once_with()
            git_tag_mock.assert_called_once_with(tag)
            git_url_mock.assert_called_once_with()

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_error_git_tag(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_tag_side_effect():
                return tag
            get_tag_mock.side_effect = get_tag_side_effect

            def git_url_side_effect():
                return url
            git_url_mock.side_effect = git_url_side_effect

            # this is the test
            git_tag_mock.side_effect = StepRunnerException('mock error')
            result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)
            expected_step_result.success = False
            expected_step_result.message = "mock error"

            # verifying correct mocks were called
            git_tag_mock.assert_called_once_with(tag)

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_error_git_url(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_tag_side_effect():
                return tag
            get_tag_mock.side_effect = get_tag_side_effect

            # this is the test here
            git_url_mock.side_effect = StepRunnerException('mock error')
            result = step_implementer._run_step()

            # verify test results
            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)
            expected_step_result.success = False
            expected_step_result.message = "mock error"

            # verifying correct mocks were called
            git_tag_mock.assert_called_once_with(tag)
            git_url_mock.assert_called_once_with()

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_error_git_push(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def get_tag_side_effect():
                return tag
            get_tag_mock.side_effect = get_tag_side_effect

            def git_url_side_effect():
                return url
            git_url_mock.side_effect = git_url_side_effect

            # this is the test here
            git_push_mock.side_effect = StepRunnerException('mock error')
            result = step_implementer._run_step()

            # verify the test results
            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)
            expected_step_result.success = False
            expected_step_result.message = "mock error"

            # verifying all mocks were called
            get_tag_mock.assert_called_once_with()
            git_tag_mock.assert_called_once_with(tag)
            git_url_mock.assert_called_once_with()
            git_push_mock.assert_called_once_with(None)

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

# TEST FOR __get_tag

    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test__get_tag_no_version(self, git_push_mock, git_tag_mock, git_url_mock):
        with TempDirectory() as temp_dir:
            tag = 'latest'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url
            }

            artifact_config = {
                'container-image-version': {'description': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            def git_url_side_effect():
                return url
            git_url_mock.side_effect = git_url_side_effect


            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_tag_mock.assert_called_once_with(tag)
            git_url_mock.assert_called_once_with()
            git_push_mock.assert_called_once_with(None)

            self.assertEqual(result.get_step_result_dict(), expected_step_result.get_step_result_dict())

# TESTS FOR __git_url

    def create_git_config_side_effect(self, mock_remote_origin_url):
        def git_config_side_effect(*args, **kwargs):
            if (args[0] == '--get' and args[1] == 'remote.origin.url'):
                kwargs['_out'].write(mock_remote_origin_url)

        return git_config_side_effect

    @patch('sh.git', create=True)
    def test__git_url_url_from_git_config(self, git_mock):
        remote_origin_url = "https://does.not.matter.xyz/foo.git"

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            git_mock.config.side_effect = TestStepImplementerTagSourceGit.\
                create_git_config_side_effect(self, remote_origin_url)

            url = step_implementer._Git__git_url()

            self.assertEqual(url, remote_origin_url)

    @patch('sh.git', create=True)
    def test__git_url_url_from_git_config_error(self, git_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            git_mock.config.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock error')

            with self.assertRaisesRegex(
                StepRunnerException,
                "Error invoking git config --get remote.origin.url:"
            ):
                step_implementer._Git__git_url()

    @patch('sh.git', create=True)
    def test__git_url_from_step_config(self, git_mock):
        remote_origin_url = "https://does.not.matter.xyz/foo.git"

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': remote_origin_url
            }

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            git_mock.assert_not_called()

            url = step_implementer._Git__git_url()

            self.assertEqual(url, remote_origin_url)

# TESTS FOR __git_tag

    @patch('sh.git', create=True)
    def test__git_tag_success(self, git_mock):
        git_tag_value = "1.0+69442c8"

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._Git__git_tag(git_tag_value)

            git_mock.tag.assert_called_once_with(
                git_tag_value,
                '-f',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

    @patch('sh.git', create=True)
    def test__git_tag_error(self, git_mock):
        git_tag_value = "1.0+69442c8"

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            git_mock.tag.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock error')

            with self.assertRaisesRegex(
                StepRunnerException,
                "Error pushing git tag"
            ):
                step_implementer._Git__git_tag(git_tag_value)

# TESTS FOR __git_push

    @patch('sh.git', create=True)
    def test__git_push_with_url_success(self, git_mock):
        url = 'www.xyz.com'

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._Git__git_push(url)

            git_mock.push.assert_called_once_with(
                url,
                '--tag',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

    @patch('sh.git', create=True)
    def test__git_push_no_url_success(self, git_mock):

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            step_implementer._Git__git_push(None)

            git_mock.push.assert_called_once_with(
                '--tag',
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

    @patch('sh.git', create=True)
    def test__git_push_error(self, git_mock):
        url = 'www.xyz.com'

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'step-runner-results')
            results_file_name = 'step-runner-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            git_mock.push.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock error')

            with self.assertRaisesRegex(
                StepRunnerException,
                "Error invoking git push"
            ):
                step_implementer._Git__git_push(url)
