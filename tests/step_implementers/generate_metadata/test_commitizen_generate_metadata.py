# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import collections
import functools
import json
import os
import re

from unittest.mock import Mock, patch

from git import Repo
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from ploigos_step_runner import StepResult
from ploigos_step_runner.step_implementers.generate_metadata import Commitizen


class TestStepImplementerCommitizenGenerateMetadata(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Commitizen,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = Commitizen.step_implementer_config_defaults()
        expected_defaults = {
            'cz-json': '.cz.json',
            'repo-root': './'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Commitizen._required_config_or_result_keys()
        expected_required_keys = ['cz-json', 'repo-root']
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('.cz.json', b'''{
                "commitizen": {
                    "bump_message": "build: bump $current_version \\u2192 $new_version [skip-ci]", 
                    "name": "cz_conventional_commits", 
                    "tag_format": "$version", 
                    "update_changelog_on_bump": true
                }
            }''')
            cz_json_file_path = os.path.join(temp_dir.path, '.cz.json')

            step_config = {
                'cz-json': cz_json_file_path,
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Commitizen',
                parent_work_dir_path=parent_work_dir_path
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    @patch('ploigos_step_runner.step_implementers.generate_metadata.commitizen.sh')
    @patch('ploigos_step_runner.step_implementers.generate_metadata.commitizen.Repo')
    def test_run_step_pass_with_no_existing_tags(self, MockRepo, mock_sh):
        previous_dir = os.getcwd()

        try:
            with TempDirectory() as temp_dir:
                parent_work_dir_path = os.path.join(temp_dir.path, 'working')

                temp_dir.write('.cz.json', b'''{
                    "commitizen": {
                        "bump_message": "build: bump $current_version \\u2192 $new_version [skip-ci]", 
                        "name": "cz_conventional_commits", 
                        "tag_format": "$version", 
                        "update_changelog_on_bump": true
                    }
                }''')
                cz_json_path = os.path.join(temp_dir.path, '.cz.json')

                step_config = {
                    'cz-json': cz_json_path,
                    'repo-root': temp_dir.path
                }
                step_implementer = self.create_step_implementer(
                    step_config=step_config,
                    step_name='generate-metadata',
                    implementer='Commitizen',
                    parent_work_dir_path=parent_work_dir_path,
                )

                mock_sh.cz.bump.side_effect = functools.partial(
                    self._mock_cz_bump, 
                    path=os.path.join(temp_dir.path, '.cz.json'),
                    increment_type='minor'
                )
                MockRepo().tags = []
                result = step_implementer._run_step()

                expected_step_result = StepResult(
                    step_name='generate-metadata',
                    sub_step_name='Commitizen',
                    sub_step_implementer_name='Commitizen'
                )
                expected_step_result.success = True
                expected_step_result.add_artifact(name='app-version', value='0.1.0')

                self.assertEqual(result, expected_step_result)
        finally:
            os.chdir(previous_dir)

    @patch('ploigos_step_runner.step_implementers.generate_metadata.commitizen.sh')
    @patch('ploigos_step_runner.step_implementers.generate_metadata.commitizen.Repo')
    def test_run_step_pass_with_existing_tags(self, MockRepo, mock_sh):
        previous_dir = os.getcwd()

        try:
            with TempDirectory() as temp_dir:
                parent_work_dir_path = os.path.join(temp_dir.path, 'working')
                repo = Repo.init(str(temp_dir.path))

                temp_dir.write('.cz.json', b'''{
                    "commitizen": {
                        "bump_message": "build: bump $current_version \\u2192 $new_version [skip-ci]", 
                        "name": "cz_conventional_commits", 
                        "tag_format": "$version", 
                        "update_changelog_on_bump": true
                    }
                }''')
                cz_json_path = os.path.join(temp_dir.path, '.cz.json')

                step_config = {
                    'cz-json': cz_json_path,
                    'repo-root': temp_dir.path
                }
                step_implementer = self.create_step_implementer(
                    step_config=step_config,
                    step_name='generate-metadata',
                    implementer='Commitizen',
                    parent_work_dir_path=parent_work_dir_path,
                )

                mock_sh.cz.bump.side_effect = functools.partial(
                    self._mock_cz_bump, 
                    path=os.path.join(temp_dir.path, '.cz.json'),
                    increment_type='minor'
                )
                tag = collections.namedtuple('Tag', 'name')
                MockRepo().tags = [
                    tag(name='v_0.1.0__'),
                    tag(name='0.3.0'),
                    tag(name='version_4.34.0'),
                    tag(name='5.2.7-prerelease'),
                    tag(name='v3.142.0-test_abcxyz')
                ]
                result = step_implementer._run_step()

                expected_step_result = StepResult(
                    step_name='generate-metadata',
                    sub_step_name='Commitizen',
                    sub_step_implementer_name='Commitizen'
                )
                expected_step_result.success = True
                expected_step_result.add_artifact(name='app-version', value='5.3.0')

                self.assertEqual(result, expected_step_result)
        finally:
            os.chdir(previous_dir)

    @staticmethod
    def _mock_cz_bump(*args, path, increment_type, **kwargs):
        with open(path, 'r') as cz_json:
            version = json.loads(cz_json.read())['commitizen']['version']
            version = re.match(r'(?P<major>\d+).(?P<minor>\d+).(?P<patch>\d+)', version).groupdict()
            
            if increment_type == 'major':
                version['major'] = str(int(version['major']) + 1)
                version['minor'] = '0'
                version['patch'] = '0'

            if increment_type == 'minor':
                version['minor'] = str(int(version['minor']) + 1)
                version['patch'] = '0'

            if increment_type == 'patch':
                version['patch'] = str(int(version['patch']) + 1)

            kwargs['_out'].write(
                f'tag to create: {version["major"]}.{version["minor"]}.{version["patch"]}'
            )