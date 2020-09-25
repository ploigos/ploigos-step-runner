"""
Abstract class and helper constants for WorkflowResult
"""
import pickle
import os

from tssc.step_result import StepResult
from tssc.exceptions import TSSCException


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
            raise TSSCException('expect StepResult instance type')

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

    def get_artifact(self, search_artifact):
        artifact = None
        for step_result in self.__workflow_list:
            artifact = step_result.get_artifact(search_artifact)
            if artifact:
                break
        return artifact

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

    def dump(self, pickle_filename):
        """
        :return:
        """
        try:
            _folder_create(pickle_filename)
            with open(pickle_filename, 'wb') as file:
                pickle.dump(self, file)
        except Exception as error:
            raise RuntimeError(f'error dumping {pickle_filename}: {error}') from error


#######
# helper methods
#######

def _folder_create(pickle_filename):
    """
    :param filename:
    :return:
    """
    path = os.path.dirname(pickle_filename)
    if path and not os.path.exists(path):
        os.makedirs(os.path.dirname(pickle_filename))


def load_workflow_results(pickle_filename):
    """
    :return: Workflow_result object
    """
    try:
        _folder_create(pickle_filename)

        # if the file does not exist return empty object
        if not os.path.isfile(pickle_filename):
            return WorkflowResult()

        # if the file is empty return empty object
        if os.path.getsize(pickle_filename) == 0:
            return WorkflowResult()

        # check that the file has Workflow object
        with open(pickle_filename, 'rb') as file:
            workflow_result = pickle.load(file)
            if not isinstance(workflow_result, WorkflowResult):
                raise RuntimeError(f'error {pickle_filename} has invalid data')
            return workflow_result

    except Exception as error:
        raise RuntimeError(f'error loading {pickle_filename}: {error}') from error


def delete_workflow_results(pickle_filename):
    """
    Currently used for testing - makes an empty file
    """
    try:
        _folder_create(pickle_filename)
        if os.path.exists(pickle_filename):
            os.remove(pickle_filename)
    except Exception as error:
        raise RuntimeError(f'error deleting {pickle_filename}: {error}') from error
