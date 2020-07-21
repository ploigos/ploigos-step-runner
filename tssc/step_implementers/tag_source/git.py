"""
Step Implementer for the tag-source step for Git.
"""
import sys
import sh
import os
from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {}

class Git(StepImplementer):
    """
    StepImplementer for the tag-source step for Git.
    """

    def __init__(self, config, results_dir, results_file_name):
        super().__init__(config, results_dir, results_file_name, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.TAG_SOURCE

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """

    def _run_step(self, runtime_step_config):
        username = None
        password = None
        tag = 'latest'
        if(runtime_step_config.get('username_env_var') \
          and runtime_step_config.get('password_env_var')):
            username = os.getenv(runtime_step_config.get('username_env_var'))
            password = os.getenv(runtime_step_config.get('password_env_var'))
        else:
            print('No username/password found, assuming ssh')
        if(self.get_step_results('generate-metadata') \
          and self.get_step_results('generate-metadata').get('image-tag')):
            tag = self.get_step_results('generate-metadata').get('image-tag')
        else:
            print('No version found in metadata. Using latest')
        self._git_tag(tag)
        git_url = self._git_url(runtime_step_config)
        self._git_push(git_url, username, password)
        results = {
            'git_tag' : tag
        }
        return results

    def _git_url(self, runtime_step_config):
        returnVal = None
        if(runtime_step_config.get('git_url')):
            returnVal = runtime_step_config.get('git_url')
        else:
            git_config = sh.git.bake("config")
            try:
                returnVal = git_config(
                    '--get',
                    'remote.origin.url',
                    _out=sys.stdout)
            except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
                raise RuntimeError('Error invoking git config --get remote.origin.url')
        return returnVal

    def _git_tag(self, git_tag_value):
        git_tag = sh.git.bake("tag")
        try:
            git_tag(git_tag_value)
        except:
            raise RuntimeError('Error invoking git tag ' + git_tag_value)

    def _git_push(self, url, username=None, password=None):
        git_push = sh.git.bake("push")
        try:
            if(username and password):
                git_push(
                    'http://' + username + ':' + password + git_url,
                    '--tag')
            else:
                git_push('--tag')
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking git push')

# register step implementer
TSSCFactory.register_step_implementer(Git, True)
