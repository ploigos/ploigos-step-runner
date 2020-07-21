"""
Step Implementer for the tag-source step for Git.
"""
import sys
import sh
from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {}

OPTIONAL_ARGS = {
    'username': None,
    'password': None
}

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
        print(step_config)

    def _run_step(self, runtime_step_config):
        username = None
        password = None
        if not all(element in runtime_step_config for element in OPTIONAL_ARGS) \
          and any(element in runtime_step_config for element in OPTIONAL_ARGS):
            raise ValueError('Either username or password is not set. Neither ' \
              'or both must be set.')
        tag = 'latest'
        if any(element in runtime_step_config for element in OPTIONAL_ARGS):
            if(runtime_step_config.get('username') \
              and runtime_step_config.get('password')):
                username = runtime_step_config.get('username')
                password = runtime_step_config.get('password')
            else:
                raise ValueError('Both username and password must have ' \
                  'non-empty value in the runtime step configuration')
        else:
            print('No username/password found, assuming ssh')
        if(self.get_step_results('generate-metadata') \
          and self.get_step_results('generate-metadata').get('image-tag')):
            tag = self.get_step_results('generate-metadata').get('image-tag')
        else:
            print('No version found in metadata. Using latest')
        self._git_tag(tag)
        git_url = self._git_url(runtime_step_config)
        protocol = None
        if git_url.startswith('http://'):
            protocol = 'http://'
            git_url = git_url[7:]
        elif git_url.startswith('https://'):
            protocol = 'https://'
            git_url = git_url[8:]
        self._git_push(protocol, git_url, username, password)
        results = {
            'git_tag' : tag
        }
        return results

    @staticmethod
    def _git_url(runtime_step_config):
        return_val = None
        if runtime_step_config.get('git_url'):
            return_val = runtime_step_config.get('git_url')
        else:
            git_config = sh.git.bake("config")
            try:
                return_val = git_config(
                    '--get',
                    'remote.origin.url',
                    _out=sys.stdout)
            except sh.ErrorReturnCode:  # pylint: disable=undefined-variable # pragma: no cover
                raise RuntimeError('Error invoking git config --get remote.origin.url')
        return return_val

    @staticmethod
    def _git_tag(git_tag_value): # pragma: no cover
        git_tag = sh.git.bake("tag")
        try:
            git_tag(git_tag_value)
        except:
            raise RuntimeError('Error invoking git tag ' + git_tag_value)

    @staticmethod
    def _git_push(protocol, url, username=None, password=None): # pragma: no cover
        git_push = sh.git.bake("push")
        try:
            if(username and password):
                git_push(
                    protocol + username + ':' + password + url,
                    '--tag')
            else:
                git_push('--tag')
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking git push')

# register step implementer
TSSCFactory.register_step_implementer(Git, True)
