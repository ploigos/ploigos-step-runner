import os

from testfixtures import TempDirectory

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

            #{'app-version': app_version, 'pre-release': 'master', 'build': build, 'version': version, 'image-tag': image_tag}}}
            runtime_args = {'repo-root': str(temp_dir.path)}
            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version': {'description': '', 'type': 'str', 'value': app_version},
                            }
                    },
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'pre-release': {'description': '', 'type': 'str', 'value': 'master'},
                            'build': {'description': '', 'type': 'str', 'value': build},
                        }
                    },
                    'SemanticVersion': {
                            'sub-step-implementer-name': 'SemanticVersion',
                            'success': True,
                            'message': '',
                            'artifacts': {
                                'version': {'description': '', 'type': 'str', 'value': version},
                                'image-tag': { 'description': '', 'type': 'str', 'value': image_tag},
                            }
                    }
                }
            }

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

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
            #{'app-version': app_version, 'pre-release': 'master', 'build': build, 'version': version, 'image-tag': image_tag}}}
            runtime_args = {'repo-root': str(temp_dir.path)}
            expected_step_results = {
                'generate-metadata': {
                    'Npm': {
                        'sub-step-implementer-name': 'Npm',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version': {'description': '', 'type': 'str', 'value': app_version},
                        }
                    },
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'pre-release': {'description': '', 'type': 'str', 'value': 'master'},
                            'build': {'description': '', 'type': 'str', 'value': build},
                            }
                    },
                    'SemanticVersion': {
                            'sub-step-implementer-name': 'SemanticVersion',
                            'success': True,
                            'message': '',
                            'artifacts': {
                                'version': {'description': '', 'type': 'str', 'value': version},
                                'image-tag': {'description': '', 'type': 'str', 'value': image_tag},
                            }
                    }
                }
            }

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

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
            #{'app-version': app_version, 'pre-release': pre_release, 'build': build, 'version': version, 'image-tag': image_tag}}}

            runtime_args={'repo-root': str(temp_dir.path)}
            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version': {'description': '', 'type': 'str', 'value': app_version },
                        }
                    },
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'pre-release': {'description': '', 'type': 'str', 'value': pre_release},
                            'build': {'description': '', 'type': 'str', 'value': build},
                            }
                    },
                    'SemanticVersion': {
                            'sub-step-implementer-name': 'SemanticVersion',
                            'success': True,
                            'message': '',
                            'artifacts': {
                                'version': {'description': '', 'type': 'str', 'value': version},
                                'image-tag': {'description': '', 'type': 'str', 'value': image_tag},
                            }
                    }
                }
            }

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

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
            #{'app-version': "42.1", 'pre-release': 'master', 'build': build, 'version': version, 'image-tag': image_tag}}}

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
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'pre-release': {'description': '', 'type': 'str', 'value': 'master'},
                            'build': {'description': '', 'type': 'str', 'value': build},
                            }
                    },
                    'SemanticVersion': {
                            'sub-step-implementer-name': 'SemanticVersion',
                            'success': True,
                            'message': '',
                            'artifacts': {
                                'version': {'description': '', 'type': 'str', 'value': version},
                                'image-tag': {'description': '', 'type': 'str', 'value': image_tag},
                            }
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path), 'app-version': app_version}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

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
            #'app-version': app_version, 'pre-release': 'master', 'build': git_branch_last_commit_hash[:7], 'version': version, 'image-tag': image_tag}}}

            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version': {'description': '', 'type': 'str', 'value': app_version},
                        }
                    },
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'pre-release': {'description': '', 'type': 'str', 'value': 'master'},
                            'build': {'description': '', 'type': 'str', 'value': git_branch_last_commit_hash[:7]},
                            }
                    },
                    'SemanticVersion': {
                            'sub-step-implementer-name': 'SemanticVersion',
                            'success': True,
                            'message': '',
                            'artifacts': {
                                'version': {'description': '', 'type': 'str', 'value': version},
                                'image-tag': {'description': '', 'type': 'str', 'value': image_tag},
                            }
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path), 'build': build}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )

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
            #{'app-version': app_version, 'pre-release': 'feature_test0', 'build': build, 'version': version, 'image-tag': image_tag}}}

            expected_step_results = {
                'generate-metadata': {
                    'Maven': {
                        'sub-step-implementer-name': 'Maven',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'app-version': {'description': '', 'type': 'str', 'value': app_version},
                        }
                    },
                    'Git': {
                        'sub-step-implementer-name': 'Git',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'pre-release': {'description': '', 'type': 'str', 'value': 'feature_test0'},
                            'build': {'description': '', 'type': 'str', 'value': build},
                            }
                    },
                    'SemanticVersion': {
                            'sub-step-implementer-name': 'SemanticVersion',
                            'success': True,
                            'message': '',
                            'artifacts': {
                                'version': {'description': '', 'type': 'str', 'value': version},
                                'image-tag': {'description': '', 'type': 'str', 'value': image_tag},
                            }
                    }
                }
            }

            runtime_args = {'repo-root': str(temp_dir.path), 'pre-release': pre_release}

            self.run_step_test_with_result_validation(
                temp_dir=temp_dir,
                step_name='generate-metadata',
                config=config,
                expected_step_results=expected_step_results,
                runtime_args=runtime_args
            )
