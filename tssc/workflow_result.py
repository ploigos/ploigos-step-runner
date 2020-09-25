"""
Abstract class and helper constants for WorkflowResult
"""
import pickle
import os
import json

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

    def dump_pickle(self, pickle_filename):
        """
        :return:
        """
        try:
            WorkflowResult._folder_create(pickle_filename)
            with open(pickle_filename, 'wb') as file:
                pickle.dump(self, file)
        except Exception as error:
            raise RuntimeError(f'error dumping {pickle_filename}: {error}') from error
    
    def dump_yml(self, yml_filename):
        """
        :return:
        """
        try:
            WorkflowResult._folder_create(yml_filename)
            with open(yml_filename, 'w') as file:
                for i in self.__workflow_list:
                    file.write(i.get_step_result_yaml())
        except Exception as error:
            raise RuntimeError(f'error dumping {yml_filename}: {error}') from error

    def dump_json(self, json_filename):
        """
        :return:
        """
        try:
            WorkflowResult._folder_create(json_filename)
            with open(json_filename, 'w') as file:
                for i in self.__workflow_list:
                    file.write(i.get_step_result_json())
        except Exception as error:
            raise RuntimeError(f'error dumping {json_filename}: {error}') from error

    @staticmethod
    def load(pickle_filename):
        """
        :return: Workflow_result object
        """
        try:
            WorkflowResult._folder_create(pickle_filename)

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
    
    @staticmethod
    def _folder_create(filename):
        """
        :param filename:
        :return:
        """
        path = os.path.dirname(filename)
        if path and not os.path.exists(path):
            os.makedirs(os.path.dirname(filename))
    
    @staticmethod
    def delete(filename):
        """
        Currently used for testing - makes an empty file
        """
        try:
            WorkflowResult._folder_create(filename)
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as error:
            raise RuntimeError(f'error deleting {filename}: {error}') from error
