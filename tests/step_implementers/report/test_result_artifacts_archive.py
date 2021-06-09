import os
import zipfile
from pathlib import Path
from unittest.mock import patch

import mock
from ploigos_step_runner import StepResult
from ploigos_step_runner.results.workflow_result import WorkflowResult
from ploigos_step_runner.step_implementers.report import ResultArtifactsArchive
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestStepImplementerResultArtifactsArchiveBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=ResultArtifactsArchive,
            step_config=step_config,
            step_name='report',
            implementer='ResultArtifactsArchive',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

class TestStepImplementerResultArtifactsArchive_other(TestStepImplementerResultArtifactsArchiveBase):
    def test_step_implementer_config_defaults(self):
        defaults = ResultArtifactsArchive.step_implementer_config_defaults()
        expected_defaults = {
            'results-archive-format': 'zip',
            'results-archive-ignored-artifacts': [
                'package-artifacts',
                'image-tar-file'
            ]
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = ResultArtifactsArchive._required_config_or_result_keys()
        expected_required_keys = [
            'organization',
            'application-name',
            'service-name',
            'version',
            'results-archive-format'
        ]
        self.assertEqual(required_keys, expected_required_keys)

class TestStepImplementerResultArtifactsArchive_run_step(TestStepImplementerResultArtifactsArchiveBase):
    @patch.object(
        ResultArtifactsArchive,
        '_ResultArtifactsArchive__create_archive',
        return_value=None
    )
    def test__run_step_pass_no_archive(self, create_archive_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_result = step_implementer._run_step()
            expected_step_result = StepResult(
                step_name='report',
                sub_step_name='ResultArtifactsArchive',
                sub_step_implementer_name='ResultArtifactsArchive'
            )
            expected_step_result.add_artifact(
                name='result-artifacts-archive',
                value='No result artifact values to archive.',
                description='Archive of all of the step result artifacts marked for archiving.'
            )
            self.assertEqual(step_result, expected_step_result)

            create_archive_mock.assert_called_once()

    @patch.object(
        ResultArtifactsArchive,
        '_ResultArtifactsArchive__create_archive',
        return_value='/fake/archive/path/foo.zip'
    )
    def test__run_step_pass(self, create_archive_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            step_result = step_implementer._run_step()
            expected_step_result = StepResult(
                step_name='report',
                sub_step_name='ResultArtifactsArchive',
                sub_step_implementer_name='ResultArtifactsArchive'
            )
            expected_step_result.add_artifact(
                name='result-artifacts-archive',
                value='/fake/archive/path/foo.zip',
                description='Archive of all of the step result artifacts marked for archiving.'
            )
            self.assertEqual(step_result, expected_step_result)

            create_archive_mock.assert_called_once()

    @patch('ploigos_step_runner.step_implementers.report.result_artifacts_archive.upload_file')
    @patch.object(
        ResultArtifactsArchive,
        '_ResultArtifactsArchive__create_archive',
        return_value='/fake/archive/path/foo.zip'
    )
    def test__run_step_pass_upload_to_file(self, create_archive_mock, upload_file_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test',
                'results-archive-destination-url': '/mock/results-archives'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # mock the upload results
            upload_file_mock.return_value = "mock upload results"

            # run the step
            step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='report',
                sub_step_name='ResultArtifactsArchive',
                sub_step_implementer_name='ResultArtifactsArchive'
            )
            expected_step_result.add_artifact(
                name='result-artifacts-archive',
                value='/fake/archive/path/foo.zip',
                description='Archive of all of the step result artifacts marked for archiving.'
            )
            expected_step_result.add_artifact(
                name='results-archive-uri',
                description='URI of the uploaded results archive.',
                value='/mock/results-archives/test-ORG/test-APP/test-SERVICE/foo.zip'
            )
            expected_step_result.add_artifact(
                name='results-archive-upload-results',
                description='Results of uploading the results archive to the given destination.',
                value='mock upload results'
            )
            self.assertEqual(step_result, expected_step_result)

            # verify mocks called
            create_archive_mock.assert_called_once()
            upload_file_mock.assert_called_once_with(
                file_path=mock.ANY,
                destination_uri='/mock/results-archives/test-ORG/test-APP/test-SERVICE/foo.zip',
                username=None,
                password=None
            )

    @patch('ploigos_step_runner.step_implementers.report.result_artifacts_archive.upload_file')
    @patch.object(
        ResultArtifactsArchive,
        '_ResultArtifactsArchive__create_archive',
        return_value='/fake/archive/path/foo.zip'
    )
    def test__run_step_pass_upload_to_remote_with_auth(self, create_archive_mock, upload_file_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test',
                'results-archive-destination-url': 'https://ploigos.com/mock/results-archives',
                'results-archive-destination-username': 'test-user',
                'results-archive-destination-password': 'test-pass'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # mock the upload results
            upload_file_mock.return_value = "mock upload results"

            # run the step
            step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='report',
                sub_step_name='ResultArtifactsArchive',
                sub_step_implementer_name='ResultArtifactsArchive'
            )
            expected_step_result.add_artifact(
                name='result-artifacts-archive',
                value='/fake/archive/path/foo.zip',
                description='Archive of all of the step result artifacts marked for archiving.'
            )
            expected_step_result.add_artifact(
                name='results-archive-uri',
                description='URI of the uploaded results archive.',
                value='https://ploigos.com/mock/results-archives/test-ORG/test-APP/test-SERVICE/foo.zip'
            )
            expected_step_result.add_artifact(
                name='results-archive-upload-results',
                description='Results of uploading the results archive to the given destination.',
                value='mock upload results'
            )
            self.assertEqual(step_result, expected_step_result)

            # verify mocks called
            create_archive_mock.assert_called_once()
            upload_file_mock.assert_called_once_with(
                file_path=mock.ANY,
                destination_uri='https://ploigos.com/mock/results-archives/test-ORG/test-APP/test-SERVICE/foo.zip',
                username='test-user',
                password='test-pass'
            )

    @patch('ploigos_step_runner.step_implementers.report.result_artifacts_archive.upload_file')
    @patch.object(
        ResultArtifactsArchive,
        '_ResultArtifactsArchive__create_archive',
        return_value='/fake/archive/path/foo.zip'
    )
    def test__run_step_pass_upload_to_remote_with_auth_failure(self, create_archive_mock, upload_file_mock):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test',
                'results-archive-destination-url': 'https://ploigos.com/mock/results-archives',
                'results-archive-destination-username': 'test-user',
                'results-archive-destination-password': 'test-pass'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # mock the upload results
            upload_file_mock.side_effect = RuntimeError('mock upload error')

            # run the step
            step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='report',
                sub_step_name='ResultArtifactsArchive',
                sub_step_implementer_name='ResultArtifactsArchive'
            )
            expected_step_result.add_artifact(
                name='result-artifacts-archive',
                value='/fake/archive/path/foo.zip',
                description='Archive of all of the step result artifacts marked for archiving.'
            )
            expected_step_result.add_artifact(
                name='results-archive-uri',
                description='URI of the uploaded results archive.',
                value='https://ploigos.com/mock/results-archives/test-ORG/test-APP/test-SERVICE/foo.zip'
            )
            expected_step_result.success = False
            expected_step_result.message = 'mock upload error'

            # verify mocks called
            create_archive_mock.assert_called_once()
            upload_file_mock.assert_called_once_with(
                file_path=mock.ANY,
                destination_uri='https://ploigos.com/mock/results-archives/test-ORG/test-APP/test-SERVICE/foo.zip',
                username='test-user',
                password='test-pass'
            )


class TestStepImplementerResultArtifactsArchive__create_archive(TestStepImplementerResultArtifactsArchiveBase):
    def test___create_archive_no_results(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            archive_path = step_implementer._ResultArtifactsArchive__create_archive()

            self.assertIsNone(archive_path)

    def test___create_archive_string_result(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }
            step_result = StepResult(
                step_name='test-step',
                sub_step_name='test-sub-step',
                sub_step_implementer_name='test-sub-step-implementer'
            )
            step_result.add_artifact(
                name='test-step-result-str',
                value='hello world'
            )
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            archive_path = step_implementer._ResultArtifactsArchive__create_archive()

            archive_zip = zipfile.ZipFile(archive_path)

            artifact_file_path = f"{step_config['organization']}-" \
                f"{step_config['application-name']}-{step_config['service-name']}-" \
                f"{step_config['version']}/test-step/test-sub-step/test-step-result-str"
            with archive_zip.open(artifact_file_path, 'r') as artifact_file:
                artifact_file_contents = artifact_file.read().decode('UTF-8')

                self.assertEqual(artifact_file_contents, 'hello world')

    def test___create_archive_file_result(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }

            artifact_file_name = 'test-artifact.txt'
            temp_dir.write(artifact_file_name, bytes('hello world file contents', 'utf-8'))

            step_result = StepResult(
                step_name='test-step',
                sub_step_name='test-sub-step',
                sub_step_implementer_name='test-sub-step-implementer'
            )
            step_result.add_artifact(
                name='test-step-result-str',
                value=os.path.join(temp_dir.path, artifact_file_name)
            )
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)


            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            archive_path = step_implementer._ResultArtifactsArchive__create_archive()

            archive_zip = zipfile.ZipFile(archive_path)

            artifact_file_path = f"{step_config['organization']}-" \
                f"{step_config['application-name']}-{step_config['service-name']}-" \
                f"{step_config['version']}/test-step/test-sub-step/test-step-result-str/" \
                f"{artifact_file_name}"
            with archive_zip.open(artifact_file_path, 'r') as artifact_file:
                artifact_file_contents = artifact_file.read().decode('UTF-8')

                self.assertEqual(artifact_file_contents, 'hello world file contents')

    def test___create_archive_dir_result(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }

            artifact_dir_name = 'test-result-artifact-dir'
            temp_dir.makedir(artifact_dir_name)

            artifact_file_name_1 = f'{artifact_dir_name}/test-artifact1.txt'
            temp_dir.write(artifact_file_name_1, bytes('hello world 1', 'utf-8'))
            artifact_file_name_2 = f'{artifact_dir_name}/test-artifact2.txt'
            temp_dir.write(artifact_file_name_2, bytes('hello world 2', 'utf-8'))

            step_result = StepResult(
                step_name='test-step',
                sub_step_name='test-sub-step',
                sub_step_implementer_name='test-sub-step-implementer'
            )
            step_result.add_artifact(
                name='test-step-result-dir',
                value=os.path.join(temp_dir.path, artifact_dir_name)
            )
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)


            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            archive_path = step_implementer._ResultArtifactsArchive__create_archive()

            archive_zip = zipfile.ZipFile(archive_path)

            artifact_file_path_1 = f"{step_config['organization']}-" \
                f"{step_config['application-name']}-{step_config['service-name']}-" \
                f"{step_config['version']}/test-step/test-sub-step/test-step-result-dir/" \
                f"{artifact_file_name_1}"
            with archive_zip.open(artifact_file_path_1, 'r') as artifact_file:
                artifact_file_contents = artifact_file.read().decode('UTF-8')

                self.assertEqual(artifact_file_contents, 'hello world 1')

            artifact_file_path_2 = f"{step_config['organization']}-" \
                f"{step_config['application-name']}-{step_config['service-name']}-" \
                f"{step_config['version']}/test-step/test-sub-step/test-step-result-dir/" \
                f"{artifact_file_name_1}"
            with archive_zip.open(artifact_file_path_2, 'r') as artifact_file:
                artifact_file_contents = artifact_file.read().decode('UTF-8')

                self.assertEqual(artifact_file_contents, 'hello world 1')

    def test___create_archive_list_result(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }
            step_result = StepResult(
                step_name='test-step',
                sub_step_name='test-sub-step',
                sub_step_implementer_name='test-sub-step-implementer'
            )
            step_result.add_artifact(
                name='test-step-result-str',
                value=[
                    'hello',
                    'world',
                    'foo'
                ]
            )
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            archive_path = step_implementer._ResultArtifactsArchive__create_archive()

            archive_zip = zipfile.ZipFile(archive_path)

            artifact_file_path = f"{step_config['organization']}-" \
                f"{step_config['application-name']}-{step_config['service-name']}-" \
                f"{step_config['version']}/test-step/test-sub-step/test-step-result-str"
            with archive_zip.open(artifact_file_path, 'r') as artifact_file:
                artifact_file_contents = artifact_file.read().decode('UTF-8')

                self.assertEqual(
                    artifact_file_contents,
                    """[
    "hello",
    "world",
    "foo"
]"""
                )

    def test___create_archive_dict_result(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }
            step_result = StepResult(
                step_name='test-step',
                sub_step_name='test-sub-step',
                sub_step_implementer_name='test-sub-step-implementer'
            )
            step_result.add_artifact(
                name='test-step-result-str',
                value={
                    'a': 'hello',
                    'b': 'world',
                    'c': 'foo'
                }
            )
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            archive_path = step_implementer._ResultArtifactsArchive__create_archive()

            archive_zip = zipfile.ZipFile(archive_path)

            artifact_file_path = f"{step_config['organization']}-" \
                f"{step_config['application-name']}-{step_config['service-name']}-" \
                f"{step_config['version']}/test-step/test-sub-step/test-step-result-str"
            with archive_zip.open(artifact_file_path, 'r') as artifact_file:
                artifact_file_contents = artifact_file.read().decode('UTF-8')

                self.assertEqual(
                    artifact_file_contents,
                    """{
    "a": "hello",
    "b": "world",
    "c": "foo"
}"""
                )

    def test___create_archive_bool_result(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }
            step_result = StepResult(
                step_name='test-step',
                sub_step_name='test-sub-step',
                sub_step_implementer_name='test-sub-step-implementer'
            )
            step_result.add_artifact(
                name='test-step-result-str',
                value=True
            )
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            archive_path = step_implementer._ResultArtifactsArchive__create_archive()

            archive_zip = zipfile.ZipFile(archive_path)

            artifact_file_path = f"{step_config['organization']}-" \
                f"{step_config['application-name']}-{step_config['service-name']}-" \
                f"{step_config['version']}/test-step/test-sub-step/test-step-result-str"
            with archive_zip.open(artifact_file_path, 'r') as artifact_file:
                artifact_file_contents = artifact_file.read().decode('UTF-8')

                self.assertEqual(
                    artifact_file_contents,
                    'True'
                )

    def test___create_archive_string_result_with_env(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }
            step_result = StepResult(
                step_name='test-step',
                sub_step_name='test-sub-step',
                sub_step_implementer_name='test-sub-step-implementer',
                environment='test-env1'
            )
            step_result.add_artifact(
                name='test-step-result-str',
                value='hello world'
            )
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            archive_path = step_implementer._ResultArtifactsArchive__create_archive()

            archive_zip = zipfile.ZipFile(archive_path)

            artifact_file_path = f"{step_config['organization']}-" \
                f"{step_config['application-name']}-{step_config['service-name']}-" \
                f"{step_config['version']}/test-step/test-sub-step/test-env1/test-step-result-str"
            with archive_zip.open(artifact_file_path, 'r') as artifact_file:
                artifact_file_contents = artifact_file.read().decode('UTF-8')

                self.assertEqual(artifact_file_contents, 'hello world')

    def test___create_archive_file_result_with_env(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'organization': 'test-ORG',
                'application-name': 'test-APP',
                'service-name': 'test-SERVICE',
                'version': '42.0-test'
            }

            artifact_file_name = 'test-artifact.txt'
            temp_dir.write(artifact_file_name, bytes('hello world file contents', 'utf-8'))

            step_result = StepResult(
                step_name='test-step',
                sub_step_name='test-sub-step',
                sub_step_implementer_name='test-sub-step-implementer',
                environment='test-env1'
            )
            step_result.add_artifact(
                name='test-step-result-str',
                value=os.path.join(temp_dir.path, artifact_file_name)
            )
            workflow_result = WorkflowResult()
            workflow_result.add_step_result(step_result)


            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
                workflow_result=workflow_result
            )

            archive_path = step_implementer._ResultArtifactsArchive__create_archive()

            archive_zip = zipfile.ZipFile(archive_path)

            artifact_file_path = f"{step_config['organization']}-" \
                f"{step_config['application-name']}-{step_config['service-name']}-" \
                f"{step_config['version']}/test-step/test-sub-step/test-env1/test-step-result-str/"\
                f"{artifact_file_name}"
            with archive_zip.open(artifact_file_path, 'r') as artifact_file:
                artifact_file_contents = artifact_file.read().decode('UTF-8')

                self.assertEqual(artifact_file_contents, 'hello world file contents')
