import unittest
from unittest.mock import ANY, PropertyMock, patch

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.step_implementers.push_container_image.pelorus_commit_timestamp_metric import \
    PelorusCommitTimestampMetric
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class TestPelorusCommitTimestampMetricBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=PelorusCommitTimestampMetric,
            step_config=step_config,
            step_name='push-container-image',
            implementer='PelorusCommitTimestampMetric',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

class TestPelorusCommitTimestampMetric_step_implementer_config_defaults(
    unittest.TestCase
):
    def test_result(self):
        defaults = PelorusCommitTimestampMetric.step_implementer_config_defaults()
        expected_defaults = {
            'pelorus-prometheus-job': 'ploigos'
        }
        self.assertEqual(defaults, expected_defaults)

class TestPelorusCommitTimestampMetric_required_config_or_result_keys(
    unittest.TestCase
):
    def test_result(self):
        required_keys = PelorusCommitTimestampMetric._required_config_or_result_keys()
        expected_required_keys = [
            'commit-hash',
            'commit-utc-timestamp',
            ['container-image-push-digest', 'container-image-digest'],
            'pelorus-prometheus-pushgateway-url',
            'pelorus-prometheus-job',
            'pelorus-app-name'
        ]
        self.assertEqual(required_keys, expected_required_keys)

@patch.object(StepImplementer, '_validate_required_config_or_previous_step_result_artifact_keys')
@patch.object(PelorusCommitTimestampMetric, 'pelorus_app_name', new_callable=PropertyMock)
class TestPelorusCommitTimestampMetric_validate_required_config_or_previous_step_result_artifact_keys(
    TestPelorusCommitTimestampMetricBase
):
    def test_valid(
        self,
        mock_pelorus_app_name,
        mock_super_validate_required_config_or_previous_step_result_artifact_keys
    ):
        # setup mocks
        mock_pelorus_app_name.return_value = 'mock-valid-pelorus-app-name'

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

        # verify
        mock_super_validate_required_config_or_previous_step_result_artifact_keys.assert_called_once()
        mock_pelorus_app_name.assert_called_once()

    def test_invalid_pelorus_app_name(
        self,
        mock_pelorus_app_name,
        mock_super_validate_required_config_or_previous_step_result_artifact_keys
    ):
        # setup mocks
        mock_pelorus_app_name.return_value = 'mock-invalid-pelorus-app-name-that-is-to-long-for-kube-to-handle-kuz-kube-has-silly-limits'

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        with self.assertRaisesRegex(
            AssertionError,
            "Given Pelorus Application Name \(mock-invalid-pelorus-app-name-that-is-to-long-for-kube-to-handle-kuz-kube-has-silly-limits\) is invalid because it is" \
            " longer than 63 characters which because it is expected to be a" \
            " kubernetes label value breaks the kubernetes label value length rules." \
            " https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set"
        ):
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

        # verify
        mock_super_validate_required_config_or_previous_step_result_artifact_keys.assert_called_once()
        mock_pelorus_app_name.assert_called()


@patch.object(PelorusCommitTimestampMetric, 'get_value')
class TestPelorusCommitTimestampMetric_properties(TestPelorusCommitTimestampMetricBase):
    def test_commit_hash(self, mock_get_value):
        # setup mocks
        mock_get_value.return_value = 'mock-hash'

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        actual_result = step_implementer.commit_hash

        # verify
        self.assertEqual(actual_result, 'mock-hash')
        mock_get_value.assert_called_once_with('commit-hash')

    def test_commit_utc_timestamp(self, mock_get_value):
        # setup mocks
        mock_get_value.return_value = 'mock-utc-timestamp'

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        actual_result = step_implementer.commit_utc_timestamp

        # verify
        self.assertEqual(actual_result, 'mock-utc-timestamp')
        mock_get_value.assert_called_once_with('commit-utc-timestamp')

    def test_container_image_digest(self, mock_get_value):
        # setup mocks
        mock_get_value.return_value = 'mock-image-digest'

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        actual_result = step_implementer.container_image_digest

        # verify
        self.assertEqual(actual_result, 'mock-image-digest')
        mock_get_value.assert_called_once_with(
            ['container-image-push-digest', 'container-image-digest']
        )

    def test_pelorus_prometheus_pushgateway_url(self, mock_get_value):
        # setup mocks
        mock_get_value.return_value = 'mock-url'

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        actual_result = step_implementer.pelorus_prometheus_pushgateway_url

        # verify
        self.assertEqual(actual_result, 'mock-url')
        mock_get_value.assert_called_once_with('pelorus-prometheus-pushgateway-url')

    def test_pelorus_prometheus_job(self, mock_get_value):
        # setup mocks
        mock_get_value.return_value = 'mock-job'

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        actual_result = step_implementer.pelorus_prometheus_job

        # verify
        self.assertEqual(actual_result, 'mock-job')
        mock_get_value.assert_called_once_with('pelorus-prometheus-job')

    def test_pelorus_app_name(self, mock_get_value):
        # setup mocks
        mock_get_value.return_value = 'mock-app-name'

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        actual_result = step_implementer.pelorus_app_name

        # verify
        self.assertEqual(actual_result, 'mock-app-name')
        mock_get_value.assert_called_once_with('pelorus-app-name')

@patch('ploigos_step_runner.step_implementers.push_container_image.pelorus_commit_timestamp_metric.push_to_gateway')
@patch.object(PelorusCommitTimestampMetric, 'pelorus_app_name', new_callable=PropertyMock)
@patch.object(PelorusCommitTimestampMetric, 'commit_hash', new_callable=PropertyMock)
@patch.object(PelorusCommitTimestampMetric, 'container_image_digest', new_callable=PropertyMock)
@patch.object(PelorusCommitTimestampMetric, 'commit_utc_timestamp', new_callable=PropertyMock)
@patch.object(PelorusCommitTimestampMetric, 'pelorus_prometheus_pushgateway_url', new_callable=PropertyMock)
@patch.object(PelorusCommitTimestampMetric, 'pelorus_prometheus_job', new_callable=PropertyMock)
class TestPelorusCommitTimestampMetric_run_step(
    TestPelorusCommitTimestampMetricBase
):
    def test_success(
        self,
        mock_pelorus_prometheus_job,
        mock_pelorus_prometheus_pushgateway_url,
        mock_commit_utc_timestamp,
        mock_container_image_digest,
        mock_commit_hash,
        mock_pelorus_app_name,
        mock_push_to_gateway
    ):
        # setup mocks
        mock_pelorus_prometheus_job.return_value = 'mock-job'
        mock_pelorus_prometheus_pushgateway_url.return_value = 'mock-push-url'
        mock_commit_utc_timestamp.return_value = '1642079293.0'
        mock_container_image_digest.return_value = 'mock-digest'
        mock_commit_hash.return_value = 'mock-commit-hash'
        mock_pelorus_app_name.return_value = 'mock-app-name'

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        actual_result = step_implementer._run_step()

        # verify
        expected_step_result = StepResult(
            step_name='push-container-image',
            sub_step_name='PelorusCommitTimestampMetric',
            sub_step_implementer_name='PelorusCommitTimestampMetric'
        )
        self.assertEqual(actual_result, expected_step_result)
        mock_push_to_gateway.assert_called_once_with(
            gateway='mock-push-url',
            job='mock-job',
            grouping_key={
                'job': 'mock-job',
                'app': 'mock-app-name',
                'commit': 'mock-commit-hash'
            },
            registry=ANY
        )

    def test_push_error(
        self,
        mock_pelorus_prometheus_job,
        mock_pelorus_prometheus_pushgateway_url,
        mock_commit_utc_timestamp,
        mock_container_image_digest,
        mock_commit_hash,
        mock_pelorus_app_name,
        mock_push_to_gateway
    ):
        # setup mocks
        mock_pelorus_prometheus_job.return_value = 'mock-job'
        mock_pelorus_prometheus_pushgateway_url.return_value = 'mock-push-url'
        mock_commit_utc_timestamp.return_value = '1642079293.0'
        mock_container_image_digest.return_value = 'mock-digest'
        mock_commit_hash.return_value = 'mock-commit-hash'
        mock_pelorus_app_name.return_value = 'mock-app-name'
        mock_push_to_gateway.side_effect = Exception('mock push error')

        # setup
        step_implementer = self.create_step_implementer()

        # run step
        actual_result = step_implementer._run_step()

        # verify
        expected_step_result = StepResult(
            step_name='push-container-image',
            sub_step_name='PelorusCommitTimestampMetric',
            sub_step_implementer_name='PelorusCommitTimestampMetric'
        )
        expected_step_result.success = False
        expected_step_result.message = "Error pushing Pelorus Commit Timestamp metric to" \
            " Prometheus Pushgateway (mock-push-url): mock push error"
        self.assertEqual(actual_result, expected_step_result)
        mock_push_to_gateway.assert_called_once_with(
            gateway='mock-push-url',
            job='mock-job',
            grouping_key={
                'job': 'mock-job',
                'app': 'mock-app-name',
                'commit': 'mock-commit-hash'
            },
            registry=ANY
        )
