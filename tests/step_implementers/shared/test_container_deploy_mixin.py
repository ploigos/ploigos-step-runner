import os
from unittest.mock import patch

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.step_implementers.shared import ContainerDeployMixin
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class ContainerDeployMixinStepImplementerMock(ContainerDeployMixin, StepImplementer):
    def _run_step(self):
        pass

class TestContainerDeployMixinBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            parent_work_dir_path='',
            environment=None
    ):
        return self.create_given_step_implementer(
            step_implementer=ContainerDeployMixinStepImplementerMock,
            step_config=step_config,
            step_name='mock',
            implementer='ContainerDeployMixinStepImplementerMock',
            parent_work_dir_path=parent_work_dir_path,
            environment=environment
        )

class TestContainerDeployMixin_step_implementer_config_defaults(TestContainerDeployMixinBase):
    def test_results(self):
        defaults = ContainerDeployMixin.step_implementer_config_defaults()
        expected_defaults = {
            'use-container-image-short-addres': False,
            'use-container-image-digest': True
        }
        self.assertEqual(defaults, expected_defaults)

class TestContainerDeployMixin__required_config_or_result_keys(TestContainerDeployMixinBase):
    def test_results(self):
        required_keys = ContainerDeployMixin._required_config_or_result_keys()
        expected_required_keys = [
            'use-container-image-short-addres',
            'use-container-image-digest',
            [
                'container-image-pull-repository',
                'container-image-push-repository',
                'container-image-repository'
            ]
        ]
        self.assertEqual(required_keys, expected_required_keys)

@patch.object(StepImplementer, '_validate_required_config_or_previous_step_result_artifact_keys')
class TestStepImplementerDeployArgoCD_validate_required_config_or_previous_step_result_artifact_keys(
    TestContainerDeployMixinBase
):
    def test_success_with_pull_registry_with_pull_digest(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'container-image-pull-registry': 'mock-reg.xyz',
                'container-image-pull-digest': 'sha256:mockabc123'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_success_with_push_registry_with_pull_digest(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'container-image-push-registry': 'mock-reg.xyz',
                'container-image-pull-digest': 'sha256:mockabc123'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_success_with_registry_with_pull_digest(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'container-image-registry': 'mock-reg.xyz',
                'container-image-pull-digest': 'sha256:mockabc123'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_success_with_pull_registry_with_push_digest(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'container-image-pull-registry': 'mock-reg.xyz',
                'container-image-push-digest': 'sha256:mockabc123'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_success_with_pull_registry_with_digest(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'container-image-pull-registry': 'mock-reg.xyz',
                'container-image-push-digest': 'sha256:mockabc123'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_success_with_pull_registry_with_push_tag(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'use-container-image-digest': False,
                'container-image-pull-registry': 'mock-reg.xyz',
                'container-image-push-tag': 'v42-mock'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_success_with_pull_registry_with_pull_tag(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'use-container-image-digest': False,
                'container-image-pull-registry': 'mock-reg.xyz',
                'container-image-pull-tag': 'v42-mock'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_success_with_pull_registry_with_tag(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'use-container-image-digest': False,
                'container-image-pull-registry': 'mock-reg.xyz',
                'container-image-tag': 'v42-mock'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_success_use_short_address_with_pull_digest(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'use-container-image-short-addres': True,
                'container-image-pull-digest': 'sha256:mockabc123'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_fail_no_registry(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'container-image-pull-digest': 'sha256:mockabc123'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            with self.assertRaisesRegex(
                StepRunnerException,
                "If using container image address with container image registry"
                " \(use-container-image-short-addres is False\)"
                " then container image registry \('container-image-pull-registry',"
                " 'container-image-push-registry', 'container-image-registry'\) must be given."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_fail_no_digest(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'container-image-pull-registry': 'mock-reg.xyz'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            with self.assertRaisesRegex(
                StepRunnerException,
                "If deploying container image with container image digest"
                " \(use-container-image-digest is True\)"
                " in the container image address" \
                " then container image digest \('container-image-pull-digest'," \
                " 'container-image-push-digest', 'container-image-digest'\) must be given."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

    def test_fail_no_tag(
        self,
        mock_super_validate
    ):
        with TempDirectory() as temp_dir:
            # setup
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            step_config = {
                'use-container-image-digest': False,
                'container-image-pull-registry': 'mock-reg.xyz'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            with self.assertRaisesRegex(
                StepRunnerException,
                "If deploying container image with container image tag"
                " \(use-container-image-digest is False\)"
                " in the container image address" \
                " then container image digest \('container-image-pull-tag'," \
                " 'container-image-push-tag', 'container-image-tag'\) must be given."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            # validate
            mock_super_validate.assert_called_once()

class TestContainerDeployMixin___get_deploy_time_container_image_address(TestContainerDeployMixinBase):
    def test_container_image_pull_registry_with_digest(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository@sha256:mockabc123'
        )

    def test_container_image_pull_registry_with_tag(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': False,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository:v42-mock'
        )

    def test_container_image_push_registry_with_digest(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': True,
            'container-image-push-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository@sha256:mockabc123'
        )

    def test_container_image_push_registry_with_tag(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': False,
            'container-image-push-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository:v42-mock'
        )

    def test_container_image_registry_with_digest(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': True,
            'container-image-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository@sha256:mockabc123'
        )

    def test_container_image_registry_with_tag(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': False,
            'container-image-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository:v42-mock'
        )

    def test_container_image_repository(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository@sha256:mockabc123'
        )

    def test_container_image_push_repository(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository@sha256:mockabc123'
        )

    def test_container_image_push_digest(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-push-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository@sha256:mockabc123'
        )

    def test_container_image_digest(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository@sha256:mockabc123'
        )

    def test_container_image_push_tag(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': False,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-push-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository:v42-mock'
        )

    def test_container_image_tag(self):
        # setup test
        step_config = {
            'use-container-image-short-address': False,
            'use-container-image-digest': False,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-registry.xyz/mock-repository:v42-mock'
        )

    def test_container_image_pull_registry_with_digest_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository@sha256:mockabc123'
        )

    def test_container_image_pull_registry_with_tag_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': False,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository:v42-mock'
        )

    def test_container_image_push_registry_with_digest_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': True,
            'container-image-push-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository@sha256:mockabc123'
        )

    def test_container_image_push_registry_with_tag_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': False,
            'container-image-push-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository:v42-mock'
        )

    def test_container_image_registry_with_digest_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': True,
            'container-image-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository@sha256:mockabc123'
        )

    def test_container_image_registry_with_tag_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': False,
            'container-image-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-pull-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository:v42-mock'
        )

    def test_container_image_repository_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository@sha256:mockabc123'
        )

    def test_container_image_push_repository_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-repository': 'mock-repository',
            'container-image-pull-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository@sha256:mockabc123'
        )

    def test_container_image_push_digest_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-push-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository@sha256:mockabc123'
        )

    def test_container_image_digest_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': True,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-digest': 'sha256:mockabc123'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository@sha256:mockabc123'
        )

    def test_container_image_push_tag_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': False,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-push-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository:v42-mock'
        )

    def test_container_image_tag_deploy_user_container_image_short_address_true(self):
        # setup test
        step_config = {
            'use-container-image-short-address': True,
            'use-container-image-digest': False,
            'container-image-pull-registry': 'mock-registry.xyz',
            'container-image-pull-repository': 'mock-repository',
            'container-image-tag': 'v42-mock'
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config
        )

        # run test
        actual_container_image_address = step_implementer._get_deploy_time_container_image_address()

        # validate
        self.assertEqual(
            actual_container_image_address,
            'mock-repository:v42-mock'
        )
