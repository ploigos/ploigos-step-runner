"""
Abstract class and helper constants for WorkflowResult
"""
import pickle
import os

from tssc.step_result import StepResult
from tssc.exceptions import TSSCException


class Wrapper:
    """
    todo: not sure if this wrapper (inner/outer) is a bad idea yet...
    """
    def __init__(self, pickle_filename):

        self.__workflow_file = WorkflowFile(pickle_filename)
        self.__results = self.__workflow_file.load()
        if self.__results is None:
            self.__results = WorkflowResult()

    @property
    def results(self):
        """
        getter
        """
        return self.__results

    def write(self, step_result):
        """
        dump to pickle
        """
        self.__results.add_step_result(step_result)
        self.__workflow_file.dump(self.__results)

    def read(self):
        """
        read from pickle
        """
        return self.__workflow_file.load()


class WorkflowFile:
    """
    :return:
    """

    def __init__(self, pickle_filename):
        """
        create the file if it does not exist
        """
        self.__pickle_filename = pickle_filename
        self._file_check(self.__pickle_filename)

    def clear(self):
        """
        :return:
        """
        with open(self.__pickle_filename, 'wb') as file:
            pickle.dump(None, file)

    def dump(self, pickle_object):
        """
        :return:
        """
        with open(self.__pickle_filename, 'wb') as file:
            pickle.dump(pickle_object, file)

    def load(self):
        """
        :return:
        """
        with open(self.__pickle_filename, 'rb') as file:
            return pickle.load(file)

    def _file_check(self, filename):
        path = os.path.dirname(filename)
        if path and not os.path.exists(path):
            os.makedirs(os.path.dirname(filename))
        if not os.path.exists(filename):
            self.clear()


class WorkflowResult:
    """
    :return:
    """

    def __init__(self):
        self.__workflow_list = []

    def clear(self):
        """
        :return:
        """
        self.__workflow_list = []

    def add_step_result(self, step_result):
        """
        :return:
        """
        if isinstance(step_result, StepResult):
            self.__workflow_list.append(step_result)
        else:
            raise TSSCException('can only add StepResult')

    def get_step_artifacts(self, step_name):
        """
        look for the step_name in the list and return
        :return:
        """
        step_artifacts = None
        for step_result in self.__workflow_list:
            if step_result.step_name == step_name:
                step_artifacts = step_result.artifacts
                break
        return step_artifacts

    def get_step_result(self, step_name):
        """
        get result step as a dictionary
        :return:
        """
        step_result = None
        for step_result in self.__workflow_list:
            if step_result.step_name == step_name:
                step_result = step_result.get_step_result()
                break
        return step_result

    def print_json(self):
        """
        :return:
        """
        for i in self.__workflow_list:
            print(i.get_step_result_json())

    def print_yml(self):
        """
        :return:
        """
        for i in self.__workflow_list:
            print(i.get_step_result_yaml())
