import os

from testfixtures import TempDirectory
import yaml
import sys

from git import Repo
from git import InvalidGitRepositoryError

from tssc import TSSCFactory
from tssc.step_implementers.generate_metadata import Git
from tssc.step_implementers.generate_metadata import Maven
from tssc.step_implementers.generate_metadata import Npm

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase
from tests.helpers.test_utils import *

class TestStepImplementerGenerateMetadataNpm(BaseTSSCTestCase):
    def test_no_provided_app_version(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))


            create_git_commit_with_sample_file(temp_dir, repo)

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

            expected_step_results = {}

            with self.assertRaises(ValueError):
                run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})

    def test_no_provided_build(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('pom.xml',b'''<project>
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

            expected_step_results = {}

            with self.assertRaises(ValueError):
                run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path), 'pre-release': 'beta0'})

    def test_no_provided_pre_release(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('pom.xml',b'''<project>
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

            expected_step_results = {}

            with self.assertRaises(ValueError):
                run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path), 'build': '1234'})


    def test_maven_git_and_version_master_branch(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('pom.xml',b'''<project>
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
                            'implementer': 'Git'
                        },
                        {
                            'implementer': 'SemanticVersion'
                        }
                    ]
                }
            }

            git_branch_last_commit_hash = str(repo.head.reference.commit)
            app_version = "42.1"
            build = git_branch_last_commit_hash[:7]
            version = "{0}+{1}".format(app_version, build)
            image_tag = "{0}".format(app_version)
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': app_version, 'pre-release': 'master', 'build': build, 'version': version, 'container-image-version': image_tag}}}

            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})

    def test_npm_git_and_version_master_branch(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('package.json',b'''{
            "name": "my-awesome-package",
            "version": "1.0.0"
            }''')
            package_file_path = os.path.join(temp_dir.path, 'package.json')

            create_git_commit_with_sample_file(temp_dir, repo)

            config = {
                'tssc-config': {
                    'generate-metadata': [
                        {
                            'implementer': 'Npm',
                            'config': {
                                'package-file': str(package_file_path)
                            }
                        },
                        {
                            'implementer': 'Git'
                        },
                        {
                            'implementer': 'SemanticVersion'
                        }
                    ]
                }
            }

            git_branch_last_commit_hash = str(repo.head.reference.commit)
            app_version = "1.0.0"
            build = git_branch_last_commit_hash[:7]
            version = "{0}+{1}".format(app_version, build)
            image_tag = "{0}".format(app_version)
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': app_version, 'pre-release': 'master', 'build': build, 'version': version, 'container-image-version': image_tag}}}

            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})

    def test_maven_git_and_version_feature_branch(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('pom.xml',b'''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>42.1</version>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            # create commit
            create_git_commit_with_sample_file(temp_dir, repo)

            # checkout a feature branch
            git_new_branch = repo.create_head('feature/test0')
            git_new_branch.checkout()

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
                            'implementer': 'Git'
                        },
                        {
                            'implementer': 'SemanticVersion'
                        }
                    ]
                }
            }

            git_branch_last_commit_hash = str(repo.head.reference.commit)
            app_version = "42.1"
            build = git_branch_last_commit_hash[:7]
            pre_release = 'feature_test0'
            version = "{0}-{1}+{2}".format(app_version, pre_release, build)
            image_tag = "{0}-{1}".format(app_version, pre_release)
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': app_version, 'pre-release': pre_release, 'build': build, 'version': version, 'container-image-version': image_tag}}}

            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path)})

    def test_override_app_version_at_runtime(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('pom.xml',b'''<project>
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
                            'implementer': 'Git'
                        },
                        {
                            'implementer': 'SemanticVersion'
                        }
                    ]
                }
            }

            git_branch_last_commit_hash = str(repo.head.reference.commit)
            app_version = "24.5"
            build = git_branch_last_commit_hash[:7]
            version = "{0}+{1}".format(app_version, build)
            image_tag = "{0}".format(app_version)
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': "42.1", 'pre-release': 'master', 'build': build, 'version': version, 'container-image-version': image_tag}}}

            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path), 'app-version': app_version})

    def test_override_build_at_runtime(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('pom.xml',b'''<project>
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
                            'implementer': 'Git'
                        },
                        {
                            'implementer': 'SemanticVersion'
                        }
                    ]
                }
            }

            git_branch_last_commit_hash = str(repo.head.reference.commit)
            app_version = "42.1"
            build = "1234"
            version = "{0}+{1}".format(app_version, build)
            image_tag = "{0}".format(app_version)
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': app_version, 'pre-release': 'master', 'build': git_branch_last_commit_hash[:7], 'version': version, 'container-image-version': image_tag}}}

            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path), 'build': build})

    def test_override_pre_release_at_runtime(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            temp_dir.write('pom.xml',b'''<project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.mycompany.app</groupId>
        <artifactId>my-app</artifactId>
        <version>42.1</version>
    </project>''')
            pom_file_path = os.path.join(temp_dir.path, 'pom.xml')

            # create commit
            create_git_commit_with_sample_file(temp_dir, repo)

            # checkout a feature branch
            git_new_branch = repo.create_head('feature/test0')
            git_new_branch.checkout()

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
                            'implementer': 'Git'
                        },
                        {
                            'implementer': 'SemanticVersion'
                        }
                    ]
                }
            }

            git_branch_last_commit_hash = str(repo.head.reference.commit)
            app_version = "42.1"
            build = git_branch_last_commit_hash[:7]
            pre_release = 'beta1'
            version = "{0}-{1}+{2}".format(app_version, pre_release, build)
            image_tag = "{0}-{1}".format(app_version, pre_release)
            expected_step_results = {'tssc-results': {'generate-metadata': {'app-version': app_version, 'pre-release': 'feature_test0', 'build': build, 'version': version, 'container-image-version': image_tag}}}

            run_step_test_with_result_validation(temp_dir, 'generate-metadata', config, expected_step_results, runtime_args={'repo-root': str(temp_dir.path), 'pre-release': pre_release})
