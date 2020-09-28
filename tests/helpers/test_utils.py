import io
import os
import re

def create_git_commit_with_sample_file(temp_dir, git_repo, sample_file_name = 'sample-file', commit_message = 'test'):
    sample_file = os.path.join(temp_dir.path, sample_file_name)
    open(sample_file, 'wb').close()
    git_repo.index.add([sample_file])
    git_repo.index.commit(commit_message)

def Any(cls):
    """
    Source
    ------
    https://stackoverflow.com/questions/21611559/assert-that-a-method-was-called-with-one-argument-out-of-several
    """
    class Any(cls):
        def __eq__(self, other):
            return True
        def __hash__(self):
            return hash(tuple(self))
    return Any()

class StringRegexParam():
    def __init__(self, regex):
        self.__regex = regex

    def __eq__(self, other):
        if isinstance(other, str):
            return re.match(self.__regex, other)
        else:
            return False

def create_sops_side_effect(mock_stdout):
    def sops_side_effect(*args, **kwargs):
        kwargs['_out'].write(mock_stdout)

    return sops_side_effect
