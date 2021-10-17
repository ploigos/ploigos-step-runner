"""`StepImplementer` for the `generate-metadata` to generate a semantic version from given input.

Supports the following semantic versions (https://semver.org/) :

  - major.minor.patch+build
  - major.minor.patch-pre_rleease+build

Notes
-----
When tagging container images we will regex + to - due
to https://github.com/docker/distribution/issues/1201.

Source for version sections:

  - major.minor.patch
    * will come from previous sub step of generate_metadata step,
      with step results including 'app_version'
    * known implementers:
      -  maven
  - pre-release
    * will come from previous sub step of generate_metadata step,
      with step results including 'pre_release'
    * known implementers:
      - git
  - build
    * will come from previous sub step of generate_metadata step,
      with step results including 'build'
    * known implementers:
      - git

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key                     | Required? | Default | Description
--------------------------------------|-----------|---------|-----------
`app-version`                         | Yes       |         | Value to use for `version` portion of semantic version (https://semver.org/). \
                                                              EX: `<app-version>`
`is-pre-release`                      | Yes       | `False` | If `True` then will add any relevant `pre-release` identifiers to semantic version (https://semver.org/), \
                                                              such as the branch name. \
                                                              If `False` then assumed to be a release build and all `pre-release` identifiers will \
                                                              be ignored from version as per the semantic version spec (https://semver.org/).
`branch`                              | No        |         | If `is-pre-release` is `True`, value to use for a pre-release name in pre-release poriton of semantic version (https://semver.org/). \
                                                              EX: `<app-version>-<branch>`
`workflow-run-num`                    | No        |         | If `is-pre-release` is `True`, value to use for a numeric identifier of the branch `pre-release` identifier if provided. \
                                                              Also always used in build identifier. \
                                                              Since this can be included in the pre-release section, it should be incremental as per the sem version spec.
                                                              EX (pre-release): `<app-version>-<branch>.<workflow-run-num>+<sha>.<workflow-run-num>` <br/>\
                                                              EX (release): `<app-version>+<sha>.<workflow-run-num>`
`sha`                                 | No        |         | Value to use for sha build identifier in build portion of semantic version. \
                                                              EX: `<app-version>+<sha>`
`sha-build-identifier-length`         | No        | 7       | Trim the given `sha` down to this length when including as build identifier in semantic version
`additional-pre-release-identifiers`  | No        |         | If `is-pre-release` is `True`, additional `pre-release` identifiers to add to semantic version (https://semver.org/). \
                                                              Ignored if `is-pre-release` is `False. \
                                                              EX (pre-release): `<app-version>-<branch>.<workflow-run-num>-<additional-pre-release-identifiers>+<sha>.<workflow-run-num>`
`additional-build-identifiers`        | No        |         | Additional `build` identifiers to add to semantic version (https://semver.org/). \
                                                              EX (pre-release): `<app-version>-<branch>.<workflow-run-num>+<sha>.<workflow-run-num>.<additional-build-identifiers>` <br/>\
                                                              EX (release): `<app-version>+<sha>.<workflow-run-num>.<additional-build-identifiers>`

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key            | Description
-------------------------------|------------
`version`                      | Full constructured semantic version
`container-image-tag`          | Constructed semenatic version without build identifier since not compatible with container image tags
`semantic-version-core`        | Semantic version version core portion
`semantic-version-pre-release` | Semantic version version pre-release portion
`semantic-version-build`       | Semantic version version build portion

"""# pylint: disable=line-too-long

import re

from ploigos_step_runner import StepImplementer, StepResult

DEFAULT_CONFIG = {
  'is-pre-release': False,
  'sha-build-identifier-length': 7
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'app-version',
    'is-pre-release'
]

class SemanticVersion(StepImplementer):  # pylint: disable=too-few-public-methods
    """`StepImplementer` for the `generate-metadata` to generate a
    semantic version from given input.
    """

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

        Returns
        -------
        dict
            Default values to use for step configuration values.

        Notes
        -----
        These are the lowest precedence configuration values.

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

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # construct version and image tag
        version_core = self.get_value('app-version')
        version = f'{version_core}'
        image_tag = f'{version_core}'
        pre_release = None
        if self.get_value('is-pre-release'):
            pre_release = self.__get_semantic_version_pre_release()
            if pre_release:
                version += f'-{pre_release}'
                image_tag += f'-{pre_release}'
            else:
                # NOTE: maybe at some point we should set some default pre-release value if
                #       none calculated so that semver reflects that it is a pre-release?
                pass
        build = self.__get_semantic_version_build()
        if build:
            version += f'+{build}'

        # add artifacts
        step_result.add_artifact(
            name='version',
            value=version,
            description='Full constructured semantic version'
        )
        step_result.add_artifact(
            name='container-image-tag',
            value=image_tag,
            description='Constructed semenatic version without build identifier' \
              ' since not compatible with container image tags'
        )
        step_result.add_artifact(
            name='semantic-version-core',
            value=version_core,
            description='Semantic version version core portion'
        )
        if pre_release:
            step_result.add_artifact(
                name='semantic-version-pre-release',
                value=pre_release,
                description='Semantic version pre-release portion'
            )
        if build:
            step_result.add_artifact(
                name='semantic-version-build',
                value=build,
                description='Semantic version build portion'
            )

        # add evidence
        step_result.add_evidence(
            name='version',
            value=version,
            description='Full constructured semantic version'
        )
        step_result.add_evidence(
            name='container-image-tag',
            value=image_tag,
            description='semenatic version without build identifier' \
                ' since not compatible with container image tags'
        )

        return step_result

    def __get_semantic_version_pre_release(self):
        """Get the pre-release portion of the semantic version

        Returns
        -------
        Pre-release portion of the semantic version.
        """
        pre_release = None
        pre_release_identifiers = []

        # if branch given add as a pre-release identifier
        branch = self.get_value('branch')
        if branch:
            pre_release_regex = re.compile(r"/", re.IGNORECASE)
            branch_pre_release_identifier = re.sub(pre_release_regex, '-', branch)
            pre_release_identifiers.append(branch_pre_release_identifier)

        # if workflow run num given ass as  apre-release identifier
        workflow_run_num = self.get_value('workflow-run-num')
        if workflow_run_num:
            pre_release_identifiers.append(workflow_run_num)

        # if additional pre-release identifiers given, add as pre-release identifiers
        additional_pre_release_identifiers = self.get_value('additional-pre-release-identifiers')
        if additional_pre_release_identifiers:
            if isinstance(additional_pre_release_identifiers, list):
                pre_release_identifiers += additional_pre_release_identifiers
            else:
                pre_release_identifiers.append(additional_pre_release_identifiers)

        if pre_release_identifiers:
            pre_release = '.'.join(pre_release_identifiers)

        return pre_release

    def __get_semantic_version_build(self):
        """Get the build portion of the semantic version

        Returns
        -------
        Build portion of the semantic version.
        """
        build = None
        build_identifiers = []

        # if sha given add as a build identifier
        sha = self.get_value('sha')
        if sha:
            sha_build_identifier = None
            sha_build_identifier_length = self.get_value('sha-build-identifier-length')
            if sha_build_identifier_length:
                sha_build_identifier = str(sha)[:sha_build_identifier_length]
            else:
                sha_build_identifier = sha
            build_identifiers.append(sha_build_identifier)

        # if workflow run num given as a build identifier
        workflow_run_num = self.get_value('workflow-run-num')
        if workflow_run_num:
            build_identifiers.append(str(workflow_run_num))

        # if additional pre-release identifiers given, add as pre-release identifiers
        additional_build_identifiers = self.get_value('additional-build-identifiers')
        if additional_build_identifiers:
            if isinstance(additional_build_identifiers, list):
                build_identifiers += additional_build_identifiers
            else:
                build_identifiers.append(additional_build_identifiers)

        if build_identifiers:
            build = '.'.join(build_identifiers)

        return build
