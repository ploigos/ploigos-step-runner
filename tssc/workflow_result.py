"""
Abstract class and helper constants for WorkflowResult
"""
import pickle
import os
import json
import yaml

from tssc.step_result import StepResult
from tssc.exceptions import TSSCException


class WorkflowResult:
    """
    Class to manage a list of step_results
    The Workflow represents the current results to this point in time
    """

    def __init__(self):
        self.__workflow_list = []

    def clear(self):
        """
        clears the workflow list of step_results
        """
        self.__workflow_list = []

    def add_step_result(self, step_result):
        """
        Add a single step_result to the workflow list

        Parameters
        ----------
        step_result : StepResult
           An StepResult object

        Raises
        ------
        Raises a TSSCException if an instance other than
        StepResult is passed as a parameter
        """
        if isinstance(step_result, StepResult):
            match = False
            for i, old in enumerate(self.__workflow_list):
                if old.step_name == step_result.step_name:
                    if old.implementer_name == step_result.implementer_name:
                        match = True
                        # grab old artifacts to merge into the new
                        step_result.merge_artifacts(old.artifacts)
                        #delete the old
                        del self.__workflow_list[i]
                        #add the new
                        self.__workflow_list.append(step_result)
            if not match:
                self.__workflow_list.append(step_result)
        else:
            raise TSSCException('expect StepResult instance type')

    def get_step_artifacts(self, step_name):
        """
        Lookup artifacts by step_name

        Parameters
        ----------
        step_name : str
             Name of step to search

        Returns
        -------
        dict
            if found, return the artifacts dict
            else return None
        """
        step_artifacts = None
        for step_result in self.__workflow_list:
            if step_result.step_name == step_name:
                step_artifacts = step_result.artifacts
                break
        return step_artifacts

    def search_for_artifact(self, search_artifact, verbose=False):
        """
        Search for an artifact in ANY step.
        The FIRST match is returned

        eg: search for 'version", the dictionary is returned:

        {'description': 'semantic version', 'type': 'str', 'value': 'v0.10.0+23'}

        eg: of search for 'version' with verbose=True:
        'step1': {
                'step-implementer-name': 'one',
                'step-name': 'step1',
                'artifacts': {
                    'a': {
                        'description': '',
                        'type': 'str',
                        'value': 'A'
                    },
                    'version': {
                        'description': 'semantic version',
                        'type': 'str',
                        'value': 'v0.10.0+23'
                    }
                },
                'message': '',
                'success': True
            }

        Parameters
        ----------
        search_artifact : str
             Name of artifact to search
        verbose : boolean
             Return the entire step_result

        Returns
        -------
        dict
            if not found return Non
            elif verbose, return the result-set dict
            elif return the artifact dict
        """
        result = None
        for step_result in self.__workflow_list:
            if step_result.get_artifact(search_artifact):
                if verbose:
                    result = step_result.get_step_result()
                else:
                    result = step_result.get_artifact(search_artifact)
                break
        return result

    def get_tssc_step_result(self, step_name):
        """
        Search for a step by name for a dict, eg:
        'tssc-results': {
            'step1': {
                'step-name': 'step1',
                'step-implementer-name': 'one',
                'success': True,
                'message': '',
                'artifacts': {
                    'a': {
                        'description': 'aA',
                        'type': 'str',
                        'value': 'A'
                    },
                    'b': {
                        'description': 'bB',
                        'type': 'file',
                        'value': 'B'
                    },
                    'z': {
                        'description': '',
                        'type': 'str',
                        'value': 'Z'
                    }
                }
            }
        }

        Parameters
        ----------
        step_name : str
             Name of step to search

        Returns
        -------
        dict
             StepResult dictionary
        """
        tssc_step_result = None
        for step_result in self.__workflow_list:
            if step_result.step_name == step_name:
                step_result = step_result.get_step_result()
                tssc_step_result = {
                    'tssc-results': step_result
                }
                break
        return tssc_step_result

    def print_json(self):
        """
        Print the list in json format
        """
        for i in self.__workflow_list:
            print(i.get_step_result_json())

    def print_yml(self):
        """
        Print the list in yml format
        """
        for i in self.__workflow_list:
            print(i.get_step_result_yaml())

    def write_to_pickle_file(self, pickle_filename):
        """
        Write the workflow list in a pickle format to file

        Parameters
        ----------
        pickle_filename : str
             Name of file to write (eg: tssc-results.pkl)

        Raises
        ------
        Raises a RuntimeError if the file cannot be dumped
        """
        try:
            WorkflowResult._folder_create(pickle_filename)
            with open(pickle_filename, 'wb') as file:
                pickle.dump(self, file)
        except Exception as error:
            raise RuntimeError(f'error dumping {pickle_filename}: {error}') from error

    def write_tssc_results_to_yml_file(self, yml_filename):
        """
        Write the workflow list in a yaml format to file
        Specifically using 'tssc-results'

        Parameters
        ----------
        yml_filename : str
             Name of file to write (eg: tssc-results.yml)

        Raises
        ------
        Raises a RuntimeError if the file cannot be dumped
        """
        try:
            WorkflowResult._folder_create(yml_filename)
            with open(yml_filename, 'w') as file:
                tssc_results = self.get_all_tssc_step_result()
                yaml.dump(tssc_results, file, indent=4)
        except Exception as error:
            raise RuntimeError(f'error dumping {yml_filename}: {error}') from error

    def write_tssc_results_to_json_file(self, json_filename):
        """
        Write the workflow list in a json format to file
        Specifically using 'tssc-results'.

        Parameters
        ----------
        json_filename : str
             Name of file to write (eg: tssc-results.json)

        Raises
        ------
        Raises a RuntimeError if the file cannot be dumped
        """
        try:
            WorkflowResult._folder_create(json_filename)
            with open(json_filename, 'w') as file:
                tssc_results = self.get_all_tssc_step_result()
                json.dump(tssc_results, file, indent=4)
        except Exception as error:
            raise RuntimeError(f'error dumping {json_filename}: {error}') from error

    def get_all_tssc_step_result(self):
        """
        Return a dictionary named tssc-results of all the step results in memory
        Specifically using 'tssc-results'.

        Returns
        -------
        results: dict
            results of all steps from list
        """
        result = {}
        for i in self.__workflow_list:
            result.update(i.get_step_result())
        tssc_results = {
            'tssc-results': result
        }
        return tssc_results

    @staticmethod
    def load_from_file(pickle_filename):
        """
        Load a pickled file into the Workflow list

        Parameters
        ----------
        pickle_filename: str
           Name of the file to load

        Raises
        ------
        Raises a TSSCException if the file cannot be loaded
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
            raise TSSCException(f'error loading {pickle_filename}: {error}') from error

    @staticmethod
    def _folder_create(filename):
        """
        Helper method to create folder if ncessary

        Parameters
        ----------
        filename: str
            Absolute name of a file.ext
        """
        path = os.path.dirname(filename)
        if path and not os.path.exists(path):
            os.makedirs(os.path.dirname(filename))

    @staticmethod
    def delete_file(filename):
        """
        Used for testing to delete a file

        Parameters
        ----------
        filename: str
            name of file
        """
        try:
            WorkflowResult._folder_create(filename)
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as error:
            raise RuntimeError(f'error deleting {filename}: {error}') from error
