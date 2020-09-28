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
    implementer_name : str
        Name of the implementer

    """

    def __init__(self, step_name, sub_step_name, implementer_name):
        """
        Result
        """
        self._step_name = step_name
        self._implementer_name = implementer_name
        self._success = True
        self._message = ''
        self._artifacts = {}
        self._sub_step_name = sub_step_name

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
        return self._step_name

    @property
    def sub_step_name(self):
        """
        Returns
        -------
        str
            Sub Step name
        """
        return self._sub_step_name

    @property
    def implementer_name(self):
        """
        Returns
        -------
        str
            Step implementer name
        """
        return self._implementer_name

    @property
    def artifacts(self):
        """
        Returns
        -------
        dict
            All artifacts of the step
        """
        return self._artifacts

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
        return self._artifacts.get(name)

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
        if name is None:
            raise TSSCException('name is required')

        if value is None:
            raise TSSCException('value is required')

        if not value_type:
            value_type = type(value).__name__

        self._artifacts[name] = {
            'description': description,
            'type': value_type,
            'value': value
        }

    # todo: needs tests
    def merge_artifacts(self, new_artifacts):
        """
        Merges an artifacts dictionary into the artifacts dictionary
        eg:
        {
          'a': {'description': '', 'type': 'str', 'value': 'A'},
          'x': {'description': '', 'type': 'str', 'value': 'X'}
        }
        Parameters
        ----------
        new_artifacts: dict
           New set of artifacts to merge in
        """
        self.artifacts.update(new_artifacts)

    @property
    def success(self):
        """
        Returns
        -------
        bool
            Success
        """
        return self._success

    @success.setter
    def success(self, success=True):
        """
        Setter for success
        """
        self._success = success

    @property
    def message(self):
        """
        Returns
        -------
        str
            Message/ error message
        """
        return self._message

    @message.setter
    def message(self, message):
        """
        Setter for message
        """
        self._message = message

    def get_step_result(self):
        """
        result= {
            "new_step": {
                "step-name": "new_step",
                "step-implementer-name": "implementer_name",
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

        Returns
        -------
        dict
            Formatted with all step result components

        """
        result = {
            self._step_name: {
                'step-name': self._step_name,
                'step-implementer-name': self._implementer_name,
                'sub-step-name': self._sub_step_name,
                'success': self._success,
                'message': self._message,
                'artifacts': self._artifacts
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
