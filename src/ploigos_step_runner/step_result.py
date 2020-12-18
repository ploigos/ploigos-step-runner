"""Class and helper constants for StepResult
"""
import json

import yaml

from ploigos_step_runner.exceptions import StepRunnerException


class StepResult: # pylint: disable=too-many-instance-attributes
    """
    Step result object.

    Parameters
    ----------
    step_name : str
        Name of the step
    sub_step_name : str
        Name of the sub step
    sub_step_implementer_name : str
        Name of the sub step implementer
    environment : str
        Optional. Environment that this step result is for
        if step was run against a specific environment.
    """

    def __init__(self, step_name, sub_step_name, sub_step_implementer_name, environment=None):
        self.__step_name = step_name
        self.__sub_step_name = sub_step_name
        self.__sub_step_implementer_name = sub_step_implementer_name
        self.__environment = environment
        self.__success = True
        self.__message = ''
        self.__artifacts = {}

    @classmethod
    def from_step_implementer(cls, step_implementer):
        """
        Returns
        ------
        ResultStep
        """
        return cls(
            step_name=step_implementer.step_name,
            sub_step_name=step_implementer.sub_step_name,
            sub_step_implementer_name=step_implementer.sub_step_implementer_name,
            environment=step_implementer.environment
        )

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
            Sub step name
        """
        return self.__sub_step_name

    @property
    def sub_step_implementer_name(self):
        """
        Returns
        -------
        str
            Sub step implementer name
        """
        return self.__sub_step_implementer_name

    @property
    def environment(self):
        """
        Returns
        -------
        str
            Environment name if this StepResult is specific to an environment,
            else None.
        """
        return self.__environment

    @property
    def artifacts(self):
        """
        Returns
        -------
        dict
            All artifacts of the step
            For Example:
            {
                'artifact1': {'description': 'description1', 'value': 'value1'},
                'artifact2': {'description': '', 'value': 'value2'}
            }

        """
        return self.__artifacts

    def get_artifact(self, name):
        """Get the dictionary of a specified artifact.

        Parameters
        ----------
        name : str
            The name of the artifact to return.

        Returns
        -------
        dict
            Dictionary for a specified artifact.
            For example:
            {'description': 'artifact1', 'value': 'value1'}

        """
        return self.artifacts.get(name)

    def get_artifact_value(self, name):
        """Get the value for a specified artifact.

        Parameters
        ----------
        name : str
            The name of the artifact.

        Returns
        -------
        str
            The value of the artifact.
        """
        value = None
        if self.artifacts.get(name):
            value = self.artifacts.get(name).get('value')

        return value

    def add_artifact(self, name, value, description=''):
        """Insert/Update an artifact with the given pattern:

        "name": {
            "description": "file description",
            "value": "step-result.txt"
        }

        Parameters
        ----------
        name : str
            Required name of the artifact
        value : str
            Required content
        description : str, optional
            Optional description (defaults to empty)

        """
        if not name:
            raise StepRunnerException('Name is required to add artifact')

        # False can be the value
        if value == '' or value is None:
            raise StepRunnerException('Value is required to add artifact')

        self.__artifacts[name] = {
            'description': description,
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
        """
        Returns
        -------
        dict
            Dictionary with the details for the sub-step.
            For example:
            {
                'sub-step-implementer-name': 'value',
                'success': Boolean,
                'message': 'value',
                'artifacts': {}
            }
        """
        result = {
            'sub-step-implementer-name': self.sub_step_implementer_name,
            'success': self.success,
            'message': self.message,
            'artifacts': self.artifacts
        }
        return result

    def get_step_result_dict(self):
        """Get the step result dictionary

        Returns
        -------
        dict
            Results with all step result components.
            For example:
            "step-name: {
                "sub-step-name": {
                    "sub-step-implementer-name": "sub_step_implementer_name",
                    "success": True,
                    "message": "",
                    "artifacts": {
                        "name": {
                            "description": "file description",
                            "value": "step-result.txt"
                        }
                    }
                }
            }
        """
        if self.environment:
            result = {
                self.environment: {
                    self.step_name: {
                        self.sub_step_name: self.get_sub_step_result()
                    }
                }
            }
        else:
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
        return json.dumps(self.get_step_result_dict())

    def get_step_result_yaml(self):
        """
        Returns
        -------
        str
            YAML formatted step result
        """
        return yaml.dump(self.get_step_result_dict())
