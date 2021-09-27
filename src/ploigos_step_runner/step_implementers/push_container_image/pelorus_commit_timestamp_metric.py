"""`StepImplementer` to extend the `push-container-image` step to push the
Pelorus Commit Timestamp metric to a Prometheus Pushgateway inlieuof the default
Pelorus Commit Timestamp exporter which depends on OpenShift BuildConfigs.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key                    | Required? | Default | Description
-------------------------------------|-----------|---------|-----------
`commit-hash`                        | Yes       |         | Current commit hash.
`commit-utc-timestamp`               | Yes       |         | Current commit UTC POSIX timestamp.
`container-image-push-digest`        | Yes       |         | Container image digest of pushed container image. \
                                                             IMPORTANT: this must be the image digest as calculated for the image \
                                                             as reported by the image registry it is pushed to as it must match \
                                                             the image digest used for deployment.
`container-image-digest`             | Yes       |         | Alias for `container-image-push-digest`.
`pelorus-prometheus-pushgateway-url` | Yes       |         | URL to Prometheus Pushgateway that Pelorus is configured to read from.
`pelorus-prometheus-job`             | Yes       | ploigos | Prometheus Job that the pushed metric should be reported from.
`pelorus-app-name`                   | Yes       |         | The name by which Pelorus knows this system component by. \
                                                             This must align with the app name that the Deploy Time exporter knows \
                                                             this system component by. By default the Pelorus Deploy Time exporter \
                                                             uses the value of the `app.kubernetes.io/name` label on the deployed Pod \
                                                             but this is configurable in Pelorus, see the Pelorus documentation \
                                                             https://github.com/konveyor/pelorus/tree/master/exporters/deploytime#supported-integrations.

Result Artifacts
----------------
Results artifacts output by this step.

None.

"""# pylint: disable=line-too-long

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer

DEFAULT_CONFIG = {
    'pelorus-prometheus-job': 'ploigos'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'commit-hash',
    'commit-utc-timestamp',
    ['container-image-push-digest', 'container-image-digest'],
    'pelorus-prometheus-pushgateway-url',
    'pelorus-prometheus-job',
    'pelorus-app-name'
]

class PelorusCommitTimestampMetric(StepImplementer):
    """`StepImplementer` to extend the `push-container-image` step to push the
    Pelorus Commit Timestamp metric to a Prometheus Pushgateway inlieuof the default
    Pelorus Commit Timestamp exporter which depends on OpenShift BuildConfigs.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

        Notes
        -----
        These are the lowest precedence configuration values.

        Returns
        -------
        dict
            Default values to use for step configuration values.
        """
        return DEFAULT_CONFIG

    @staticmethod
    def _required_config_or_result_keys():
        """Getter for step configuration or previous step result artifacts that are required before
        running this step.

        See Also
        --------
        _validate_required_config_or_previous_step_result_artifact_keys

        Returns
        -------
        array_list
            Array of configuration keys or previous step result artifacts
            that are required before running the step.
        """
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * given 'pelorus-app-name' is equal to or less then 63 characters

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        assert len(self.pelorus_app_name) <= 63, \
            f"Given Pelorus Application Name ({self.pelorus_app_name}) is invalid because it is" \
            " longer than 63 characters which because it is expected to be a" \
            " kubernetes label value breaks the kubernetes label value length rules." \
            " https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set"

    @property
    def commit_hash(self):
        """
        Returns
        -------
        str
            Current commit hash.
        """
        return self.get_value('commit-hash')

    @property
    def commit_utc_timestamp(self):
        """
        Returns
        -------
        str
            Current commit UTC POSIX timestamp.
        """
        return self.get_value('commit-utc-timestamp')

    @property
    def container_image_digest(self):
        """
        Returns
        -------
        str
            Container image digest of pushed container image.
        """
        return self.get_value(['container-image-push-digest', 'container-image-digest'])

    @property
    def pelorus_prometheus_pushgateway_url(self):
        """
        Returns
        -------
        str
            URL to Prometheus Pushgateway that Pelorus is configured to read from.
        """
        return self.get_value('pelorus-prometheus-pushgateway-url')

    @property
    def pelorus_prometheus_job(self):
        """
        Returns
        -------
        str
            Prometheus Job that the pushed metric should be reported from.
        """
        return self.get_value('pelorus-prometheus-job')

    @property
    def pelorus_app_name(self):
        """
        Returns
        -------
        str
            The name by which Pelorus knows this system component by.
        """
        return self.get_value('pelorus-app-name')

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # create the gauge
        registry = CollectorRegistry()
        gauge = Gauge(
            name='commit_timestamp',
            documentation='Pelorus Software Delivery Performance (SDP) Commit timestamp.' \
                'https://github.com/konveyor/pelorus/blob/master/exporters/committime/README.md#commit-time-exporter',
            registry=registry,
            labelnames=['app', 'commit', 'image_sha']
        )

        # set the value and its labels
        gauge.labels(
            app=self.pelorus_app_name,
            commit=self.commit_hash,
            image_sha=self.container_image_digest
        ).set(self.commit_utc_timestamp)

        # push to prometheus pushgateway
        try:
            push_to_gateway(
                gateway=self.pelorus_prometheus_pushgateway_url,
                job=self.pelorus_prometheus_job,
                grouping_key={
                    'job': self.pelorus_prometheus_job,
                    'app': self.pelorus_app_name,
                    'commit': self.commit_hash
                },
                registry=registry
            )
        except Exception as error: # pylint: disable=broad-except
            step_result.success = False
            step_result.message = "Error pushing Pelorus Commit Timestamp metric to" \
                f" Prometheus Pushgateway ({self.pelorus_prometheus_pushgateway_url}): {error}"

        return step_result
