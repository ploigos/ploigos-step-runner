"""
Class and helper constants for StepResult
"""
import json
import yaml
from tssc.exceptions import TSSCException


class StepResult:
    """
    TSSC step result dictionary.

    Parameters
    ----------
    step_name : str
        Name of the step
    sub_step_name : str
        Name of the sub step
    sub_step_implementer_name : str
        Name of the sub step implementer

    """

    def __init__(self, step_name, sub_step_name, sub_step_implementer_name):
        """
        Step Result Init
        """
        self.__step_name = step_name
        self.__sub_step_name = sub_step_name
        self.__sub_step_implementer_name = sub_step_implementer_name
        self.__success = True
        self.__message = ''
        self.__artifacts = {}

    def __str__(self):
        """
        Returns
        -------
        str
            JSON formatted step result
        """
        return self.get_step_result_json()

    @property
    def step_name(self):
        """
        Returns
        -------
        str
            Step name
        """
        return self.__step_name

    @property
    def sub_step_name(self):
        """
        Returns
        -------
        str
            Step name
        """
        return self.__sub_step_name

    @property
    def sub_step_implementer_name(self):
        """
        Returns
        -------
        str
            Step implementer name
        """
        return self.__sub_step_implementer_name

    @property
    def artifacts(self):
        """
        Returns
        -------
        dict
            All artifacts of the step
        """
        return self.__artifacts

    def get_artifact(self, name):
        """
        Parameters
        ----------
        name : str
            The name of the artifact to return

        Returns
        -------
        dict
            Specific artifact given name
        """
        return self.artifacts.get(name)

    def add_artifact(self, name, value, description='', value_type=None):
        """
        Insert/Update an artifact with the given pattern:
            "name": {
                "description": "file description",
                "type": "file",
                "value": "file://step-result.txt"
            }

        Parameters
        ----------
        name : str
            Required name of the artifact
        value : str
            Required content
        description : str, optional
            Optional description (defaults to empty)
        value_type : str, optional
            Optional type of the value (defaults to str)

        """
        if not name:
            raise TSSCException('Name is required to add artifact')

        # False can be the value
        if value == '' or value is None:
            raise TSSCException('Value is required to add artifact')

        if not value_type:
            value_type = type(value).__name__

        self.__artifacts[name] = {
            'description': description,
            'type': value_type,
            'value': value
        }

    def merge_artifact(self, new_artifact):
        """
        Merges an artifacts dictionary into the artifacts dictionary

        Parameters
        ----------
        new_artifact: dict
           New set of artifacts to merge in
          eg:
          { 'a': {'description': '', 'type': 'str', 'value': 'A'} }
        """
        self.artifacts.update(new_artifact)

    @property
    def success(self):
        """
        Returns
        -------
        bool
            Success
        """
        return self.__success

    @success.setter
    def success(self, success=True):
        """
        Setter for success
        """
        self.__success = success

    @property
    def message(self):
        """
        Returns
        -------
        str
            Message/ error message
        """
        return self.__message

    @message.setter
    def message(self, message):
        """
        Setter for message
        """
        self.__message = message

    def get_sub_step_result(self):
        result = {
            'sub-step-implementer-name': self.sub_step_implementer_name,
            'success': self.success,
            'message': self.message,
            'artifacts': self.artifacts
        }
        return result

    def get_step_result(self):
        """
        result= {
            "step-name: {
                "sub-step-name": {
                    "sub-step-implementer-name": "sub_step_implementer_name",
                    "success": True,
                    "message": "",
                    "artifacts": {
                        "name": {
                            "description": "file description",
                            "type": "file",
                            "value": "file://step-result.txt"
                        }
                    }
                }
            }
        }

        Returns
        -------
        dict
            Formatted with all step result components

        """
        result = {
            self.step_name: {
                self.sub_step_name: self.get_sub_step_result()
            }
        }
        return result

    def get_step_result_json(self):
        """
        Returns
        -------
        str
            JSON formatted step result
        """
        return json.dumps(self.get_step_result())

    def get_step_result_yaml(self):
        """
        Returns
        -------
        str
            YAML formatted step result
        """
        return yaml.dump(self.get_step_result())
