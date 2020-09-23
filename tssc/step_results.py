"""
Abstract class and helper constants for StepResults
"""
import json
import yaml


class StepResults:
    """
     {
    "newstep": {
        "step-name": "newstep",
        "step-implementer-name": "news",
        "end-state": {
            "success": true,
            "message": "it works"
        },
        "artifacts": [
            {
                "name": "newtest_1",
                "desc": "reporter",
                "type": "file",
                "value": "file://hello.txt"
            },
            {
                "name": "newtest_2",
                "desc": "reporter",
                "type": "url",
                "value": "http://www.google.com"
            }
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

        # we build this at runtime...
        # chose a list for the yml to look pretty
        self._artifact_list = []

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

    def get_json(self):
        """
        hello
        """
        return json.dumps(self.get_result_set(), indent=4)

    def get_yaml(self):
        """
        hello
        """
        return yaml.dump(self.get_result_set())

    def get_artifacts(self):
        """
        hello
        """
        return self._artifact_list

    def get_artifact(self, name):
        """
        hello
        """
        for i in self._artifact_list:
            if i['name'] == name:
                return i
        return None

    def set_end_state(self, success, message):
        """
        hello
        """
        self._success = success
        self._message = message

    def get_result_set(self):
        """
        hello
        """
        #  this is what we output at the end...
        resultset = {
          self._step_name : {
            'step-name': self._step_name,
            'step-implementer-name': self._implementer_name,
            'end-state': {
              'success': self._success,
              'message': self._message
            },
            'artifacts': self._artifact_list
          }
        }
        return resultset

    def add_artifact(self, name, desc, thetype, value):
        """
        hello
        """
        artifact = {
            'name': name,
            'desc': desc,
            'type': thetype,
            'value': value
        }
        self._artifact_list.append(artifact)
