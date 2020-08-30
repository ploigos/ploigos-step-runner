"""Trusted Software Supply Chain Library (tssc) main entry point.

Command-Line Options
--------------------

    -h, --help
        show this help message and exit

    -s STEP, --step STEP
        TSSC workflow step to run

    -e ENVIRONMENT, --environment  ENVIRONMENT
        The environment to run this step against.

    -c CONFIG [CONFIG ...], --config CONFIG [CONFIG ...]
        TSSC workflow configuration files, or directories containing files, in yml or json

    -r RESULTS_DIR, --results-dir RESULTS_DIR
        TSSC workflow results file in yml or json

    --step-config STEP_CONFIG_KEY=STEP_CONFIG_VALUE [STEP_CONFIG_KEY=STEP_CONFIG_VALUE ...]
        Override step config provided by the given TSSC
        config-file with these arguments.

Step Configuration
------------------

### Steps

* generate-metadata
* tag-source
* static-code-analysis
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

### Variable Precedence

From least precedence to highest precedence.

    1. StepImplementer implementation provided configuration defaults
    2. Global Configuration Defaults (tssc-config.global-defaults)
    3. Global Environment Configuration Defaults (tssc-config.global-environment-defaults)
    4. Step Configuration (tssc-config.{STEP_NAME}.config)
    5. Step Environment Configuration
         (tssc-config.{STEP_NAME}.environment-config.{ENVIRONMENT_NAME})
    6. Step Configuration Runtime Overrides (--environment arugment to tssc main entry point)

** Example 1 **

    ---
    tssc-config:
      # Dictionary of configuration options which will be used in step configuration if that
      # step does not have a specific value for that configuration already or one is not
      # given by global-environment-defaults.
      global-defaults:
        # A sample config option with a default global value.
        # Overrides
        #   * StepImplementers default config values
        # Is Overriden by:
        #   * global-environment-defaults
        #   * step config
        #   * step environment config
        #   * step config runtime overrides
        sample-config-option-1: 'global default'

      # Dictionary of dictionaries where the first level keys are environment names and their
      # dictionary values are configuration defaults to use when invoking a step in the context
      # of that environment.
      #
      # NOTE: Environment names can be anything so long as they line up with the environment value
      # given to the `--environment` flag of the main tssc entry point.
      #global-environment-defaults:
        # Sample configuration for an environment named 'SAMPLE-ENV-1'.
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main tssc entry point.
        #SAMPLE-ENV-1:
          # Sample config option that may differ from environment to environment.
          #sample-config-option-2: 'default for use in the SAMPLE-ENV-1 env"

        # Sample configuration for an environment named 'SAMPLE-ENV-2'.
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main tssc entry point.
        #SAMPLE-ENV-2:
          # Sample config option that may differ from environment to environment.
          #sample-config-option-2: 'default for use in the SAMPLE-ENV-2 env"

      # Sample step config for step named SAMPLE-STEP-1
      SAMPLE-STEP-1:
      - implementer: SampleStep1Implementer1
        config:
          sample-config-option-3: 'value for sample-config-option-3 for use in this step'
        environment-config:
          SAMPLE-ENV-1:
            sample-config-option-4: 'value for use in this step in SAMPLE-ENV-1 environment'
          SAMPLE-ENV-2:
            sample-config-option-4: 'value for use in this step in SAMPLE-ENV-1 environment'

### Example Configuration Files

.. Note::
    Optional step configurations are listed commented out and with their default values.

** Example TSSC Config file for a Maven built Application **

    ---
    tssc-config:
      # Optional
      # Dictionary of configuration options which will be used in step configuration if that
      # step does not have a specific value for that configuration already or one is not
      # given by global-environment-defaults.
      global-defaults:
        # Required.
        # Name of the application the artifact built and deployed by this TSSC workflow is part of.
        application-name: ''

        # Required.
        # Name of the service this artifact built and deployed by this TSSC workflow implements as
        # part of the application it is a part of.
        service-name: ''

      # Optional
      # Dictionary of dictionaries where the first level keys are environment names and their
      # dictionary values are configuration defaults to use when invoking a step in the context
      # of that environment.
      #
      # NOTE: Environment names can be anything so long as they line up with the environment value
      # given to the `--environment` flag of the main tssc entry point.
      global-environment-defaults:
        # Sample
        # Sample configuration for an environment named 'DEV'.
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main tssc entry point.
        DEV:
          # Required
          kube-app-domain: ''

          #Optional
          #kube-api-token: ''

          #Optional
          #insecure-skip-tls-verify: 'true'

          # Required
          argocd-username: ''

          # Required
          argocd-password: ''

          # Required
          argocd-api: ''

          # Optional
          #argocd-sync-timeout-seconds: '60'

          # Optional
          #argocd-helm-chart-path: './'

        # Sample
        # Sample configuration for an environment named 'TEST'
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main tssc entry point.
        TEST:
          # Required
          kube-app-domain: ''

          #Optional
          #kube-api-token: ''

          #Optional
          #insecure-skip-tls-verify: 'true'

          # Required
          argocd-username: ''

          # Required
          argocd-password: ''

          # Required
          argocd-api: ''

          # Optional
          #argocd-sync-timeout-seconds: '60'

          # Optional
          #argocd-helm-chart-path: './'

        # Sample
        # Sample configuration for an environment named 'PROD'
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main tssc entry point.
        #PROD:
        # Sample
        # Sample parameter that may differ from environment to environment.
        #kube-api-uri: 'api.prod.myorg.xyz"

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

      static-code-analysis:
      - implementer: SonarQube
        config: {
          # Required.
          # URL to the sonarqube server
          url: 'http//sonarqube-sonarqube.company.com/'

          # Required.
          # Properties file in root folder (eg: sonar-project.properties)
          properties: 'sonar-project.properties'

          # Optional.
          #user: None

          # Optional.
          #password: None
        }

      unit-test:
      - implementer: Maven
        config: {
          # Optional.
          # fail-on-no-tests: true

          # Optional.
          # pom_file: 'pom.xml'
        }

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

      push-artifacts:
      - implementer: Maven
        config: {
          # Required.
          # URL to the artifact repository to push the artifact to.
          #url: ''

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

      deploy:
      - implementer: ArgoCD
        config:
          # argocd specific variables are set per environment above

          # Required
          helm-config-repo: ''

          # Optional
          #values-yaml-directory: './cicd/Deployment/'

          # Optional
          #value-yaml-template: 'values.yaml.j2'

          # Required
          git-email: ''

          # Optional
          #git-friendly-name: 'TSSC'

          # Optional
          #git-username: None

          # Optional
          #git-password: None

          # Any template parameters required by values.yaml.j2 can be listed below. Note dashes will
          # be converted to underscores to be compliant with the jinja template variable
          # specification
          readiness-probe-path: ''


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
      # Optional
      # Dictionary of configuration options which will be used in step configuration if that
      # step does not have a specific value for that configuration already or one is not
      # given by global-environment-defaults.
      global-defaults:
        # Required.
        # Name of the application the artifact built and deployed by this TSSC workflow is part of.
        application-name: ''

        # Required.
        # Name of the service this artifact built and deployed by this TSSC workflow implements as
        # part of the application it is a part of.
        service-name: ''

      # Optional
      # Dictionary of dictionaries where the first level keys are environment names and their
      # dictionary values are configuration defaults to use when invoking a step in the context
      # of that environment.
      #
      # NOTE: Environment names can be anything so long as they line up with the environment value
      # given to the `--environment` flag of the main tssc entry point.
      global-environment-defaults:
        # Optional Sample
        # Sample configuration for an environment named 'DEV'.
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main tssc entry point.
        DEV:
          # Required
          kube-app-domain: ''

          #Optional
          #kube-api-token: ''

          #Optional
          #insecure-skip-tls-verify: 'true'

          # Required
          argocd-username: ''

          # Required
          argocd-password: ''

          # Required
          argocd-api: ''

          # Optional
          #argocd-sync-timeout-seconds: '60'

          # Optional
          #argocd-helm-chart-path: './'

        # Sample
        # Sample configuration for an environment named 'TEST'
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main tssc entry point.
        TEST:
          # Required
          kube-app-domain: ''

          #Optional
          #kube-api-token:

          #Optional
          #insecure-skip-tls-verify: 'true'

          # Required
          argocd-username: ''

          # Required
          argocd-password: ''

          # Required
          argocd-api: ''

          # Optional
          #argocd-sync-timeout-seconds: '60'

          # Optional
          #argocd-helm-chart-path: './'

        # Sample
        # Sample configuration for an environment named 'PROD'
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main tssc entry point.
        #PROD:
        # Sample
        # Sample parameter that may differ from environment to environment.
        #kube-api-uri: 'api.prod.myorg.xyz"

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

      static-code-analysis:
      - implementer: SonarQube
        config: {
          # Required.
          # URL to the sonarqube server
          url: 'http//sonarqube-sonarqube.company.com/'

          # Required.
          # Properties file in root folder (eg: sonar-project.properties)
          properties: 'sonar-project.properties'

          # Optional.
          #user: None

          # Optional.
          #password: None
        }

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

      deploy:
      - implementer: ArgoCD
        config:
          # argocd specific variables are set per environment above

          # Required
          helm-config-repo: ''

          # Optional
          #values-yaml-directory: './cicd/Deployment/'

          # Optional
          #value-yaml-template: 'values.yaml.j2'

          # Optional
          #argocd-helm-chart-path: './'

          # Required
          git-email: ''

          # Optional
          #git-friendly-name: 'TSSC'

          # Optional
          #git-username: None

          # Optional
          #git-password: None

          # Any template parameters required by values.yaml.j2 can be listed below.
          # Note dashes will be converted to underscores to be compliant with the jinja
          # template variable specification
          readiness-probe-path: ''

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
...     --config=my-app-tssc-config.yml
...     --results-file=my-app-tssc-results.yml
...     --step=generate-metadata

"""

import __main__
from .config import TSSCConfig, TSSCStepConfig, TSSCSubStepConfig
from .factory import TSSCFactory
from .exceptions import TSSCException
from .step_implementer import DefaultSteps, StepImplementer
