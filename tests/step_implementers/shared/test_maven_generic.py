import os
from pathlib import Path
from shutil import copyfile
from unittest.mock import PropertyMock, patch

from ploigos_step_runner import StepResult, StepRunnerException, WorkflowResult
from ploigos_step_runner.config.config import Config
from ploigos_step_runner.step_implementers.shared.maven_generic import \
    MavenGeneric
from ploigos_step_runner.utils.file import create_parent_dir
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


@patch("ploigos_step_runner.StepImplementer.__init__")
class TestStepImplementerSharedMavenGeneric___init__(BaseStepImplementerTestCase):

    def test_no_environment_no_maven_phases_and_goals(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        step_implementer = MavenGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config
        )

        self.assertIsNone(step_implementer._MavenGeneric__maven_settings_file)
        self.assertIsNone(step_implementer._MavenGeneric__maven_phases_and_goals)
        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None
        )

    def test_with_environment_no_maven_phases_and_goals(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        step_implementer = MavenGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='test-env'
        )

        self.assertIsNone(step_implementer._MavenGeneric__maven_settings_file)
        self.assertIsNone(step_implementer._MavenGeneric__maven_phases_and_goals)
        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment='test-env'
        )

    def test_no_environment_with_maven_phases_and_goals(self, mock_super_init):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = {}

        step_implementer = MavenGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            maven_phases_and_goals=['fake-phase']
        )

        self.assertIsNone(step_implementer._MavenGeneric__maven_settings_file)
        self.assertEqual(
            step_implementer._MavenGeneric__maven_phases_and_goals,
            ['fake-phase']
        )
        mock_super_init.assert_called_once_with(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=None
        )

class TestStepImplementerSharedMavenGeneric_step_implementer_config_defaults(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenGeneric.step_implementer_config_defaults(),
            {
                'pom-file': 'pom.xml',
                'tls-verify': True,
                'maven-profiles': [],
                'maven-additional-arguments': [],
                'maven-no-transfer-progress': True
            }
        )

class TestStepImplementerSharedMavenGeneric__required_config_or_result_keys(
    BaseStepImplementerTestCase
):
    def test_result(self):
        self.assertEqual(
            MavenGeneric._required_config_or_result_keys(),
            [
                'pom-file',
                'maven-phases-and-goals'
            ]
        )

class BaseTestStepImplementerSharedMavenGeneric(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=MavenGeneric,
            step_config=step_config,
            step_name='foo',
            implementer='MavenGeneric',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

@patch("ploigos_step_runner.StepImplementer._validate_required_config_or_previous_step_result_artifact_keys")
class TestStepImplementerSharedMavenGeneric__validate_required_config_or_previous_step_result_artifact_keys(
    BaseTestStepImplementerSharedMavenGeneric
):
    def test_valid(self, mock_super_validate):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path,
                'maven-phases-and-goals': 'fake-phase'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            Path(pom_file_path).touch()
            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once_with()

    def test_pom_file_does_not_exist(self, mock_super_validate):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = '/does/not/exist/pom.xml'
            step_config = {
                'pom-file': pom_file_path,
                'maven-phases-and-goals': 'fake-phase'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                AssertionError,
                rf'Given maven pom file \(pom-file\) does not exist: {pom_file_path}'
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
                mock_super_validate.assert_called_once_with()

class TestStepImplementerSharedMavenGeneric_maven_phases_and_goals(
    BaseTestStepImplementerSharedMavenGeneric
):
    def test_use_object_property_no_config_value(self):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        config = None

        step_implementer = MavenGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            maven_phases_and_goals=['fake-phase']
        )

        self.assertEqual(
            step_implementer.maven_phases_and_goals,
            ['fake-phase']
        )

    def test_use_object_property_with_config_value(self):
        workflow_result = WorkflowResult()
        parent_work_dir_path = '/fake/path'
        step_config = {
            'maven-phases-and-goals': ['config-value-fake-phase']
        }
        config = Config({
            Config.CONFIG_KEY: {
                'foo': [
                    {
                        'implementer': 'MavenGeneric',
                        'config': step_config
                    }
                ]

            }
        })

        step_implementer = MavenGeneric(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            maven_phases_and_goals=['object-property-fake-phase']
        )

        self.assertEqual(
            step_implementer.maven_phases_and_goals,
            ['object-property-fake-phase']
        )

    def test_use_config_value(self):
        parent_work_dir_path = '/fake/path'
        step_config = {
            'maven-phases-and-goals': ['config-value-fake-phase']
        }

        step_implementer = self.create_step_implementer(
            step_config=step_config,
            parent_work_dir_path=parent_work_dir_path,
        )

        self.assertEqual(
            step_implementer.maven_phases_and_goals,
            ['config-value-fake-phase']
        )

@patch(
    "ploigos_step_runner.step_implementers.shared.maven_generic.generate_maven_settings",
    return_value='/mock/settings.xml'
)
class TestStepImplementerSharedMavenGeneric_maven_settings_file(
    BaseTestStepImplementerSharedMavenGeneric
):
    def test_no_config(self, mock_gen_mvn_settings):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path,
                'maven-phases-and-goals': 'fake-phase'
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # call first time
            maven_settings_file = step_implementer.maven_settings_file
            self.assertEqual(
                maven_settings_file,
                '/mock/settings.xml'
            )
            mock_gen_mvn_settings.assert_called_once_with(
                working_dir=step_implementer.work_dir_path,
                maven_servers=None,
                maven_repositories=None,
                maven_mirrors=None
            )

            # call second time
            mock_gen_mvn_settings.reset_mock()
            maven_settings_file = step_implementer.maven_settings_file
            self.assertEqual(
                maven_settings_file,
                '/mock/settings.xml'
            )
            mock_gen_mvn_settings.assert_not_called()

    def test_given_config_maven_servers_maven_repos_and_maven_mirrors(self, mock_gen_mvn_settings):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            maven_servers = {
                'internal-mirror-1': {
                    'id': 'internal-server',
                    'password': 'you-wish',
                    'username': 'team-a'
                }
            }
            maven_repositories = {
                'internal-mirror-1': {
                    'id': 'internal-mirror-1',
                    'url': 'https://nexus.apps.ploigos.com/repository/maven-public/',
                    'snapshots': 'true',
                    'releases': 'true'
                }
            }
            maven_mirrors = {
                'internal-mirror-1': {
                    'id': 'internal-mirror',
                    'mirror-of': '*',
                    'url': 'https://nexus.apps.ploigos.com/repository/maven-public/'
                }
            }

            step_config = {
                'pom-file': pom_file_path,
                'maven-phases-and-goals': 'fake-phase',
                'maven-servers': maven_servers,
                'maven-repositories': maven_repositories,
                'maven-mirrors': maven_mirrors
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # call first time
            maven_settings_file = step_implementer.maven_settings_file
            self.assertEqual(
                maven_settings_file,
                '/mock/settings.xml'
            )
            mock_gen_mvn_settings.assert_called_once_with(
                working_dir=step_implementer.work_dir_path,
                maven_servers=maven_servers,
                maven_repositories=maven_repositories,
                maven_mirrors=maven_mirrors
            )

            # call second time
            mock_gen_mvn_settings.reset_mock()
            maven_settings_file = step_implementer.maven_settings_file
            self.assertEqual(
                maven_settings_file,
                '/mock/settings.xml'
            )
            mock_gen_mvn_settings.assert_not_called()

@patch('ploigos_step_runner.step_implementers.shared.maven_generic.write_effective_pom')
class TestStepImplementerSharedMavenGeneric__get_effective_pom(
    BaseTestStepImplementerSharedMavenGeneric
):
    def test_call_once(self, write_effective_pom_mock):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # mock effective pom
            Path(pom_file_path).touch()
            def write_effective_pom_mock_side_effect(pom_file_path, output_path, profiles):
                create_parent_dir(pom_file_path)
                copyfile(pom_file_path, output_path)
            write_effective_pom_mock.side_effect = write_effective_pom_mock_side_effect

            # first call
            expected_effective_pom_path = os.path.join(
                step_implementer.work_dir_path,
                'effective-pom.xml'
            )
            actual_effective_pom_path = step_implementer._get_effective_pom()
            self.assertEqual(actual_effective_pom_path, expected_effective_pom_path)
            write_effective_pom_mock.assert_called_once_with(
                pom_file_path=pom_file_path,
                output_path=expected_effective_pom_path,
                profiles=[]
            )

    def test__get_effective_pom_call_twice(self, write_effective_pom_mock):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # mock effective pom
            Path(pom_file_path).touch()
            def write_effective_pom_mock_side_effect(pom_file_path, output_path, profiles):
                create_parent_dir(pom_file_path)
                copyfile(pom_file_path, output_path)
            write_effective_pom_mock.side_effect = write_effective_pom_mock_side_effect

            # first call
            expected_effective_pom_path = os.path.join(
                step_implementer.work_dir_path,
                'effective-pom.xml'
            )
            actual_effective_pom_path = step_implementer._get_effective_pom()
            self.assertEqual(actual_effective_pom_path, expected_effective_pom_path)
            write_effective_pom_mock.assert_called_once_with(
                pom_file_path=pom_file_path,
                output_path=expected_effective_pom_path,
                profiles=[]
            )

            # second call
            write_effective_pom_mock.reset_mock()
            expected_effective_pom_path = os.path.join(
                step_implementer.work_dir_path,
                'effective-pom.xml'
            )
            actual_effective_pom_path = step_implementer._get_effective_pom()
            self.assertEqual(actual_effective_pom_path, expected_effective_pom_path)
            write_effective_pom_mock.assert_not_called()

    def test_call_with_profiles(self, write_effective_pom_mock):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path,
                'maven-profiles': ['mock-profile1']
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # mock effective pom
            Path(pom_file_path).touch()
            def write_effective_pom_mock_side_effect(pom_file_path, output_path, profiles):
                create_parent_dir(pom_file_path)
                copyfile(pom_file_path, output_path)
            write_effective_pom_mock.side_effect = write_effective_pom_mock_side_effect

            # first call
            expected_effective_pom_path = os.path.join(
                step_implementer.work_dir_path,
                'effective-pom.xml'
            )
            actual_effective_pom_path = step_implementer._get_effective_pom()
            self.assertEqual(actual_effective_pom_path, expected_effective_pom_path)
            write_effective_pom_mock.assert_called_once_with(
                pom_file_path=pom_file_path,
                output_path=expected_effective_pom_path,
                profiles=['mock-profile1']
            )

@patch('ploigos_step_runner.step_implementers.shared.maven_generic.get_xml_element_by_path')
@patch.object(MavenGeneric, '_get_effective_pom')
class TestStepImplementerSharedMavenGeneric__get_effective_pom_element(
    BaseTestStepImplementerSharedMavenGeneric
):
    def test_result(self, get_effective_pom_mock, get_xml_element_by_path_mock):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            def get_effective_pom_side_effect():
                return '/does/not/matter/pom.xml'
            get_effective_pom_mock.side_effect = get_effective_pom_side_effect

            step_implementer._get_effective_pom_element('foo')
            get_effective_pom_mock.assert_called_once_with()
            get_xml_element_by_path_mock.assert_called_once_with(
                '/does/not/matter/pom.xml',
                'foo',
                default_namespace='mvn'
            )

@patch('ploigos_step_runner.step_implementers.shared.maven_generic.run_maven')
@patch.object(
    MavenGeneric,
    'maven_phases_and_goals',
    new_callable=PropertyMock,
    return_value=['fake-phase']
)
@patch.object(
    MavenGeneric,
    'maven_settings_file',
    new_callable=PropertyMock,
    return_value='/fake/settings.xml'
)
class TestStepImplementerSharedMavenGeneric__run_maven_step(
    BaseTestStepImplementerSharedMavenGeneric
):
    def test_defaults(self, mock_settings_file, mock_phases_and_goals, mock_run_maven):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            mvn_output_file_path = os.path.join(test_dir.path, 'maven-output.txt')
            step_implementer._run_maven_step(
                mvn_output_file_path=mvn_output_file_path
            )

            mock_run_maven.assert_called_with(
                mvn_output_file_path=mvn_output_file_path,
                phases_and_goals=['fake-phase'],
                additional_arguments=[],
                pom_file=pom_file_path,
                tls_verify=True,
                profiles=[],
                no_transfer_progress=True,
                settings_file='/fake/settings.xml'
            )


    def test_custom_profile(self, mock_settings_file, mock_phases_and_goals, mock_run_maven):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path,
                'maven-profiles': ['fake-profile-1', 'fakse-profile-2']
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            mvn_output_file_path = os.path.join(test_dir.path, 'maven-output.txt')
            step_implementer._run_maven_step(
                mvn_output_file_path=mvn_output_file_path
            )

            mock_run_maven.assert_called_with(
                mvn_output_file_path=mvn_output_file_path,
                phases_and_goals=['fake-phase'],
                additional_arguments=[],
                pom_file=pom_file_path,
                tls_verify=True,
                profiles=['fake-profile-1', 'fakse-profile-2'],
                no_transfer_progress=True,
                settings_file='/fake/settings.xml'
            )

    def test_no_tls_verify(self, mock_settings_file, mock_phases_and_goals, mock_run_maven):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path,
                'tls-verify': False
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            mvn_output_file_path = os.path.join(test_dir.path, 'maven-output.txt')
            step_implementer._run_maven_step(
                mvn_output_file_path=mvn_output_file_path
            )

            mock_run_maven.assert_called_with(
                mvn_output_file_path=mvn_output_file_path,
                phases_and_goals=['fake-phase'],
                additional_arguments=[],
                pom_file=pom_file_path,
                tls_verify=False,
                profiles=[],
                no_transfer_progress=True,
                settings_file='/fake/settings.xml'
            )

    def test_yes_transfer_progress(self, mock_settings_file, mock_phases_and_goals, mock_run_maven):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path,
                'maven-no-transfer-progress': False
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            mvn_output_file_path = os.path.join(test_dir.path, 'maven-output.txt')
            step_implementer._run_maven_step(
                mvn_output_file_path=mvn_output_file_path
            )

            mock_run_maven.assert_called_with(
                mvn_output_file_path=mvn_output_file_path,
                phases_and_goals=['fake-phase'],
                additional_arguments=[],
                pom_file=pom_file_path,
                tls_verify=True,
                profiles=[],
                no_transfer_progress=False,
                settings_file='/fake/settings.xml'
            )

    def test_config_additional_arguments(
        self,
        mock_settings_file,
        mock_phases_and_goals,
        mock_run_maven
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path,
                'maven-additional-arguments': ['-Dfake.config.arg=True']
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            mvn_output_file_path = os.path.join(test_dir.path, 'maven-output.txt')
            step_implementer._run_maven_step(
                mvn_output_file_path=mvn_output_file_path
            )

            mock_run_maven.assert_called_with(
                mvn_output_file_path=mvn_output_file_path,
                phases_and_goals=['fake-phase'],
                additional_arguments=['-Dfake.config.arg=True'],
                pom_file=pom_file_path,
                tls_verify=True,
                profiles=[],
                no_transfer_progress=True,
                settings_file='/fake/settings.xml'
            )

    def test_step_implementer_additional_arguments(
        self,
        mock_settings_file,
        mock_phases_and_goals,
        mock_run_maven
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            mvn_output_file_path = os.path.join(test_dir.path, 'maven-output.txt')
            step_implementer._run_maven_step(
                mvn_output_file_path=mvn_output_file_path,
                step_implementer_additional_arguments=['-Dfake.step_implementer.arg=True']
            )

            mock_run_maven.assert_called_with(
                mvn_output_file_path=mvn_output_file_path,
                phases_and_goals=['fake-phase'],
                additional_arguments=['-Dfake.step_implementer.arg=True'],
                pom_file=pom_file_path,
                tls_verify=True,
                profiles=[],
                no_transfer_progress=True,
                settings_file='/fake/settings.xml'
            )

    def test_step_implementer_additional_arguments_and_config_additional_arguments(
        self,
        mock_settings_file,
        mock_phases_and_goals,
        mock_run_maven
    ):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            pom_file_path = os.path.join(test_dir.path, 'pom.xml')
            step_config = {
                'pom-file': pom_file_path,
                'maven-additional-arguments': ['-Dfake.config.arg=True']
            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            mvn_output_file_path = os.path.join(test_dir.path, 'maven-output.txt')
            step_implementer._run_maven_step(
                mvn_output_file_path=mvn_output_file_path,
                step_implementer_additional_arguments=['-Dfake.step_implementer.arg=True']
            )

            mock_run_maven.assert_called_with(
                mvn_output_file_path=mvn_output_file_path,
                phases_and_goals=['fake-phase'],
                additional_arguments=['-Dfake.step_implementer.arg=True', '-Dfake.config.arg=True'],
                pom_file=pom_file_path,
                tls_verify=True,
                profiles=[],
                no_transfer_progress=True,
                settings_file='/fake/settings.xml'
            )

@patch.object(MavenGeneric, '_run_maven_step')
@patch.object(MavenGeneric, 'write_working_file', return_value='/mock/mvn_output.txt')
class TestStepImplementerSharedMavenGeneric__run_step(
    BaseTestStepImplementerSharedMavenGeneric
):
    def test_success(self, mock_write_working_file, mock_run_maven_step):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='foo',
                sub_step_name='MavenGeneric',
                sub_step_implementer_name='MavenGeneric'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt'
            )

    def test_fail(self, mock_write_working_file, mock_run_maven_step):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step_config = {}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run step with mock failure
            mock_run_maven_step.side_effect = StepRunnerException('Mock error running maven')
            actual_step_result = step_implementer._run_step()

            # create expected step result
            expected_step_result = StepResult(
                step_name='foo',
                sub_step_name='MavenGeneric',
                sub_step_implementer_name='MavenGeneric'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from maven.",
                name='maven-output',
                value='/mock/mvn_output.txt'
            )
            expected_step_result.message = "Error running maven. " \
                "More details maybe found in 'maven-output' report artifact: "\
                "Mock error running maven"
            expected_step_result.success = False

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

            mock_write_working_file.assert_called_once()
            mock_run_maven_step.assert_called_with(
                mvn_output_file_path='/mock/mvn_output.txt'
            )
