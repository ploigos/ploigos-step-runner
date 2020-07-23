import pytest
from testfixtures import TempDirectory

import os
import yaml

from tssc import TSSCFactory, StepImplementer, TSSCException

class dummy_context_mgr():
    def __enter__(self):
        return None
    def __exit__(self, exc_type, exc_value, traceback):
        return False

class WriteConfigAsResultsStepImplementer(StepImplementer):
    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, {})

    @classmethod
    def step_name(cls):
        return 'write-config-as-results'

    def _run_step(self, runtime_step_config):
        return runtime_step_config

def _run_step_implementer_test(config, step, expected_step_results, test_dir):
    results_dir_path = os.path.join(test_dir.path, 'tssc-results')
    factory = TSSCFactory(config, results_dir_path)
    factory.run_step(step)

    with open(os.path.join(results_dir_path, "tssc-results.yml"), 'r') as step_results_file:
        step_results = yaml.safe_load(step_results_file.read())
        assert step_results == expected_step_results

def test_one_step_writes_to_empty_results_file():
    config1 = {
        'tssc-config': {
            'write-config-as-results': {
                'implementer': 'WriteConfigAsResultsStepImplementer',
                'config': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1'
                }
            }
        }
    }
    config1_expected_step_results = {
        'tssc-results': {
            'write-config-as-results': {
                'config-1': "config-1",
                'config-overwrite-me': 'config-1'
            }
        }
    }

    TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
    with TempDirectory() as test_dir:
        _run_step_implementer_test(
            config1,
            'write-config-as-results',
            config1_expected_step_results,
            test_dir
        )

def test_merge_results_from_running_same_step_twice_with_different_config():
    config1 = {
        'tssc-config': {
            'write-config-as-results': {
                'implementer': 'WriteConfigAsResultsStepImplementer',
                'config': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1'
                }
            }
        }
    }
    config1_expected_step_results = {
        'tssc-results': {
            'write-config-as-results': {
                'config-1': "config-1",
                'config-overwrite-me': 'config-1'
            }
        }
    }
    config2 = {
        'tssc-config': {
            'write-config-as-results': {
                'implementer': 'WriteConfigAsResultsStepImplementer',
                'config': {
                    'config-2': 'config-2',
                    'config-overwrite-me': 'config-2'
                }
            }
        }
    }
    config2_expected_step_results = {
        'tssc-results': {
            'write-config-as-results': {
                'config-1': "config-1",
                'config-2': 'config-2',
                'config-overwrite-me': 'config-2'
            }
        }
    }

    TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)

    with TempDirectory() as test_dir:
        _run_step_implementer_test(
            config1,
            'write-config-as-results',
            config1_expected_step_results,
            test_dir
        )
        _run_step_implementer_test(
            config2,
            'write-config-as-results',
            config2_expected_step_results,
            test_dir
        )

def test_merge_results_from_two_sub_steps():
    config = {
        'tssc-config': {
            'write-config-as-results': [
                {
                    'implementer': 'WriteConfigAsResultsStepImplementer',
                    'config': {
                        'config-1': "config-1",
                        'config-overwrite-me': 'config-1'
                    }
                },
                {
                'implementer': 'WriteConfigAsResultsStepImplementer',
                'config': {
                    'config-2': 'config-2',
                    'config-overwrite-me': 'config-2'
                    }
                }
            ]
        }
    }
    config_expected_step_results = {
        'tssc-results': {
            'write-config-as-results': {
                'config-1': "config-1",
                'config-2': 'config-2',
                'config-overwrite-me': 'config-2'
            }
        }
    }

    TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)

    with TempDirectory() as test_dir:
        _run_step_implementer_test(
            config,
            'write-config-as-results',
            config_expected_step_results,
            test_dir
        )

def test_one_step_existing_results_file_bad_yaml():
    config = {
        'tssc-config': {
            'write-config-as-results': {
                'implementer': 'WriteConfigAsResultsStepImplementer',
                'config': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1'
                }
            }
        }
    }

    TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
    with TempDirectory() as test_dir:
        results_dir_path = os.path.join(test_dir.path, 'tssc-results')
        results_file_path = os.path.join(results_dir_path, 'tssc-results.yml')
        test_dir.write(results_file_path,b'''{}bad[yaml}''')

        with pytest.raises(TSSCException):
            _run_step_implementer_test(
                config,
                'write-config-as-results',
                None,
                test_dir
            )

def test_one_step_existing_results_file_missing_key():
    config = {
        'tssc-config': {
            'write-config-as-results': {
                'implementer': 'WriteConfigAsResultsStepImplementer',
                'config': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1'
                }
            }
        }
    }

    TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
    with TempDirectory() as test_dir:
        results_dir_path = os.path.join(test_dir.path, 'tssc-results')
        results_file_path = os.path.join(results_dir_path, 'tssc-results.yml')
        test_dir.write(results_file_path,b'''not-expected-root-key-for-results: {}''')

        with pytest.raises(TSSCException):
            _run_step_implementer_test(
                config,
                'write-config-as-results',
                None,
                test_dir
            )

def test_one_step_existing_results_file_empty():
    config = {
        'tssc-config': {
            'write-config-as-results': {
                'implementer': 'WriteConfigAsResultsStepImplementer',
                'config': {
                    'config-1': "config-1",
                    'config-overwrite-me': 'config-1'
                }
            }
        }
    }

    config_expected_step_results = {
        'tssc-results': {
            'write-config-as-results': {
                'config-1': "config-1",
                'config-overwrite-me': 'config-1'
            },
        }
    }

    TSSCFactory.register_step_implementer(WriteConfigAsResultsStepImplementer)
    with TempDirectory() as test_dir:
        results_dir_path = os.path.join(test_dir.path, 'tssc-results')
        results_file_path = os.path.join(results_dir_path, 'tssc-results.yml')
        test_dir.write(results_file_path,b'''''')
        _run_step_implementer_test(
            config,
            'write-config-as-results',
            config_expected_step_results,
            test_dir
        )
