import os

from testfixtures import TempDirectory
import yaml
import sys

from git import Repo

from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from tests.helpers.test_utils import create_git_commit_with_sample_file


class TestStepImplementerGenerateMetadataNpm(BaseStepImplementerTestCase):
    def test_no_provided_app_version(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            create_git_commit_with_sample_file(temp_dir, repo)
            git_branch_last_commit_hash = str(repo.head.reference.commit)

            config = {
                'tssc-config': {
                    'generate-metadata': [
                        {
                            'implementer': 'Git'
                        },
                        {
                            'implementer': 'SemanticVersion'
                        }
                    ]
                }
            }

            expected_step_results = {
                'generate-metadata': {
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'pre-release': {'description': '', 'type': 'str', 'value': 'master'},
                            'build': {
                                'description': '', 'type': 'str',
                                'value': git_branch_last_commit_hash[:7]
                            }
                        }
                    },
                    'SemanticVersion': {
                        'sub-step-implementer-name': 'SemanticVersion',
                        'success': False,
                        'message': 'No value for (app-version) provided via runtime flag '
                                   '(app-version) or from prior step implementer (generate-metadata)',
                        'artifacts': {}
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path)}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_no_provided_build(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('pom.xml', b'''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>42.1</version>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            create_git_commit_with_sample_file(temp_dir, repo)

            config = {
                'tssc-config': {
                    'generate-metadata': [
                        {
                            'implementer': 'Maven',
                            'config': {
                                'pom-file': str(pom_file_path)
                            }
                        },
                        {
                            'implementer': 'SemanticVersion'
                        }
                    ]
                }
            }

            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': True, 'message': '',
                        'artifacts': {
                            'app-version': {'description': '', 'type': 'str', 'value': '42.1'}
                        }
                    },
                    'SemanticVersion': {
                        'sub-step-implementer-name': 'SemanticVersion',
                        'success': False,
                        'message': 'No value for (build) provided via runtime flag '
                                   '(build) or from prior step implementer (generate-metadata)',
                        'artifacts': {}
                    }
                }
            }
            runtime_args = {'repo-root': str(temp_dir.path), 'pre-release': 'beta0'}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

    def test_no_provided_pre_release(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('pom.xml', b'''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>42.1</version>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            create_git_commit_with_sample_file(temp_dir, repo)

            config = {
                'tssc-config': {
                    'generate-metadata': [
                        {
                            'implementer': 'Maven',
                            'config': {
                                'pom-file': str(pom_file_path)
                            }
                        },
                        {
                            'implementer': 'SemanticVersion'
                        }
                    ]
                }
            }

            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version': {'description': '', 'type': 'str', 'value': '42.1'},
                        }
                    },
                    'SemanticVersion': {
                        'sub-step-implementer-name': 'SemanticVersion',
                        'success': False,
                        'message': 'No value for (pre-release) provided via runtime flag '
                                   '(pre-release) or from prior step implementer (generate-metadata)',
                        'artifacts': {}
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path), 'build': '1234'}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

