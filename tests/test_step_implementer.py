import os
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from ploigos_step_runner import StepResult, WorkflowResult
from ploigos_step_runner.config import Config
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.step_runner import StepRunner
from testfixtures import TempDirectory

from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.sample_step_implementers import (
    FailStepImplementer, FooStepImplementer,
    RequiredStepConfigMultipleOptionsStepImplementer,
    WriteConfigAsResultsStepImplementer)


class TestStepImplementer(BaseStepImplementerTestCase):
    def _run_step_implementer_test(
        self,
        config,
        step,
        expected_step_results,
        test_dir,
        environment=None
    ):
        working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
        factory = StepRunner(
            config=config,
            results_file_name='step-runner-results.yml',
            work_dir_path=working_dir_path
        )
        factory.run_step(
            step_name=step,
            environment=environment
        )

        pickle = f'{working_dir_path}/step-runner-results.pkl'
        workflow_result = WorkflowResult.load_from_pickle_file(pickle)

        step_result = workflow_result.get_step_result(
            step_name=step
        )
        self.assertEqual(step_result, expected_step_results)

    def _setup_get_value_with_env_test(self, test_dir, environment):
        step_config = {
            'test': 'hello world',
            'old-param-name': 'foo42',
            'new-param-name': 'bar42'
        }

        parent_work_dir_path = os.path.join(test_dir.path, 'working')

        workflow_result = WorkflowResult()

        step_result_no_evn = StepResult(
            step_name='foo',
            sub_step_name='Mock',
            sub_step_implementer_name='Mock'
        )
        step_result_no_evn.add_artifact(
            name='container-image-tag',
            value='localhost/mock:0.42.0-weird'
        )
        workflow_result.add_step_result(step_result=step_result_no_evn)

        step_result_deploy_test = StepResult(
            step_name='deploy',
            sub_step_name='ArgoCD',
            sub_step_implementer_name='ArgoCD',
            environment='TEST'
        )
        step_result_deploy_test.add_artifact(
            name='deployed-host-urls',
            value='https://awesome-app.test.ploigos.xyz'
        )
        step_result_deploy_test.add_artifact(
            name='container-image-tag',
            value='localhost/test/mock:0.42.0-weird'
        )
        workflow_result.add_step_result(step_result=step_result_deploy_test)

        step_result_deploy_prod = StepResult(
            step_name='deploy',
            sub_step_name='ArgoCD',
            sub_step_implementer_name='ArgoCD',
            environment='PROD'
        )
        step_result_deploy_prod.add_artifact(
            name='deployed-host-urls',
            value='https://awesome-app.prod.ploigos.xyz'
        )
        step_result_deploy_test.add_artifact(
            name='container-image-tag',
            value='localhost/prod/mock:0.42.0-weird'
        )
        workflow_result.add_step_result(step_result=step_result_deploy_prod)
        pickle_filename = os.path.join(parent_work_dir_path, 'step-runner-results.pkl')
        workflow_result.write_to_pickle_file(pickle_filename=pickle_filename)

        return self.create_given_step_implementer(
            step_implementer=FooStepImplementer,
            step_config=step_config,
            step_name='foo',
            implementer='FooStepImplementer',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            environment=environment
        )

@patch.object(StepImplementer, '_StepImplementer__add_additional_artifacts_to_step_result')
class TestStepImplementer_run_step(TestStepImplementer):
    def test_one_step_writes_to_empty_results_file(
        self,
        mock_add_additional_artifacts_to_step_result
    ):
        config1 = {
            'step-runner-config': {
                'write-config-as-results': {
                    'implementer':
                        'tests.helpers.sample_step_implementers.'
                        'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }
        config1_expected_step_results = StepResult(
            step_name='write-config-as-results',
            sub_step_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer'
        )
        config1_expected_step_results.success=True
        config1_expected_step_results.add_artifact(
            name='config-1',
            value='config-1'
        )
        config1_expected_step_results.add_artifact(
            name='config-overwrite-me',
            value='config-1'
        )
        config1_expected_step_results.add_artifact(
            name='required-config-key',
            value='required'
        )

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results,
                test_dir
            )

        mock_add_additional_artifacts_to_step_result.assert_called_once()

    def test_one_step_existing_results_file_bad_pickle(
        self,
        mock_add_additional_artifacts_to_step_result
    ):
        config = {
            'step-runner-config': {
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            results_file_path = os.path.join(results_dir_path, 'step-runner-results.pkl')
            test_dir.write(results_file_path, b'''{}bad[yaml}''')

            with self.assertRaisesRegex(
                    StepRunnerException,
                    r'error loading .*'):
                self._run_step_implementer_test(
                    config,
                    'write-config-as-results',
                    None,
                    test_dir
                )

        mock_add_additional_artifacts_to_step_result.assert_not_called()

    def test_boolean_false_config_variable(
        self,
        mock_add_additional_artifacts_to_step_result
    ):
        config = {
            'step-runner-config': {
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'required-config-key': False
                    }
                }
            }
        }

        config_expected_step_results = StepResult(
            step_name='write-config-as-results',
            sub_step_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer'
        )
        config_expected_step_results.success=True
        config_expected_step_results.add_artifact(
            name='required-config-key',
            value=False
        )

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config,
                'write-config-as-results',
                config_expected_step_results,
                test_dir
            )

        mock_add_additional_artifacts_to_step_result.assert_called_once()

    def test_one_step_existing_results_file_empty(
        self,
        mock_add_additional_artifacts_to_step_result
    ):
        config = {
            'step-runner-config': {
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }

        config_expected_step_results = StepResult(
            step_name='write-config-as-results',
            sub_step_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer'
        )
        config_expected_step_results.success = True
        config_expected_step_results.add_artifact(
            name='config-1',
            value='config-1'
        )
        config_expected_step_results.add_artifact(
            name='config-overwrite-me',
            value='config-1'
        )
        config_expected_step_results.add_artifact(
            name='required-config-key',
            value='required'
        )

        with TempDirectory() as test_dir:
            results_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            results_file_path = os.path.join(results_dir_path, 'step-runner-results.pkl')
            test_dir.write(results_file_path, b'''''')
            self._run_step_implementer_test(
                config,
                'write-config-as-results',
                config_expected_step_results,
                test_dir
            )

        mock_add_additional_artifacts_to_step_result.assert_called_once()

    def test_global_environment_default_config(
        self,
        mock_add_additional_artifacts_to_step_result
    ):
        config1 = {
            'step-runner-config': {
                'global-environment-defaults': {
                    'SAMPLE-ENV-1': {
                        'sample-config-option-1': 'sample env 1 value'
                    },
                    'SAMPLE-ENV-2': {
                        'sample-config-option-1': 'sample env 2 value'
                    }
                },
                'write-config-as-results': {
                    'implementer':
                        'tests.helpers.sample_step_implementers.'
                        'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    }
                }
            }
        }
        config1_expected_step_results_env_1 = {
            'SAMPLE-ENV-1': {
                'write-config-as-results': {
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'environment-name':
                                {'description': '', 'value': 'SAMPLE-ENV-1'},
                            'sample-config-option-1':
                                {'description': '', 'value': 'sample env 1 value'},
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'},
                        }
                    }
                }
            }
        }
        config1_expected_step_results_env_2 = {
            'SAMPLE-ENV-2': {
                'write-config-as-results': {
                    'tests.helpers.sample_step_implementers.'
                    'WriteConfigAsResultsStepImplementer': {
                        'sub-step-implementer-name':
                            'tests.helpers.sample_step_implementers.'
                            'WriteConfigAsResultsStepImplementer',
                        'success': True,
                        'message': '',
                        'artifacts': {
                            'environment-name':
                                {'description': '', 'value': 'SAMPLE-ENV-2'},
                            'config-1':
                                {'description': '', 'value': 'config-1'},
                            'sample-config-option-1':
                                {'description': '', 'value': 'sample env 2 value'},
                            'config-overwrite-me':
                                {'description': '', 'value': 'config-1'},
                            'required-config-key':
                                {'description': '', 'value': 'required'}
                        }
                    }
                }
            }
        }

        config1_expected_step_results_env_1 = StepResult(
            step_name='write-config-as-results',
            sub_step_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            environment='SAMPLE-ENV-1'
        )
        config1_expected_step_results_env_1.success=True
        config1_expected_step_results_env_1.add_artifact(
            name='environment-name',
            value='SAMPLE-ENV-1'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='sample-config-option-1',
            value='sample env 1 value'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='config-1',
            value='config-1'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='config-overwrite-me',
            value='config-1'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='required-config-key',
            value='required'
        )

        config1_expected_step_results_env_2 = StepResult(
            step_name='write-config-as-results',
            sub_step_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            environment='SAMPLE-ENV-2'
        )
        config1_expected_step_results_env_2.success=True
        config1_expected_step_results_env_2.add_artifact(
            name='environment-name',
            value='SAMPLE-ENV-2'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='sample-config-option-1',
            value='sample env 2 value'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='config-1',
            value='config-1'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='config-overwrite-me',
            value='config-1'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='required-config-key',
            value='required'
        )

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_1,
                test_dir,
                'SAMPLE-ENV-1'
            )
        mock_add_additional_artifacts_to_step_result.assert_called_once()

        mock_add_additional_artifacts_to_step_result.reset_mock()
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_2,
                test_dir,
                'SAMPLE-ENV-2'
            )
        mock_add_additional_artifacts_to_step_result.assert_called_once()

    def test_step_environment_config(
        self,
        mock_add_additional_artifacts_to_step_result
    ):
        config1 = {
            'step-runner-config': {
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    },
                    'environment-config': {
                        'SAMPLE-ENV-1': {
                            'sample-config-option-1': 'step env config - env 1 value'
                        },
                        'SAMPLE-ENV-2': {
                            'sample-config-option-1': 'step env config - env 2 value'
                        }
                    }
                }
            }
        }

        config1_expected_step_results_env_1 = StepResult(
            step_name='write-config-as-results',
            sub_step_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            environment='SAMPLE-ENV-1'
        )
        config1_expected_step_results_env_1.success=True
        config1_expected_step_results_env_1.add_artifact(
            name='sample-config-option-1',
            value='step env config - env 1 value'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='config-1',
            value='config-1'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='config-overwrite-me',
            value='config-1'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='required-config-key',
            value='required'
        )

        config1_expected_step_results_env_2 = StepResult(
            step_name='write-config-as-results',
            sub_step_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            environment='SAMPLE-ENV-2'
        )
        config1_expected_step_results_env_2.success=True
        config1_expected_step_results_env_2.add_artifact(
            name='sample-config-option-1',
            value='step env config - env 2 value'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='config-1',
            value='config-1'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='config-overwrite-me',
            value='config-1'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='required-config-key',
            value='required'
        )

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_1,
                test_dir,
                'SAMPLE-ENV-1'
            )
        mock_add_additional_artifacts_to_step_result.assert_called_once()

        mock_add_additional_artifacts_to_step_result.reset_mock()
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_2,
                test_dir,
                'SAMPLE-ENV-2'
            )
        mock_add_additional_artifacts_to_step_result.assert_called_once()


    def test_global_environment_default_and_step_environment_config(
        self,
        mock_add_additional_artifacts_to_step_result
    ):
        config1 = {
            'step-runner-config': {
                'global-environment-defaults': {
                    'SAMPLE-ENV-1': {
                        'sample-config-option-1': 'global env config - env 1 value - 1',
                        'sample-config-option-2': 'global env config - env 1 value - 2'
                    },
                    'SAMPLE-ENV-2': {
                        'sample-config-option-1': 'global env config - env 2 value - 1',
                        'sample-config-option-2': 'global env config - env 2 value - 2'
                    }
                },
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1',
                        'required-config-key': 'required'
                    },
                    'environment-config': {
                        'SAMPLE-ENV-1': {
                            'sample-config-option-1': 'step env config - env 1 value - 1'
                        },
                        'SAMPLE-ENV-2': {
                            'sample-config-option-1': 'step env config - env 2 value - 1'
                        }
                    },
                }
            }
        }

        config1_expected_step_results_env_1 = StepResult(
            step_name='write-config-as-results',
            sub_step_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            environment='SAMPLE-ENV-1'
        )
        config1_expected_step_results_env_1.success=True
        config1_expected_step_results_env_1.add_artifact(
            name='environment-name',
            value='SAMPLE-ENV-1'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='sample-config-option-1',
            value='step env config - env 1 value - 1'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='sample-config-option-2',
            value='global env config - env 1 value - 2'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='config-1',
            value='config-1'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='config-overwrite-me',
            value='config-1'
        )
        config1_expected_step_results_env_1.add_artifact(
            name='required-config-key',
            value='required'
        )

        config1_expected_step_results_env_2 = StepResult(
            step_name='write-config-as-results',
            sub_step_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.'
                'WriteConfigAsResultsStepImplementer',
            environment='SAMPLE-ENV-2'
        )
        config1_expected_step_results_env_2.success=True
        config1_expected_step_results_env_2.add_artifact(
            name='environment-name',
            value='SAMPLE-ENV-2'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='sample-config-option-1',
            value='step env config - env 2 value - 1'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='sample-config-option-2',
            value='global env config - env 2 value - 2'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='config-1',
            value='config-1'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='config-overwrite-me',
            value='config-1'
        )
        config1_expected_step_results_env_2.add_artifact(
            name='required-config-key',
            value='required'
        )

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_1,
                test_dir,
                'SAMPLE-ENV-1'
            )
        mock_add_additional_artifacts_to_step_result.assert_called_once()

        mock_add_additional_artifacts_to_step_result.reset_mock()
        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config1,
                'write-config-as-results',
                config1_expected_step_results_env_2,
                test_dir,
                'SAMPLE-ENV-2'
            )
        mock_add_additional_artifacts_to_step_result.assert_called_once()

    def test_missing_required_config_key(
        self,
        mock_add_additional_artifacts_to_step_result
    ):
        config = {
            'step-runner-config': {
                'required-step-config-test': {
                    'implementer':
                        'tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer',
                    'config': {}
                }
            }
        }

        expected_results = StepResult(
            step_name='required-step-config-test',
            sub_step_name='tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.RequiredStepConfigStepImplementer'
        )
        expected_results.success = False
        expected_results.message = "Missing required step configuration" \
            " or previous step result artifact keys: ['required-config-key']"

        with TempDirectory() as test_dir:
            self._run_step_implementer_test(
                config,
                'required-step-config-test',
                expected_results,
                test_dir
            )

        mock_add_additional_artifacts_to_step_result.assert_not_called()

class TestStepImplementer_other(TestStepImplementer):
    def test_empty_constructor_params(self):
        config = Config({
            'step-runner-config': {
                'write-config-as-results': {
                    'implementer': 'tests.helpers.sample_step_implementers.'
                                   'WriteConfigAsResultsStepImplementer'
                }
            }
        })
        step_config = config.get_step_config('write-config-as-results')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.'
            'WriteConfigAsResultsStepImplementer')

        step = WriteConfigAsResultsStepImplementer(
            workflow_result=None,
            parent_work_dir_path='',
            config=sub_step
        )

        self.assertEqual(step.step_environment_config, {})
        self.assertEqual(step.step_config, {})
        self.assertEqual(step.global_config_defaults, {})
        self.assertEqual(step.global_environment_config_defaults, {})

    def test_write_working_file(self):
        config = Config({
            'step-runner-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                workflow_result=WorkflowResult(),
                parent_work_dir_path=working_dir_path,
                config=sub_step
            )

            step.write_working_file('test-working-file', b'hello world')

            with open(os.path.join(working_dir_path, 'foo', 'test-working-file'), 'r') \
                    as working_file:
                self.assertEqual(working_file.read(), 'hello world')

    def test_write_working_file_touch(self):
        config = Config({
            'step-runner-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                workflow_result=WorkflowResult(),
                parent_work_dir_path=working_dir_path,
                config=sub_step
            )

            step.write_working_file('foo/test.json')

            working_file_path = os.path.join(working_dir_path, 'foo/foo/test.json')
            self.assertTrue(os.path.exists(working_file_path))

            with open(working_file_path, 'r') as working_file:
                self.assertEqual(working_file.read(), '')

    def test_get_config_value(self):
        step_config = {
            'test': 'hello world'
        }

        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            step = self.create_given_step_implementer(
                step_implementer=FooStepImplementer,
                step_config=step_config,
                step_name='foo',
                implementer='FooStepImplementer',
                parent_work_dir_path=parent_work_dir_path
            )

            self.assertEqual(step.get_config_value('test'), 'hello world')
            self.assertIsNone(step.get_config_value('does-not-exist'))

    def test_get_config_value_with_env(self):
        config = Config({
            'step-runner-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {
                        'test': 'hello world',
                        'env-config-override-key': 'override-me'
                    },
                    'environment-config': {
                        'SAMPLE-ENV-1': {
                            'env-config-override-key': 'step env config - env 1 value - 1'
                        },
                        'SAMPLE-ENV-2': {
                            'env-config-override-key': 'step env config - env 2 value - 1'
                        }
                    },
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                workflow_result=WorkflowResult(),
                parent_work_dir_path=working_dir_path,
                config=sub_step,
                environment='SAMPLE-ENV-1'
            )

            self.assertEqual(step.get_config_value('test'), 'hello world')
            self.assertIsNone(step.get_config_value('does-not-exist'))
            self.assertEqual(
                step.get_config_value('env-config-override-key'),
                'step env config - env 1 value - 1')

    def test_has_config_value(self):
        config = Config({
            'step-runner-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {
                        'test': 'hello world',
                        'env-config-override-key': 'override-me',
                        'username': 'foo',
                        'password': 'bar'
                    },
                    'environment-config': {
                        'SAMPLE-ENV-1': {
                            'env-config-override-key': 'step env config - env 1 value - 1'
                        },
                        'SAMPLE-ENV-2': {
                            'env-config-override-key': 'step env config - env 2 value - 1'
                        }
                    },
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                workflow_result=WorkflowResult(),
                parent_work_dir_path=working_dir_path,
                config=sub_step,
                environment='SAMPLE-ENV-1'
            )

            self.assertFalse(step.has_config_value('bar'))
            self.assertFalse(step.has_config_value(['bar']))

            self.assertFalse(step.has_config_value(['username', 'foo'], False))
            self.assertTrue(step.has_config_value(['username', 'foo'], True))

            self.assertTrue(step.has_config_value(['username', 'password'], False))
            self.assertTrue(step.has_config_value(['username', 'password'], True))

    def test_fail(self):
        config = Config({
            'step-runner-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FailStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FailStepImplementer')

        with TempDirectory() as test_dir:
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FailStepImplementer(
                workflow_result=WorkflowResult(),
                parent_work_dir_path=working_dir_path,
                config=sub_step
            )
            result = step.run_step()

        self.assertEqual(False, result.success)

    def test_create_working_dir_sub_dir(self):
        config = Config({
            'step-runner-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        with TempDirectory() as test_dir:
            working_dir_path = os.path.join(test_dir.path, 'step-runner-working')
            step = FooStepImplementer(
                workflow_result=WorkflowResult(),
                parent_work_dir_path=working_dir_path,
                config=sub_step
            )

            sub = step.create_working_dir_sub_dir('folder1')
            self.assertEqual(sub, f'{working_dir_path}/foo/folder1')
            self.assertEqual(True, os.path.isdir(sub))

            sub = step.create_working_dir_sub_dir('folder1/folder2/folder3')
            self.assertEqual(sub, f'{working_dir_path}/foo/folder1/folder2/folder3')
            self.assertEqual(True, os.path.isdir(sub))

class TestStepImplementer_get_value(TestStepImplementer):
    def test_get_value_no_env(self):
        step_config = {
            'test': 'hello world'
        }

        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            artifact_config = {
                'fake-previous-step-artifact': {
                    'description': '',
                    'value': 'world hello'
                },
            }

            workflow_result = self.setup_previous_result(parent_work_dir_path, artifact_config)

            step = self.create_given_step_implementer(
                step_implementer=FooStepImplementer,
                step_config=step_config,
                step_name='foo',
                implementer='FooStepImplementer',
                workflow_result=workflow_result,
                parent_work_dir_path=parent_work_dir_path
            )

            self.assertEqual(step.get_value('test'), 'hello world')
            self.assertEqual(step.get_value('fake-previous-step-artifact'), 'world hello')
            self.assertIsNone(step.get_value('does-not-exist'))

    def test_get_value_from_artifact_without_specifing_environment_where_last_artifact_was_from_environment_and_artifact_never_set_without_environment(self):
        with TempDirectory() as test_dir:
            step = self._setup_get_value_with_env_test(test_dir=test_dir, environment=None)
            self.assertEqual(
                step.get_value('deployed-host-urls'),
                'https://awesome-app.prod.ploigos.xyz'
            )

    # NOTE: maybe this should actually return the first instance where the environment was not set?
    def test_get_value_from_artifact_without_specifing_environment_where_last_artifact_was_from_environment_and_artifact_was_set_without_environment(self):
        with TempDirectory() as test_dir:
            step = self._setup_get_value_with_env_test(test_dir=test_dir, environment=None)
            self.assertEqual(
                step.get_value('container-image-tag'),
                'localhost/prod/mock:0.42.0-weird'
            )

    def test_get_value_from_step_run_in_environment_that_has_result_value_for_that_environment_1(self):
        with TempDirectory() as test_dir:
            step = self._setup_get_value_with_env_test(test_dir=test_dir, environment='TEST')
            self.assertEqual(
                step.get_value('deployed-host-urls'),
                'https://awesome-app.test.ploigos.xyz'
            )

    def test_get_value_from_step_run_in_environment_that_has_result_value_for_that_environment_2(self):
        with TempDirectory() as test_dir:
            step = self._setup_get_value_with_env_test(test_dir=test_dir, environment='PROD')
            self.assertEqual(
                step.get_value('deployed-host-urls'),
                'https://awesome-app.prod.ploigos.xyz'
            )

    def test_get_value_from_step_run_in_environment_that_nodes_not_have_result_value_for_that_environment(self):
        with TempDirectory() as test_dir:
            step = self._setup_get_value_with_env_test(test_dir=test_dir, environment='RANDOM')
            self.assertEqual(
                step.get_value('deployed-host-urls'),
                'https://awesome-app.prod.ploigos.xyz'
            )

    def test_get_value_multiple_keys_1(self):
        with TempDirectory() as test_dir:
            step = self._setup_get_value_with_env_test(test_dir=test_dir, environment='RANDOM')
            self.assertEqual(
                step.get_value(['old-param-name', 'new-param-name']),
                'foo42'
            )

    def test_get_value_multiple_keys_2(self):
        with TempDirectory() as test_dir:
            step = self._setup_get_value_with_env_test(test_dir=test_dir, environment='RANDOM')
            self.assertEqual(
                step.get_value(['new-param-name', 'old-param-name']),
                'bar42'
            )

    def test_get_value_multiple_keys_3(self):
        with TempDirectory() as test_dir:
            step = self._setup_get_value_with_env_test(test_dir=test_dir, environment='RANDOM')
            self.assertEqual(
                step.get_value(['does-not-exist', 'old-param-name']),
                'foo42'
            )

    def test_get_value_multiple_keys_4(self):
        with TempDirectory() as test_dir:
            step = self._setup_get_value_with_env_test(test_dir=test_dir, environment='RANDOM')
            self.assertEqual(
                step.get_value(['old-param-name', 'does-not-exist']),
                'foo42'
            )

class TestStepImplementer_validate_required_config_or_previous_step_result_artifact_keys(TestStepImplementer):
    def test__validate_required_config_or_previous_step_result_artifact_keys_mutliple_keys_missing_config(self):
        with TempDirectory() as test_dir:
            step_config = {}

            step = self.create_given_step_implementer(
                step_implementer=RequiredStepConfigMultipleOptionsStepImplementer,
                step_config=step_config,
                step_name='foo',
                implementer='RequiredStepConfigMultipleOptionsStepImplementer',
                parent_work_dir_path=test_dir.path
            )

            with self.assertRaisesRegex(
                AssertionError,
                r"Missing required step configuration or previous step result artifact keys: "
                r"\[\['new-required-key', 'old-required-key'\]\]"
            ):
                step._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_mutliple_keys_first_option(self):
        with TempDirectory() as test_dir:
            step_config = {
                'new-required-key': 'new-value-42'
            }

            step = self.create_given_step_implementer(
                step_implementer=RequiredStepConfigMultipleOptionsStepImplementer,
                step_config=step_config,
                step_name='foo',
                implementer='RequiredStepConfigMultipleOptionsStepImplementer',
                parent_work_dir_path=test_dir.path
            )

            step._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_mutliple_keys_second_option(self):
        with TempDirectory() as test_dir:
            step_config = {
                'old-required-key': 'new-value-42'
            }

            step = self.create_given_step_implementer(
                step_implementer=RequiredStepConfigMultipleOptionsStepImplementer,
                step_config=step_config,
                step_name='foo',
                implementer='RequiredStepConfigMultipleOptionsStepImplementer',
                parent_work_dir_path=test_dir.path
            )

            step._validate_required_config_or_previous_step_result_artifact_keys()

class TestStepImplementer___print_data_string(TestStepImplementer):
    def test___print_data_string(self):
        stdout_buff = StringIO()
        with redirect_stdout(stdout_buff):
            StepImplementer._StepImplementer__print_data(
                title="Test Title",
                data="test string data"
            )

        stdout = stdout_buff.getvalue()
        self.assertEqual(
            stdout,
            "        Test Title\n"
            "            test string data\n\n"
        )

    def test___print_data_num(self):
        stdout_buff = StringIO()
        with redirect_stdout(stdout_buff):
            StepImplementer._StepImplementer__print_data(
                title="Test Title",
                data="42"
            )

        stdout = stdout_buff.getvalue()
        self.assertEqual(
            stdout,
            "        Test Title\n"
            "            42\n\n"
        )

    def test___print_data_list(self):
        stdout_buff = StringIO()
        with redirect_stdout(stdout_buff):
            StepImplementer._StepImplementer__print_data(
                title="Test Title",
                data=[
                    'hello',
                    'world',
                    42
                ]
            )

        stdout = stdout_buff.getvalue()
        self.assertEqual(
            stdout,
            '        Test Title\n'
            '            [\n'
            '                "hello",\n'
            '                "world",\n'
            '                42\n'
            '            ]\n\n'
        )

    def test___print_data_dict(self):
        stdout_buff = StringIO()
        with redirect_stdout(stdout_buff):
            StepImplementer._StepImplementer__print_data(
                title="Test Title",
                data={
                    'application-name': 'ref-quarkus-mvn-jenkins-std',
                    'container-registries': {
                        'quay-quay-enterprise.apps.tssc.rht-set.com': {
                            'password': '*************************************',
                            'username': 'ploigos-ref+workflow_reference_quarkus_mvn_jenkins_workflow_standard'
                        },
                        'registry.redhat.io': {
                            'password': '******************************',
                            'username': '6340056|tssc-integration-infra'
                        }
                    },
                    'maven-mirrors': {
                        'internal-mirror': {
                            'id': 'internal-mirror',
                            'mirror-of': '*',
                            'url': 'http://artifactory.apps.tssc.rht-set.com/artifactory/release/'
                        }
                    },
                    'maven-servers': {
                        'internal-mirror': {
                            'id': 'internal-server',
                            'password': '***********',
                            'username': 'tssc'
                        }
                    },
                    'organization': 'ploigos-ref',
                    'service-name': 'fruit'
                }
            )

        stdout = stdout_buff.getvalue()
        self.assertEqual(
            stdout,
            '        Test Title\n'
            '            {\n'
            '                "application-name": "ref-quarkus-mvn-jenkins-std",\n'
            '                "container-registries": {\n'
            '                    "quay-quay-enterprise.apps.tssc.rht-set.com": {\n'
            '                        "password": "*************************************",\n'
            '                        "username": "ploigos-ref+workflow_reference_quarkus_mvn_jenkins_workflow_standard"\n'
            '                    },\n'
            '                    "registry.redhat.io": {\n'
            '                        "password": "******************************",\n'
            '                        "username": "6340056|tssc-integration-infra"\n'
            '                    }\n'
            '                },\n'
            '                "maven-mirrors": {\n'
            '                    "internal-mirror": {\n'
            '                        "id": "internal-mirror",\n'
            '                        "mirror-of": "*",\n'
            '                        "url": "http://artifactory.apps.tssc.rht-set.com/artifactory/release/"\n'
            '                    }\n'
            '                },\n'
            '                "maven-servers": {\n'
            '                    "internal-mirror": {\n'
            '                        "id": "internal-server",\n'
            '                        "password": "***********",\n'
            '                        "username": "tssc"\n'
            '                    }\n'
            '                },\n'
            '                "organization": "ploigos-ref",\n'
            '                "service-name": "fruit"\n'
            '            }\n\n'
        )

class TestStepImplementer___add_additional_artifacts_to_step_result(BaseStepImplementerTestCase):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=FooStepImplementer,
            step_config=step_config,
            step_name='mock-step',
            implementer='FooStepImplementer',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_no_additional_artifacts(self):
        # setup test
        step_config = {}
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            parent_work_dir_path='/mock/work-dir'
        )

        # run test
        actual_step_result = StepResult(
            step_name='mock-step',
            sub_step_name='FooStepImplementer',
            sub_step_implementer_name='FooStepImplementer'
        )
        step_implementer._StepImplementer__add_additional_artifacts_to_step_result(
            step_result=actual_step_result
        )

        # verify results
        expected_step_result = StepResult(
            step_name='mock-step',
            sub_step_name='FooStepImplementer',
            sub_step_implementer_name='FooStepImplementer'
        )
        self.assertEqual(actual_step_result, expected_step_result)

    def test_additional_artifacts_list_of_dirs(self):
        # setup test
        step_config = {
            'additional-artifacts': [
                {
                    'name': 'mock-user-reports1',
                    'value': 'target/mock-foo'
                },
                {
                    'name': 'mock-user-reports2',
                    'value': 'target/mock-bar'
                }
            ]
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            parent_work_dir_path='/mock/work-dir'
        )

        # run test
        actual_step_result = StepResult(
            step_name='mock-step',
            sub_step_name='FooStepImplementer',
            sub_step_implementer_name='FooStepImplementer'
        )
        step_implementer._StepImplementer__add_additional_artifacts_to_step_result(
            step_result=actual_step_result
        )

        # verify results
        expected_step_result = StepResult(
            step_name='mock-step',
            sub_step_name='FooStepImplementer',
            sub_step_implementer_name='FooStepImplementer'
        )
        expected_step_result.add_artifact(
            name='mock-user-reports1',
            value='target/mock-foo'
        )
        expected_step_result.add_artifact(
            name='mock-user-reports2',
            value='target/mock-bar'
        )
        self.assertEqual(actual_step_result, expected_step_result)

    def test_additional_artifacts_list_of_strings(self):
        # setup test
        step_config = {
            'additional-artifacts': [
                'target/mock-foo',
                'target/mock-bar'
            ]
        }
        step_implementer = self.create_step_implementer(
            step_config=step_config,
            parent_work_dir_path='/mock/work-dir'
        )

        # run test
        actual_step_result = StepResult(
            step_name='mock-step',
            sub_step_name='FooStepImplementer',
            sub_step_implementer_name='FooStepImplementer'
        )
        step_implementer._StepImplementer__add_additional_artifacts_to_step_result(
            step_result=actual_step_result
        )

        # verify results
        expected_step_result = StepResult(
            step_name='mock-step',
            sub_step_name='FooStepImplementer',
            sub_step_implementer_name='FooStepImplementer'
        )
        expected_step_result.add_artifact(
            name='mock-foo',
            value='target/mock-foo'
        )
        expected_step_result.add_artifact(
            name='mock-bar',
            value='target/mock-bar'
        )
        self.assertEqual(actual_step_result, expected_step_result)
