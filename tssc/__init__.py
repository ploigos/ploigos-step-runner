"""Trusted Software Supply Chain Library (tssc) main entry point.

Command-Line Options
--------------------

    -h, --help                                 show this help message and exit

    -s STEP, --step STEP                       TSSC workflow step to run

    -c CONFIG_FILE, --config-file CONFIG_FILE  TSSC workflow configuration file in yml or json

    -r RESULTS_DIR, --results-dir RESULTS_DIR  TSSC workflow results file in yml or json

    --step-config STEP_CONFIG_KEY=STEP_CONFIG_VALUE [STEP_CONFIG_KEY=STEP_CONFIG_VALUE ...]

                                               Override step config provided by the given TSSC
                                               config-file with these arguments.

Step Config
-----------

### Steps

* generate-metadata
* tag-source
* security-static-code-analysis
* linting-static-code-analysis
* package
* unit-test
* push-artifacts
* create-container-image
* push-container-image
* container-image-unit-test
* container-image-static-compliance-scan
* container-image-static-vulnerability-scan
* create-deployment-environment
* deploy
* uat
* runtime-vulnerability-scan
* canary-test
* publish-workflow-results

### Example Configuration Files

.. Note::
    Optional step configurations are listed commented out and with their default values.

** Example TSSC Config file for a Maven built Application **

    ---
    tssc-config:
      global-defaults:
        # Required.
        # Name of the application the artifact built and deployed by this TSSC workflow is part of.
        application-name: ''

        # Required.
        # Name of the service this artifact built and deployed by this TSSC workflow implements as
        # part of the application it is a part of.
        service-name: ''

      generate-metadata:
      - implementer: Maven
        config: {
          # Optional.
          #pom-file: 'pom.xml'
        }

      - implementer: Git
        config: {
          # Optional.
          #repo-root: './'

          # Optional.
          #build-string-length: 7
        }

      - implementer: SemanticVersion

      tag-source:
      - implementer: Git
        config: {
          # Optional.
          # Will use current directory to determine URL if not specified.
          #url: None

          # Optional.
          #username: None

          # Optional.
          #password: None
        }

      security-static-code-analysis:
      # WARNING: not yet implemented
      - implementer: SonarQube
        config: {}

      linting-static-code-analysis:
        # WARNING: not yet implemented
      - implementer: SonarQube
        config: {}

      package:
      - implementer: Maven
        config: {
          # Optional.
          #pom-file: 'pom.xml'

          # Optional
          #artifact-extensions: ['jar', 'war', 'ear']

          # Optional
          #artifact-parent-dir: 'target'
        }

      unit-test:
      # WARNING: not yet implemented
      - implementer: Maven
        config: {}

      push-artifacts:
      - implementer: Maven
        config: {
          # Required.
          # URL to the artifact repository to push the artifact to.
          url: ''

          # Optional.
          #user: None

          # Optional.
          #password: None
        }

      create-container-image:
      - implementer: Buildah
        config: {
          # Optional.
          #imagespecfile: 'Dockerfile'

          # Optional.
          #context: '.'

          # Optional.
          #tlsverify: true

          # Optional.
          #format: 'oci'
        }

      push-container-image:
      - implementer: Skopeo
        config: {
          destination: '' # Required. Container image repository destination to push image to
          #src-tls-verify: true # Optional
          #dest-tls-verify: true # Optional
        }

      # WARNING: not yet implemented
      container-image-unit-test: []

      container-image-static-compliance-scan:
      # WARNING: not yet implemented
      - implementer: OpenSCAP
        config: {}

      container-image-static-vulnerability-scan:
      # WARNING: not yet implemented
      - implementer: OpenSCAP
        config: {}

      # WARNING: not yet implemented
      create-deployment-environment: []

      # WARNING: not yet implemented
      deploy: []

      uat:
      # WARNING: not yet implemented
      - implementer: Cucumber
        config: {}

      # WARNING: not yet implemented
      runtime-vulnerability-scan: []

      canary-test:
        # WARNING: not yet implemented
      - implementer: Selenium
        config: {}

      # WARNING: not yet implemented
      publish-workflow-results: []

** Example TSSC Config file for a NPM built Application **

    ---
    tssc-config:
      global-defaults:
        # Required.
        # Name of the application the artifact built and deployed by this TSSC workflow is part of.
        application-name: ''

        # Required.
        # Name of the service this artifact built and deployed by this TSSC workflow implements as
        # part of the application it is a part of.
        service-name: ''

      generate-metadata:
      # WARNING: not yet implemented
      - implementer: NPM
        config: {}

      - implementer: Git
        config: {
          # Optional.
          #repo-root: './'

          # Optional.
          #build-string-length: 7
        }

      - implementer: SemanticVersion

      tag-source:
      - implementer: Git
        config: {
          # Optional.
          # Will use current directory to determine URL if not specified.
          #url: None

          # Optional.
          #username: None

          # Optional.
          #password: None
        }

      security-static-code-analysis:
      # WARNING: not yet implemented
      - implementer: SonarQube
        config: {}

      linting-static-code-analysis:
        # WARNING: not yet implemented
      - implementer: SonarQube
        config: {}

      package:
      # WARNING: not yet implemented
      - implementer: NPM
        config: {}

      unit-test:
      # WARNING: not yet implemented
      - implementer: NPM
        config: {}

      push-artifacts:
      # WARNING: not yet implemented
      - implementer: NPM
        config: {
          # Required.
          # URL to the artifact repository to push the artifact to.
          url: ''

          # Optional.
          #user: None

          # Optional.
          #password: None
        }

      create-container-image:
      - implementer: Buildah
        config: {
          # Optional.
          #imagespecfile: 'Dockerfile'

          # Optional.
          #context: '.'

          # Optional.
          #tlsverify: true

          # Optional.
          #format: 'oci'
        }

      push-container-image:
      - implementer: Skopeo
        config: {
          destination: '' # Required. Container image repository destination to push image to
          #src-tls-verify: true # Optional
          #dest-tls-verify: true # Optional
        }

      # WARNING: not yet implemented
      container-image-unit-test: []

      container-image-static-compliance-scan:
      # WARNING: not yet implemented
      - implementer: OpenSCAP
        config: {}

      container-image-static-vulnerability-scan:
      # WARNING: not yet implemented
      - implementer: OpenSCAP
        config: {}

      # WARNING: not yet implemented
      create-deployment-environment: []

      # WARNING: not yet implemented
      deploy: []

      uat:
      # WARNING: not yet implemented
      - implementer: Cucumber
        config: {}

      # WARNING: not yet implemented
      runtime-vulnerability-scan: []

      canary-test:
        # WARNING: not yet implemented
      - implementer: Selenium
        config: {}

      # WARNING: not yet implemented
      publish-workflow-results: []

Examples
--------

Getting Help

>>> python -m tssc --help


Example Running the 'generate-metadata' step

>>> python -m tssc
...     --config-file=my-app-tssc-config.yml
...     --results-file=my-app-tssc-results.yml
...     --step=generate-metadata

"""

import __main__
from .factory import TSSCFactory
from .exceptions import TSSCException
from .step_implementer import DefaultSteps, StepImplementer
