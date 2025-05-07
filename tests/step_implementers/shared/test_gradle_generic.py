import os
from pathlib import Path
from shutil import copyfile
from unittest.mock import PropertyMock, patch

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import WorkflowResult
from ploigos_step_runner.config import Config
from ploigos_step_runner.step_implementers.shared.gradle_generic import \
    GradleGeneric
from ploigos_step_runner.utils.file import create_parent_dir
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase

class BaseTestStepImplementerSharedGradleGeneric(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={'build-file': 'build.gradle'},
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=GradleGeneric,
            step_config=step_config,
            step_name='foo',
            implementer='GradleGeneric',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
       )

class TestStepImplementerSharedGradleGeneric__run_step(
    BaseTestStepImplementerSharedGradleGeneric
):
    def test_success(self):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            os.mkdir(parent_work_dir_path)
            os.mkdir(os.path.join(parent_work_dir_path, 'app'))

            build_file = 'app/build.gradle'

            with open(os.path.join(parent_work_dir_path, build_file), 'w') as outf:
                outf.write('version "1.0"\n')
                outf.close()

            step_config = {'build-file': os.path.join(parent_work_dir_path, 'app/build.gradle'), 'gradle-tasks': ['build']}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path
            )

            required_keys = step_implementer._required_config_or_result_keys()

            # run step
            actual_step_result = step_implementer._run_step()

            step_name = 'foo'

            # create expected step result
            expected_step_result = StepResult(
                step_name=step_name,
                sub_step_name='GradleGeneric',
                sub_step_implementer_name='GradleGeneric'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from gradle.",
                name='gradle-output',
                value=os.path.join(parent_work_dir_path, step_name + '/gradle_output.txt') 
            )

            expected_step_result.success = True

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

    def test_fail(self):
        with TempDirectory() as test_dir:

            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            os.mkdir(parent_work_dir_path)

            step_config = {'build-file': 'unknown.gradle', 'gradle-tasks': ['build']}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            actual_step_result = step_implementer._run_step()

            if len(actual_step_result.message) > 0:
                actual_step_result.message = actual_step_result.message.split('\n')[0]
            
            step_name='foo'
            
            # create expected step result
            expected_step_result = StepResult(
                step_name=step_name,
                sub_step_name='GradleGeneric',
                sub_step_implementer_name='GradleGeneric'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from gradle.",
                name='gradle-output',
                value=os.path.join(parent_work_dir_path, step_name + '/gradle_output.txt')
            )
            
            expected_step_result.message = "Error running gradle. " \
                "More details maybe found in 'gradle-output' report artifact: "\
                "Error running gradle. "
            expected_step_result.success = False

            # verify step result
            self.assertEqual(
                actual_step_result,
                expected_step_result
            )

    def test_gradletasks(self):
        with TempDirectory() as test_dir:

            parent_work_dir_path = os.path.join(test_dir.path, 'working')

            os.mkdir(parent_work_dir_path)
            os.mkdir(os.path.join(parent_work_dir_path, 'app'))
            
            build_file = 'app/build.gradle'
            
            with open(os.path.join(parent_work_dir_path, build_file), 'w') as outf:
                outf.write('version "1.0"\n')
                outf.close()            
            
            step_config = {'build-file': 'app/build.gradle', 'gradle-tasks': ['build']}

            # gradle_generic = GradleGeneric(config=step_config, workflow_result=None, parent_work_dir_path=parent_work_dir_path)

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path
            )
            
            print(step_implementer.gradle_tasks)            
            

# @patch.object(GradleGeneric, '_run_gradle_step')
class TestStepImplementerSharedGradleGeneric__run_additional(
    BaseTestStepImplementerSharedGradleGeneric
):

    def test_additional(self):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            
            os.mkdir(parent_work_dir_path)
            os.mkdir(os.path.join(parent_work_dir_path, 'app'))

            build_file = 'app/build.gradle'
            
            with open(os.path.join(parent_work_dir_path, build_file), 'w') as outf:
                outf.write('version "1.0"\n')
                outf.close()
                
            step_config = {'build-file': os.path.join(parent_work_dir_path, 'app/build.gradle'), 'gradle-tasks': ['build']}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path
            )

            actual_gradle_result = step_implementer._run_gradle_step(gradle_output_file_path='gradle_output.txt', step_implementer_additional_arguments=['--full-stacktrace'])

            expected_gradle_result = None
            
            self.assertEqual(
                actual_gradle_result,
                expected_gradle_result
            )

    def test_additional_RaiseError(self):
        with TempDirectory() as test_dir:
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            
            os.mkdir(parent_work_dir_path)
            os.mkdir(os.path.join(parent_work_dir_path, 'app'))

            build_file = 'app/build.gradle'
            
            with open(os.path.join(parent_work_dir_path, build_file), 'w') as outf:
                outf.write('version "1.0"\n')
                outf.close()
                
            step_config = {'build-file': os.path.join(parent_work_dir_path, 'app/build.gradle'), 'gradle-tasks': ['build']}
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path
            )

            try:
                actual_gradle_result = step_implementer._run_gradle_step(gradle_output_file_path='gradle_output.txt', step_implementer_additional_arguments=['--invalid-option'])
            except StepRunnerException as sre:
                return None

