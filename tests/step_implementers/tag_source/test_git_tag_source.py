# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
from unittest.mock import patch, PropertyMock

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.tag_source import Git
from ploigos_step_runner.results import StepResult


class TestStepImplementerTagSourceGit(BaseStepImplementerTestCase):
    def create_step_implementer(
        self,
        workflow_result=None,
        step_config={},
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Git,
            step_config=step_config,
            step_name='tag-source',
            implementer='Git',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

# TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = Git.step_implementer_config_defaults()
        expected_defaults = {
            'version': 'latest',
            'git-repo-root': './',
            'git-commit-message': 'Automated commit of changes during release engineering' \
                                  ' generate-metadata step',
            'git-user-name': 'Ploigos Robot',
            'git-user-email': 'ploigos-robot'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Git._required_config_or_result_keys()
        expected_required_keys = [
            ['git-repo-root', 'repo-root'],
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
         with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

# TESTS FOR _run_step

    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_run_step_pass(self, git_repo_mock, git_url_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password',
                'version': tag
            }

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }

            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path,
            )

            git_url_mock.return_value = url

            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_url_mock.assert_called_once_with()
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_repo_mock.git.push.assert_called_once_with(url, '--tag')

            self.assertEqual(result, expected_step_result)

    '''
    TODO: Is this test case possible with the new logic? (i.e., can 'version' / 'tag' ever be empty?)
    '''
    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_run_step_pass_no_tag(self, git_repo_mock, git_url_mock):
        with TempDirectory() as temp_dir:
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password',
                'version': None
            }

            #artifact_config = {
            #    'version': {'description': '', 'value': tag},
            #    'container-image-version': {'description': '', 'value': tag}
            #}

            artifact_config = {}

            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path,
            )

            git_url_mock.return_value = url

            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value='latest')

            # verifying all mocks were called
            git_url_mock.assert_called_once_with()
            git_repo_mock.create_tag.assert_called_once_with('latest', force=True)
            git_repo_mock.git.push.assert_called_once_with(url, '--tag')

            self.assertEqual(result, expected_step_result)

    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_run_step_pass_http(self, git_repo_mock, git_url_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'http://git.ploigos.xyz/ploigos-references/ploigos-reference-app-quarkus-rest-json.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag
            git_url_mock.return_value = url

            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_url_mock.assert_called_once_with()
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_repo_mock.git.push.assert_called_once_with(url, '--tag')

            self.assertEqual(result, expected_step_result)

    '''
    TODO: URL splitting should be pulled into a utility class and tested separately
    '''
    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_repo')
    def test_run_step_pass_http_nonstandard_port(self, git_repo_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            git_username = 'git-username'
            git_password = 'git-password'
            url = 'http://git.ploigos.xyz:8080/ploigos-references/ploigos-reference-app-quarkus-rest-json.git'
            target_url = f'http://{git_username}:{git_password}@git.ploigos.xyz:8080/ploigos-references/' \
                         f'ploigos-reference-app-quarkus-rest-json.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_repo_mock.git.push.assert_called_once_with(target_url, '--tag')

            self.assertEqual(result, expected_step_result)

    '''
    TODO: URL splitting should be pulled into a utility class and tested separately
    '''
    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_repo')
    def test_run_step_pass_http_username_provided_twice(self, git_repo_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            git_username = 'git-username'
            git_password = 'git-password'
            url = 'http://fake-user:fake-password@git.ploigos.xyz/ploigos-references/' \
                  'ploigos-reference-app-quarkus-rest-json.git'
            target_url = f'http://{git_username}:{git_password}@git.ploigos.xyz/ploigos-references/' \
                         f'ploigos-reference-app-quarkus-rest-json.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_repo_mock.git.push.assert_called_once_with(target_url, '--tag')

            self.assertEqual(result, expected_step_result)

    '''
    TODO: URL splitting should be pulled into a utility class and tested separately
    '''
    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_repo')
    def test_run_step_pass_http_username_and_password_from_url(self, git_repo_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            git_username = 'git-username'
            git_password = 'git-password'
            url = f'http://{git_username}:{git_password}@git.ploigos.xyz/ploigos-references/' \
                  'ploigos-reference-app-quarkus-rest-json.git'
            target_url = f'http://{git_username}:{git_password}@git.ploigos.xyz/ploigos-references/' \
                         f'ploigos-reference-app-quarkus-rest-json.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_repo_mock.git.push.assert_called_once_with(target_url, '--tag')

            self.assertEqual(result, expected_step_result)

    '''
    TODO: URL splitting should be pulled into a utility class and tested separately
    '''
    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_repo')
    def test_run_step_pass_http_username_from_url_no_password(self, git_repo_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            git_username = 'git-username'
            url = f'http://{git_username}@git.ploigos.xyz/ploigos-references/' \
                  'ploigos-reference-app-quarkus-rest-json.git'
            target_url = f'http://{git_username}@git.ploigos.xyz/ploigos-references/' \
                         f'ploigos-reference-app-quarkus-rest-json.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_repo_mock.git.push.assert_called_once_with(target_url, '--tag')

            self.assertEqual(result, expected_step_result)

    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_run_step_pass_https(self, git_repo_mock, git_url_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'https://git.ploigos.xyz/ploigos-references/ploigos-reference-app-quarkus-rest-json.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag
            git_url_mock.return_value = url

            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_url_mock.assert_called_once_with()
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_repo_mock.git.push.assert_called_once_with(url, '--tag')

            get_tag_value_mock.assert_called_once_with()

            self.assertEqual(result, expected_step_result)

    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_run_step_pass_ssh(self, git_repo_mock, git_url_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'ssh://git.ploigos.xyz/ploigos-references/ploigos-reference-app-quarkus-rest-json.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag
            git_url_mock.return_value = url

            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_url_mock.assert_called_once_with()
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_repo_mock.git.push.assert_called_once_with(url, '--tag')

            get_tag_value_mock.assert_called_once_with()

            self.assertEqual(result, expected_step_result)

    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_run_step_pass_no_username_password(self, git_repo_mock, git_url_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag
            git_url_mock.return_value = url

            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_url_mock.assert_called_once_with()
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_repo_mock.git.push.assert_called_once_with(url, '--tag')

            self.assertEqual(result, expected_step_result)

    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_run_step_error_git_tag(self, git_repo_mock, git_url_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            error = 'I AM ERROR'

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag
            git_url_mock.return_value = url

            # this is the test
            git_repo_mock.create_tag.side_effect = Exception(error)
            result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)
            expected_step_result.success = False
            expected_step_result.message = f"Error tagging and pushing tags: Error creating git tag ({tag}): {error}"

            # verifying correct mocks were called
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)

            self.assertEqual(result, expected_step_result)

    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_run_step_error_git_url(self, git_repo_mock, git_url_mock, get_tag_value_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            error = 'uh oh spaghetti-os'

            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            get_tag_value_mock.return_value = tag

            # this is the test here
            git_url_mock.side_effect = StepRunnerException(error)
            result = step_implementer._run_step()

            # verify test results
            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)
            expected_step_result.success = False
            expected_step_result.message = f"Error tagging and pushing tags: {error}"

            # verifying correct mocks were called
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_url_mock.assert_called_once()

            self.assertEqual(result, expected_step_result)

    @patch.object(Git, '_Git__get_tag_value')
    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test_run_step_error_git_push(self, git_repo_mock, git_url_mock, get_tag_value_mock):
        # Test data setup
        tag = '1.0+69442c8'
        url = 'git@github.com:ploigos/ploigos-step-runner.git'
        error = 'oh no. ohhhhh no.'
        branch_name = 'feature/no-feature'

        # Mock setup
        get_tag_value_mock.return_value = tag
        git_url_mock.return_value = url
        git_repo_mock.active_branch.name = branch_name

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            artifact_config = {
                'version': {'description': '', 'value': tag},
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url,
                'git-username': 'git-username',
                'git-password': 'git-password'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            # this is the test here
            git_repo_mock.git.push.side_effect = Exception(error)
            result = step_implementer._run_step()

            # verify the test results
            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git'
            )
            expected_step_result.add_artifact(name='tag', value=tag)
            expected_step_result.success = False
            expected_step_result.message = f"Error tagging and pushing tags: Error pushing tags to remote ({url})" \
                f" on current branch ({branch_name}): {error}"

            # verifying all mocks were called
            git_repo_mock.create_tag.assert_called_once_with(tag, force=True)
            git_url_mock.assert_called_once_with()
            git_repo_mock.git.push.assert_called_once_with(url, '--tag')

            self.assertEqual(result, expected_step_result)

# TEST FOR __get_tag

    @patch.object(Git, 'git_url')
    @patch.object(Git, 'git_tag')
    @patch.object(Git, 'git_repo')
    def test__get_tag_no_version(self, git_repo_mock, git_tag_mock, git_url_mock):
        with TempDirectory() as temp_dir:
            tag = 'latest'
            url = 'git@github.com:ploigos/ploigos-step-runner.git'
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': tag}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='tag-source',
                sub_step_name='Git',
                sub_step_implementer_name='Git')
            expected_step_result.add_artifact(name='tag', value=tag)

            # verifying all mocks were called
            git_tag_mock.assert_called_once_with(tag)
            git_repo_mock.git.push.assert_called_once_with(git_url_mock, '--tag')

            self.assertEqual(result, expected_step_result)

    @patch.object(Git, 'git_repo')
    def test__git_url_from_step_config(self, git_repo_mock):
        remote_origin_url = "https://does.not.matter.xyz/foo.git"

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'url': remote_origin_url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            git_repo_mock.assert_not_called()

            url = step_implementer.git_url

            self.assertEqual(url, remote_origin_url)

# TESTS FOR __git_tag

    @patch.object(Git, 'git_repo')
    def test__git_tag_success(self, git_repo_mock):
        git_tag_value = "1.0+69442c8"

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            step_implementer.git_tag(git_tag_value)

            git_repo_mock.create_tag.assert_called_once_with(
                git_tag_value,
                force=True
            )

    @patch.object(Git, 'git_repo')
    def test__git_tag_error(self, git_repo_mock):
        git_tag_value = "1.0+69442c8"
        error = 'Uh oh!'

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            git_repo_mock.create_tag.side_effect = Exception(error)

            with self.assertRaisesMessage(
                StepRunnerException,
                f"Error creating git tag ({git_tag_value}): {error}"
            ):
                step_implementer.git_tag(git_tag_value)

# TESTS FOR __git_push

    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test__git_push_with_url_success(self, git_repo_mock, git_url_mock):
        url = 'www.xyz.com'

        git_url_mock.return_value = url

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            step_implementer.git_push()

            git_repo_mock.git.push.assert_called_once_with(url)

    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test__git_push_no_url_success(self, git_repo_mock, git_url_mock):
        git_url_mock.return_value = None

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            step_implementer.git_push()

            git_repo_mock.git.push.assert_called_once_with(None)

    @patch.object(Git, 'git_url', new_callable=PropertyMock)
    @patch.object(Git, 'git_repo')
    def test__git_push_error(self, git_repo_mock, git_url_mock):
        # Data setup
        url = 'www.xyz.com'
        branch_name = 'latest'
        error = 'Whoops!'

        # Mock setup
        git_url_mock.return_value = url

        git_repo_mock.active_branch.name = branch_name
        git_repo_mock.git.push.side_effect = Exception(error)

        # Run test
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            artifact_config = {
                'container-image-version': {'description': '', 'value': '1.0-69442c8'}
            }
            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step_config = {
                'git-url': url
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            with self.assertRaisesMessage(
                StepRunnerException,
                f"Error pushing changes to remote ({url})"
                f" on current branch ({branch_name}): {error}"
            ):
                step_implementer.git_push()
