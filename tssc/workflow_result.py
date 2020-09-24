"""
Abstract class and helper constants for WorkflowResult
"""
import os
import pickle

from tssc.step_result import StepResult
from tssc.exceptions import TSSCException


class WorkflowFile:
    """
    :return:
    """

    def __init__(self, pickle_filename):
        self.__pickle_filename = pickle_filename

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
        # load into memory
        if os.path.exists(self.__pickle_filename):
            with open(self.__pickle_filename, 'rb') as file:
                return pickle.load(file)
        return None


class WorkflowResult:
    """
    :return:
    """

    def __init__(self):
        self._workflow_list = []

    def clear(self):
        """
        :return:
        """
        self._workflow_list = []

    def add_step_result(self, data):
        """
        :return:
        """
        if isinstance(data, list):
            for i in data:
                if isinstance(data, list):
                    self._workflow_list.append(i)
        elif isinstance(data, StepResult):
            self._workflow_list.append(data)
        else:
            raise TSSCException('can only add StepResult(s)')

    def get_step_artifacts(self, step_name):
        """
        get result step as a dictionary
        :return:
        """
        step = None
        for step_result in self._workflow_list:
            if step_result.get_step_name() == step_name:
                step = step_result.get_artifacts()
                break
        return step

    def get_step_result(self, step_name):
        """
        get result step as a dictionary
        :return:
        """
        step = None
        for step_result in self._workflow_list:
            if step_result.get_step_name() == step_name:
                step = step_result.get_step_result()
                break
        return step

    def print_json(self):
        """
        :return:
        """
        for i in self._workflow_list:
            print(i.get_json())

    def print_yml(self):
        """
        :return:
        """
        for i in self._workflow_list:
            print(i.get_yaml())
