"""
Step Implementer for the package step for Maven.
"""
import os
import subprocess

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {
    'pom-file': 'pom.xml'
}

# https://stackoverflow.com/questions/21377520/do-a-maven-build-in-a-python-script
class ChangeDir:
    """
    Internal helper class to manage changing directories, and returning to the
    starting working directory.
    """
    def __init__(self, new_path):
        self.saved_path = None
        self.new_path = os.path.expanduser(new_path)

    # Change directory with the new path
    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    # Return back to previous directory
    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)

class Maven(StepImplementer):
    """
    StepImplementer for the package step for Maven.

    Raises
    ------
    ValueError
        If given pom file does not exist
        If given pom file does not contain required elements
    """

    def __init__(self, config, results_file):
        super().__init__(config, results_file, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.PACKAGE

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """
        print(step_config)

        if 'pom-file' not in step_config or not step_config['pom-file']:
            raise ValueError('Key (pom-file) must have none empty value in the step configuration')

    def _run_step(self, runtime_step_config):
        pom_file = runtime_step_config['pom-file']

        if not os.path.exists(pom_file):
            raise ValueError('Given pom file does not exist: ' + pom_file)

        process_args = ["mvn", "clean", "install"]
        java_artifact_extenstions = ["jar", "war", "ear"]
        return_code = 1

        with ChangeDir(os.path.dirname(pom_file)):
            return_code = subprocess.call(process_args)
        if return_code:
            raise ValueError('Issue invoking ' + str(process_args) + \
              ' with given pom file (' + pom_file + ')')

        java_packaged_artifacts = []
        for filename in os.listdir(os.path.join(os.path.dirname(pom_file), "target")):
            if any(filename.endswith(ext) for ext in java_artifact_extenstions):
                java_packaged_artifacts.append(filename)

        results = {
            'artifacts' : {
            }
        }
        for artifact in java_packaged_artifacts:
            results['artifacts'][artifact] = \
              os.path.join(os.path.dirname(pom_file), "target", artifact)

        return results

# register step implementer
TSSCFactory.register_step_implementer(Maven)
