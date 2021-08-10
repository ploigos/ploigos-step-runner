"""`StepImplementer` for the `deploy` step using `helm secrets upgrade --install` so that it works for both an initial \
upgrade of a preinstalled helm chart.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default | Description
-----------------------------|-----------|---------|-----------
`helm-chart`                 | Yes       |         | The chart argument can be either: a chart \
                                                     reference('example/mariadb'), a path to a chart directory, a \
                                                     packaged chart, or a fully qualified URL.
`helm-release`               | Yes       |         | Release tag.
`helm-flags`                 | No        | `[]`    | Use flags to customize the installation behavior.       
""" # pylint: disable=line-too-long

import os


DEFAULT_CONFIG = {
    'helm-flags' : ''
}


REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'helm-chart',
    'helm-release'
]