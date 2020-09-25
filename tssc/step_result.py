"""
Abstract class and helper constants for StepResult
"""
import json
import yaml


class StepResult:
    """
    Dictionary of result information for ONE step.
     {
    "newstep": {
        "step-name": "newstep",
        "step-implementer-name": "news",
        "success": True,
        "message": ""
        "artifacts": {
            "key": "key"
            "name": {
                "desc": "reporter",
                "type": "file",
                "value": "file://hello.txt"
            },
        }
    }
    }
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
        Result String
        """
        return self.get_step_result_json()

    @property
    def step_name(self):
        """
        hello
        """
        return self._step_name

    @property
    def artifacts(self):
        """
        hello
        """
        return self._artifacts

    def get_artifact(self, name):
        """
        hello
        """
        #
        return self._artifacts.get(name)

    def add_artifact(self, name, value, description='', value_type=None):
        """
        hello
        """
        if not value_type:
            value_type = type(value)
        self._artifacts[name] = {
            'description': description,
            'type': value_type,
            'value': value
        }

    @property
    def success(self):
        """
        hello
        """
        return self._success

    @success.setter
    def success(self, success=True):
        """
        hello
        """
        self._success = success

    @property
    def message(self):
        """
        hello
        """
        return self._message

    @message.setter
    def message(self, message):
        """
        hello
        """
        self._message = message

    def get_step_result(self):
        """
        Returns
        -------
        Dict
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
        hello
        """
        # return json.dumps(self.get_step_result())
        return json.dumps(self.get_step_result(), indent=4)

    def get_step_result_yaml(self):
        """
        hello
        """
        return yaml.dump(self.get_step_result())
