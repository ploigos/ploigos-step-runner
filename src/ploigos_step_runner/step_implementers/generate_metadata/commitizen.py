"""`StepImplementer` for the `generate-metadata` step using Commitizen.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key  | Required? | Default    | Description
-------------------|-----------|------------|-----------
`repo-root`        | Yes       | `./`       | Directory path to the Git repo to anaylze tags.
`cz-json`          | Yes       | `.cz.json` | json file with the commitizen configurataion.

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`app-version`       | Value to use for `version` portion of semantic version \
                      (https://semver.org/). Uses the version from `cz bump` in dry-run mode.
"""

import json
import io
import os
import re
import sys

import sh

from git import Repo
from ploigos_step_runner import StepImplementer, StepResult

DEFAULT_CONFIG = {
    'cz-json': '.cz.json',
    'repo-root': './',
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'cz-json',
    'repo-root'
]

class Commitizen(StepImplementer):
    """
    StepImplementer for the generate-metadata step for Commitizen.
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

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * given 'cz-json' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        cz_json_path = self.get_value('cz-json')
        assert os.path.exists(cz_json_path), \
            f'cz-json does not exist: {cz_json_path}'

        with open(cz_json_path, 'rb') as cz_json:
            assert json.loads(cz_json.read()), "cz-json is not valid JSON"

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """

        step_result = StepResult.from_step_implementer(self)
        cz_json_path = self.get_value('cz-json')

        repo_root = self.get_value('repo-root')
        repo = Repo(repo_root)
        os.chdir(repo_root)

        with open(cz_json_path, 'rb+') as cz_json:
            cz_json_contents = json.loads(cz_json.read())
            cz_json_contents['commitizen']['version'] = self._get_version_tag(repo.tags)
            cz_json.seek(0)
            cz_json.truncate(0)
            cz_json.write(json.dumps(cz_json_contents).encode())

        out = io.StringIO()
        sh.cz.bump( # pylint: disable=no-member
            '--dry-run',
            '--yes',
            _out=out,
            _err=sys.stderr,
            _tee='err'
        )
        bump_regex = r'tag to create: (\d+.\d+.\d+)'
        version = re.findall(bump_regex, out.getvalue(),)[0]
        step_result.add_artifact(name='app-version', value=version)

        return step_result

    @staticmethod
    def _get_version_tag(tags):
        """Gets the latest tag version and updates the json config.

        Returns
        -------
        tag_version
            String representing the latest repo tag version.
        """

        tag_version = '0.0.0'

        # check for existing repo tags. if no existing repo tag is found then default to version
        # 0.0.0. if existing repo tags are found then use the latest version tag.
        for tag in tags:
            semantic_version = re.match(r'.*(\d+).(\d+).(\d+).*', tag.name)
            for i, part in enumerate(semantic_version.groups()):
                tag_version_part = tag_version.split('.')[i]
                if part > tag_version_part:
                    tag_version = ".".join(semantic_version.groups())
                elif part < tag_version_part:
                    break

        return tag_version
