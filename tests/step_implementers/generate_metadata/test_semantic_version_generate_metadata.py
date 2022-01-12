import os

from mock import patch
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementers.generate_metadata import \
    SemanticVersion
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestStepImplementerSemanticVersionGenerateMetadataBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=SemanticVersion,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

class TestStepImplementerSemanticVersionGenerateMetadata_misc(
    TestStepImplementerSemanticVersionGenerateMetadataBase
):

    def test_step_implementer_config_defaults(self):
        defaults = SemanticVersion.step_implementer_config_defaults()
        expected_defaults = {
            'is-pre-release': False,
            'sha-build-identifier-length': 7,
            'container-image-tag-build-deliminator': '_'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = SemanticVersion._required_config_or_result_keys()
        expected_required_keys = [
            'app-version',
            'is-pre-release',
            'container-image-tag-build-deliminator'
        ]
        self.assertEqual(required_keys, expected_required_keys)

@patch.object(SemanticVersion, '_SemanticVersion__get_semantic_version_pre_release')
@patch.object(SemanticVersion, '_SemanticVersion__get_semantic_version_build')
class TestStepImplementerSemanticVersionGenerateMetadata__run_step(
    TestStepImplementerSemanticVersionGenerateMetadataBase
):
    def test_only_app_version(self, mock_build, mock_pre_release):
        # setup
        step_config = {
            'app-version': '0.42.1'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='SemanticVersion'
        )

        # setup mocks
        mock_build.return_value = None
        mock_pre_release.return_value = None

        # run test
        actual_result= step_implementer._run_step()

        # verify results
        expected_step_result = StepResult(
            step_name='generate-metadata',
            sub_step_name='SemanticVersion',
            sub_step_implementer_name='SemanticVersion'
        )
        expected_step_result.add_artifact(
            name='version',
            value='0.42.1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_artifact(
            name='container-image-tag',
            value='0.42.1',
            description='Constructed semenatic version without build identifier' \
              ' since not compatible with container image tags'
        )
        expected_step_result.add_artifact(
            name='semantic-version-core',
            value='0.42.1',
            description='Semantic version version core portion'
        )
        expected_step_result.add_evidence(
            name='version',
            value='0.42.1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_evidence(
            name='container-image-tag',
            value='0.42.1',
            description='semenatic version without build identifier' \
                ' since not compatible with container image tags'
        )

        self.assertEqual(actual_result, expected_step_result)
        mock_pre_release.assert_not_called()
        mock_build.assert_called_once()

    def test_app_version_and_build(self, mock_build, mock_pre_release):
        # setup
        step_config = {
            'app-version': '0.42.1'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='SemanticVersion'
        )

        # setup mocks
        mock_build.return_value = 'mock1'
        mock_pre_release.return_value = None

        # run test
        actual_result= step_implementer._run_step()

        # verify results
        expected_step_result = StepResult(
            step_name='generate-metadata',
            sub_step_name='SemanticVersion',
            sub_step_implementer_name='SemanticVersion'
        )
        expected_step_result.add_artifact(
            name='version',
            value='0.42.1+mock1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_artifact(
            name='container-image-tag',
            value='0.42.1_mock1',
            description='Constructed semenatic version without build identifier' \
              ' since not compatible with container image tags'
        )
        expected_step_result.add_artifact(
            name='semantic-version-core',
            value='0.42.1',
            description='Semantic version version core portion'
        )
        expected_step_result.add_artifact(
            name='semantic-version-build',
            value='mock1',
            description='Semantic version build portion'
        )
        expected_step_result.add_evidence(
            name='version',
            value='0.42.1+mock1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_evidence(
            name='container-image-tag',
            value='0.42.1_mock1',
            description='semenatic version without build identifier' \
                ' since not compatible with container image tags'
        )

        self.assertEqual(actual_result, expected_step_result)
        mock_pre_release.assert_not_called()
        mock_build.assert_called_once()

    def test_app_version_and_build_custom_container_image_tag_build_deliminator(self, mock_build, mock_pre_release):
        # setup
        step_config = {
            'app-version': '0.42.1',
            'container-image-tag-build-deliminator': '_-_'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='SemanticVersion'
        )

        # setup mocks
        mock_build.return_value = 'mock1'
        mock_pre_release.return_value = None

        # run test
        actual_result= step_implementer._run_step()

        # verify results
        expected_step_result = StepResult(
            step_name='generate-metadata',
            sub_step_name='SemanticVersion',
            sub_step_implementer_name='SemanticVersion'
        )
        expected_step_result.add_artifact(
            name='version',
            value='0.42.1+mock1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_artifact(
            name='container-image-tag',
            value='0.42.1_-_mock1',
            description='Constructed semenatic version without build identifier' \
              ' since not compatible with container image tags'
        )
        expected_step_result.add_artifact(
            name='semantic-version-core',
            value='0.42.1',
            description='Semantic version version core portion'
        )
        expected_step_result.add_artifact(
            name='semantic-version-build',
            value='mock1',
            description='Semantic version build portion'
        )
        expected_step_result.add_evidence(
            name='version',
            value='0.42.1+mock1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_evidence(
            name='container-image-tag',
            value='0.42.1_-_mock1',
            description='semenatic version without build identifier' \
                ' since not compatible with container image tags'
        )

        self.assertEqual(actual_result, expected_step_result)
        mock_pre_release.assert_not_called()
        mock_build.assert_called_once()

    def test_app_version_and_is_pre_release_with_given_pre_release_identifiers(self, mock_build, mock_pre_release):
        # setup
        step_config = {
            'app-version': '0.42.1',
            'is-pre-release': True
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='SemanticVersion'
        )

        # setup mocks
        mock_build.return_value = None
        mock_pre_release.return_value = 'feature-mock1'

        # run test
        actual_result= step_implementer._run_step()

        # verify results
        expected_step_result = StepResult(
            step_name='generate-metadata',
            sub_step_name='SemanticVersion',
            sub_step_implementer_name='SemanticVersion'
        )
        expected_step_result.add_artifact(
            name='version',
            value='0.42.1-feature-mock1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_artifact(
            name='container-image-tag',
            value='0.42.1-feature-mock1',
            description='Constructed semenatic version without build identifier' \
              ' since not compatible with container image tags'
        )
        expected_step_result.add_artifact(
            name='semantic-version-core',
            value='0.42.1',
            description='Semantic version version core portion'
        )
        expected_step_result.add_artifact(
            name='semantic-version-pre-release',
            value='feature-mock1',
            description='Semantic version pre-release portion'
        )
        expected_step_result.add_evidence(
            name='version',
            value='0.42.1-feature-mock1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_evidence(
            name='container-image-tag',
            value='0.42.1-feature-mock1',
            description='semenatic version without build identifier' \
                ' since not compatible with container image tags'
        )

        self.assertEqual(actual_result, expected_step_result)
        mock_pre_release.assert_called_once()
        mock_build.assert_called_once()

    # NOTE: maybe at some point we should set some default pre-release value if
    #       none calculated so that semver reflects that it is a pre-release?
    def test_app_version_and_is_pre_release_without_given_pre_release_identifiers(self, mock_build, mock_pre_release):
        # setup
        step_config = {
            'app-version': '0.42.1',
            'is-pre-release': True
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='SemanticVersion'
        )

        # setup mocks
        mock_build.return_value = None
        mock_pre_release.return_value = None

        # run test
        actual_result= step_implementer._run_step()

        # verify results
        expected_step_result = StepResult(
            step_name='generate-metadata',
            sub_step_name='SemanticVersion',
            sub_step_implementer_name='SemanticVersion'
        )
        expected_step_result.add_artifact(
            name='version',
            value='0.42.1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_artifact(
            name='container-image-tag',
            value='0.42.1',
            description='Constructed semenatic version without build identifier' \
              ' since not compatible with container image tags'
        )
        expected_step_result.add_artifact(
            name='semantic-version-core',
            value='0.42.1',
            description='Semantic version version core portion'
        )
        expected_step_result.add_evidence(
            name='version',
            value='0.42.1',
            description='Full constructured semantic version'
        )
        expected_step_result.add_evidence(
            name='container-image-tag',
            value='0.42.1',
            description='semenatic version without build identifier' \
                ' since not compatible with container image tags'
        )

        self.assertEqual(actual_result, expected_step_result)
        mock_pre_release.assert_called_once()
        mock_build.assert_called_once()

    def test_app_version_and_is_pre_release_with_given_pre_release_identifiers_and_build(self, mock_build, mock_pre_release):
        # setup
        step_config = {
            'app-version': '0.42.1',
            'is-pre-release': True
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='SemanticVersion'
        )

        # setup mocks
        mock_build.return_value = 'mock3'
        mock_pre_release.return_value = 'feature-mock1'

        # run test
        actual_result= step_implementer._run_step()

        # verify results
        expected_step_result = StepResult(
            step_name='generate-metadata',
            sub_step_name='SemanticVersion',
            sub_step_implementer_name='SemanticVersion'
        )
        expected_step_result.add_artifact(
            name='version',
            value='0.42.1-feature-mock1+mock3',
            description='Full constructured semantic version'
        )
        expected_step_result.add_artifact(
            name='container-image-tag',
            value='0.42.1-feature-mock1_mock3',
            description='Constructed semenatic version without build identifier' \
              ' since not compatible with container image tags'
        )
        expected_step_result.add_artifact(
            name='semantic-version-core',
            value='0.42.1',
            description='Semantic version version core portion'
        )
        expected_step_result.add_artifact(
            name='semantic-version-pre-release',
            value='feature-mock1',
            description='Semantic version pre-release portion'
        )
        expected_step_result.add_artifact(
            name='semantic-version-build',
            value='mock3',
            description='Semantic version build portion'
        )
        expected_step_result.add_evidence(
            name='version',
            value='0.42.1-feature-mock1+mock3',
            description='Full constructured semantic version'
        )
        expected_step_result.add_evidence(
            name='container-image-tag',
            value='0.42.1-feature-mock1_mock3',
            description='semenatic version without build identifier' \
                ' since not compatible with container image tags'
        )

        self.assertEqual(actual_result, expected_step_result)
        mock_pre_release.assert_called_once()
        mock_build.assert_called_once()

class TestStepImplementerSemanticVersionGenerateMetadata___get_semantic_version_pre_release(
    TestStepImplementerSemanticVersionGenerateMetadataBase
):
    def test_empty(self):
        # setup
        step_config = {
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_pre_release = step_implementer._SemanticVersion__get_semantic_version_pre_release()

        # verify results
        self.assertEqual(actual_pre_release, None)

    def test_only_branch(self):
        # setup
        step_config = {
            'branch': 'feature/mock1'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_pre_release = step_implementer._SemanticVersion__get_semantic_version_pre_release()

        # verify results
        self.assertEqual(actual_pre_release, 'feature-mock1')

    def test_only_workflow_run_num(self):
        # setup
        step_config = {
            'workflow-run-num': '42'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_pre_release = step_implementer._SemanticVersion__get_semantic_version_pre_release()

        # verify results
        self.assertEqual(actual_pre_release, '42')

    def test_only_additional_pre_release_identifiers_list(self):
        # setup
        step_config = {
            'additional-pre-release-identifiers': [
                'mock1',
                'mock2'
            ]
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_pre_release = step_implementer._SemanticVersion__get_semantic_version_pre_release()

        # verify results
        self.assertEqual(actual_pre_release, 'mock1.mock2')

    def test_only_additional_pre_release_identifiers_string(self):
        # setup
        step_config = {
            'additional-pre-release-identifiers': 'mock1'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_pre_release = step_implementer._SemanticVersion__get_semantic_version_pre_release()

        # verify results
        self.assertEqual(actual_pre_release, 'mock1')

    def test_branch_workflow_run_num_additional_pre_release_identifiers(self):
        # setup
        step_config = {
            'branch': 'feature/mock1',
            'workflow-run-num': '42',
            'additional-pre-release-identifiers': [
                'mock1',
                'mock2'
            ]
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_pre_release = step_implementer._SemanticVersion__get_semantic_version_pre_release()

        # verify results
        self.assertEqual(actual_pre_release, 'feature-mock1.42.mock1.mock2')

class TestStepImplementerSemanticVersionGenerateMetadata___get_semantic_version_build(
    TestStepImplementerSemanticVersionGenerateMetadataBase
):
    def test_empty(self):
        # setup
        step_config = {
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_build = step_implementer._SemanticVersion__get_semantic_version_build()

        # verify results
        self.assertEqual(actual_build, None)

    def test_only_sha_default_length(self):
        # setup
        step_config = {
            'sha': 'a1b2c3d4e5f6g7h8i9'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_build = step_implementer._SemanticVersion__get_semantic_version_build()

        # verify results
        self.assertEqual(actual_build, 'a1b2c3d')

    def test_only_sha_custom_length(self):
        # setup
        step_config = {
            'sha': 'a1b2c3d4e5f6g7h8i9',
            'sha-build-identifier-length': 10
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_build = step_implementer._SemanticVersion__get_semantic_version_build()

        # verify results
        self.assertEqual(actual_build, 'a1b2c3d4e5')

    def test_only_sha_no_length(self):
        # setup
        step_config = {
            'sha': 'a1b2c3d4e5f6g7h8i9',
            'sha-build-identifier-length': None
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_build = step_implementer._SemanticVersion__get_semantic_version_build()

        # verify results
        self.assertEqual(actual_build, 'a1b2c3d4e5f6g7h8i9')

    def test_only_workflow_run_num(self):
        # setup
        step_config = {
            'workflow-run-num': 42
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_build = step_implementer._SemanticVersion__get_semantic_version_build()

        # verify results
        self.assertEqual(actual_build, '42')

    def test_only_additional_build_identifiers_list(self):
        # setup
        step_config = {
            'additional-build-identifiers': [
                'mock3',
                'mock4'
            ]
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_build = step_implementer._SemanticVersion__get_semantic_version_build()

        # verify results
        self.assertEqual(actual_build, 'mock3.mock4')

    def test_only_additional_build_identifiers_string(self):
        # setup
        step_config = {
            'additional-build-identifiers': 'mock3'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_build = step_implementer._SemanticVersion__get_semantic_version_build()

        # verify results
        self.assertEqual(actual_build, 'mock3')

    def test_sha_workflow_run_num_additional_build_identifiers_list(self):
        # setup
        step_config = {
            'sha': 'a1b2c3d4e5f6g7h8i9',
            'workflow-run-num': 42,
            'additional-build-identifiers': [
                'mock3',
                'mock4'
            ]
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            step_name='generate-metadata',
            implementer='Git'
        )

        # run test
        actual_build = step_implementer._SemanticVersion__get_semantic_version_build()

        # verify results
        self.assertEqual(actual_build, 'a1b2c3d.42.mock3.mock4')
