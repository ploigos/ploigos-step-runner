"""
Abstract class and helper constants for StepResult
"""
import json
import yaml


class StepResult:
    """
     {
    "newstep": {
        "step-name": "newstep",
        "step-implementer-name": "news",
        "success": True,
        "message": ""
        "artifacts": {
            "name": {
                "desc": "reporter",
                "type": "file",
                "value": "file://hello.txt"
            },
        ]
    }
    }
    """

    def __init__(self, step_name, implementer_name):
        """
        hello
        """
        self._step_name = step_name
        self._implementer_name = implementer_name
        self._success = True
        self._message = ''
        self._artifacts = {}

    def __str__(self):
        """
        hello
        """
        string = u'[step:%s %s message: %s]' %(self._step_name,
                                               self._implementer_name,
                                               self._message)
        return string

    def get_step_name(self):
        """
        hello
        """
        return self._step_name

    def get_artifacts(self):
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

    def add_artifact(self, name, desc, the_type, value):
        """
        hello
        """
        self._artifacts[name] = {
            'desc': desc,
            'type': the_type,
            'value': value
        }

    def get_json(self):
        """
        public
        """
        #return json.dumps(self.get_result_set(), indent=4)
        return json.dumps(self.get_step_result())

    def get_yaml(self):
        """
        hello
        """
        return yaml.dump(self.get_step_result())

    def set_success_message(self, success, message=''):
        """
        hello
        """
        self._success = success
        self._message = message

    def get_step_result(self):
        """
        hello
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
