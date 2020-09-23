"""
Abstract class and helper constants for StepResults
"""
import pickle

from tssc.step_results import StepResults


class StepResultsList:
    """
    hello
    :return:
    """

    def __init__(self, pickle_filename, ):
        self._pickle_filename = pickle_filename
        self._the_list = []

    def list_load(self):
        """
        hello
        :return:
        """
        # example of loading array of objs
        # load the list into memory
        with open(self._pickle_filename, 'rb') as file:
            self._the_list = pickle.load(file)

    def list_dump(self):
        """
        hello
        :return:
        """
        # example of dumping array of objs
        # overwrite the file with the list in memory!
        # you will update the list in memory with append
        with open(self._pickle_filename, 'wb') as file:
            pickle.dump(self._the_list, file)

    def list_append(self, data):
        """
        hello
        :return:
        """
        if isinstance(data, list):
            for i in data:
                self._the_list.append(i)
        elif isinstance(data, StepResults):
            self._the_list.append(data)
        else:
            print('you loose')

    def list_json(self):
        """
        hello
        :return:
        """
        # example of json ...
        self.list_load()
        for i in self._the_list:
            print(i.get_json())

    def list_yml(self):
        """
        hello
        :return:
        """
        # example of yml ...
        self.list_load()
        for i in self._the_list:
            print(i.get_yaml())

    def get_result_step(self, step_name):
        """
        hello
        :return:
        """
        step = None
        for i in self._the_list:
            if i.get_step_name() == step_name:
                step = i
                break
        return step
