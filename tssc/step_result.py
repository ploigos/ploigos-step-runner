"""
Class and helper constants for StepResult
"""
import json
import yaml


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

    def __init__(self, step_name, implementer_name):
        """
        Result
        """
        self._step_name = step_name
        self._implementer_name = implementer_name
        self._success = True
        self._message = ''
        self._artifacts = {}

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
        Returns
        -------
        dict
            Specific artifact given name
        """
        return self._artifacts.get(name)

    def add_artifact(self, name, value, description='', value_type=None):
        """
        Adds an artifact with the given parameters
        """
        if not value_type:
            value_type = type(value).__name__
        self._artifacts[name] = {
            'description': description,
            'type': value_type,
            'value': value
        }

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
        Returns
        -------
        dict
            Formatted with all step result components

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

        """
        result = {
            self._step_name: {
                'step-name': self._step_name,
                'step-implementer-name': self._implementer_name,
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
