# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
from io import IOBase
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tssc.step_implementers.tag_source import Git
from tssc.step_result import StepResult

from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from tests.helpers.test_utils import Any


class TestStepImplementerGitTagSourceBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Git,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

# TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = Git.step_implementer_config_defaults()
        expected_defaults = {}
        self.assertEqual(defaults, expected_defaults)

    def test_required_runtime_step_config_keys(self):
        required_keys = Git.required_runtime_step_config_keys()
        expected_required_keys = []
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_runtime_step_config_valid(self):
        step_config = {
            'username': 'username',
            'password': 'password'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='tag-source',
            implementer='Git'
        )

        step_implementer._validate_runtime_step_config(step_config)

    def test__validate_runtime_step_config_invalid(self):
        step_config = {
            'username': 'username'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='tag-source',
            implementer='Git'
        )
        with self.assertRaisesRegex(
                AssertionError,
                re.compile(
                    'Either username or password is not set. Neither or both must be set.'
                )
        ):
            step_implementer._validate_runtime_step_config(step_config)

# TESTS FOR _run_step

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_pass(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:rhtconsulting/tssc-python-package.git'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'username': 'username',
                'password': 'password'
            }

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': tag},
                'container-image-version': {'description': '', 'type': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_pass_http(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'http://gitea.apps.tssc.rht-set.com/tssc-references/tssc-reference-app-quarkus-rest-json.git'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'username': 'username',
                'password': 'password'
            }

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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
            git_push_mock.assert_called_once_with('http://username:password@' + url[7:])

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_pass_https(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'https://gitea.apps.tssc.rht-set.com/tssc-references/tssc-reference-app-quarkus-rest-json.git'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'username': 'username',
                'password': 'password'
            }

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': tag},
                'container-image-version': {'description': '', 'type': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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
            git_push_mock.assert_called_once_with('https://username:password@' + url[8:])

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_pass_no_username_password(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:rhtconsulting/tssc-python-package.git'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url
            }

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': tag},
                'container-image-version': {'description': '', 'type': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    def test_run_step_fail_empty_username_password(self):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'git@github.com:rhtconsulting/tssc-python-package.git'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url,
                'username': '',
                'password': ''
            }

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': tag},
                'container-image-version': {'description': '', 'type': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='tag-source', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.success = False
            expected_step_result.message = 'Both username and password must have non-empty value in the runtime step configuration'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_fail_http_no_username_password(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'http://gitea.apps.tssc.rht-set.com/tssc-references/tssc-reference-app-quarkus-rest-json.git'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url
            }

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': tag},
                'container-image-version': {'description': '', 'type': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch.object(Git, '_Git__get_tag')
    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test_run_step_fail_https_no_username_password(self, git_push_mock, git_tag_mock, git_url_mock, get_tag_mock):
        with TempDirectory() as temp_dir:
            tag = '1.0+69442c8'
            url = 'https://gitea.apps.tssc.rht-set.com/tssc-references/tssc-reference-app-quarkus-rest-json.git'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url
            }

            artifact_config = {
                'version': {'description': '', 'type': '', 'value': tag},
                'container-image-version': {'description': '', 'type': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

# TEST FOR __get_tag

    @patch.object(Git, '_Git__git_url')
    @patch.object(Git, '_Git__git_tag')
    @patch.object(Git, '_Git__git_push')
    def test__get_tag_no_version(self, git_push_mock, git_tag_mock, git_url_mock):
        with TempDirectory() as temp_dir:
            tag = 'latest'
            url = 'git@github.com:rhtconsulting/tssc-python-package.git'
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': url
            }

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': tag}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

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
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            git_mock.config.side_effect = TestStepImplementerGitTagSourceBase.\
                create_git_config_side_effect(self, remote_origin_url)

            url = step_implementer._Git__git_url()

            self.assertEqual(url, remote_origin_url)

    @patch('sh.git', create=True)
    def test__git_url_url_from_git_config_error(self, git_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            git_mock.config.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock error')

            with self.assertRaisesRegex(
                RuntimeError,
                "Error invoking git config --get remote.origin.url:"
            ):
                step_implementer._Git__git_url()

    @patch('sh.git', create=True)
    def test__git_url_from_step_config(self, git_mock):
        remote_origin_url = "https://does.not.matter.xyz/foo.git"

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': remote_origin_url
            }

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            git_mock.tag.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock error')

            with self.assertRaisesRegex(
                RuntimeError,
                "Error pushing git tag"
            ):
                step_implementer._Git__git_tag(git_tag_value)

# TESTS FOR __git_push

    @patch('sh.git', create=True)
    def test__git_push_with_url_success(self, git_mock):
        url = 'www.xyz.com'

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
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
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {}

            artifact_config = {
                'container-image-version': {'description': '', 'type': '', 'value': '1.0-69442c8'}
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='tag-source',
                implementer='Git',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            git_mock.push.side_effect = sh.ErrorReturnCode('git', b'mock out', b'mock error')

            with self.assertRaisesRegex(
                RuntimeError,
                "Error invoking git push"
            ):
                step_implementer._Git__git_push(url)
