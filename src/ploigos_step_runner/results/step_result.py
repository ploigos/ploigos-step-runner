"""Defines a StepResult object which represents the results of a invocation
of a StepImplementer#run.
"""

from ploigos_step_runner import StepRunnerException
from ploigos_step_runner.results.step_result_artifact import StepResultArtifact
from ploigos_step_runner.results.step_result_evidence import StepResultEvidence


class StepResult: # pylint: disable=too-many-instance-attributes
    """Defines a StepResult object which represents the results of a invocation
    of a StepImplementer#run.

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
        self.__evidence = {}

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
        """Get the artifacts associated with this step result.

        Returns
        -------
        dict of str: StepResultArtifacts
            Key is artifact name, value is StepResultArtifact.
        """
        return self.__artifacts

    @property
    def evidence(self):
        """Get the evidence associated with this step result.

        Returns
        -------
        dict of str: StepResultEvidence
            Key is evidence name, value is StepResultEvidence.
        """
        return self.__evidence

    @property
    def artifacts_dicts(self):
        """Get the artifacts associated with this step result as dictionaries.

        Returns
        -------
        list of dict
            Each item in list a dict representation of the StepResultArtifact.
        """
        artifact_dicts = []
        for artifact in self.artifacts.values():
            artifact_dicts.append(artifact.as_dict())

        return artifact_dicts

    @property
    def evidence_dicts(self):
        """Get the evidence associated with this step result as dictionaries.

        Returns
        -------
        list of dict
            Each item in list a dict representation of the StepResultEvidence.
        """
        evidence_dicts = []
        for evidence in self.evidence.values():
            evidence_dicts.append(evidence.as_dict())

        return evidence_dicts

    def get_artifact(self, name):
        """Get artifact with given name for this StepResult.

        Parameters
        ----------
        name : str
            The name of the artifact to return.

        Returns
        -------
        StepResultArtifact
            The step result artifact with the given name for this StepResult.
        """
        return self.__artifacts.get(name)

    def get_evidence(self, name):
        """Get evidence with given name for this StepResult.

        Parameters
        ----------
        name : str
            The name of the evidence to return.

        Returns
        -------
        StepResultEvidence
            The step result evidence with the given name for this StepResult.
        """
        return self.__evidence.get(name)

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
        if self.__artifacts.get(name):
            value = self.__artifacts.get(name).value

        return value

    def get_evidence_value(self, name):
        """Get the value for a specified evidence.

        Parameters
        ----------
        name : str
            The name of the evidence.

        Returns
        -------
        str
            The value of the evidence.
        """
        value = None
        if self.evidence.get(name):
            value = self.__evidence.get(name).value

        return value

    def add_artifact(self, name, value, description=''):
        """Add an artifact to this StepResult.

        Parameters
        ----------
        name : str
            Name of the result artifact.
        value : str
            Arbitrary value of the artifact.
        description : str, optional
            Human readable description of the result artifact (defaults to empty).
        """
        if not name:
            raise StepRunnerException('Name is required to add artifact')

        # False can be the value
        if value == '' or value is None:
            raise StepRunnerException('Value is required to add artifact')

        self.__artifacts[name] = StepResultArtifact(
            name=name,
            value=value,
            description=description
        )

    def add_evidence(self, name, value, description=''):
        """Add evidence to this StepResult.

        Parameters
        ----------
        name : str
            Name of the result evidence.
        value : str
            Arbitrary value of the evidence.
        description : str, optional
            Human readable description of the result evidence (defaults to empty).
        """
        if not name:
            raise StepRunnerException('Name is required to add evidence')

        # False can be the value
        if value == '' or value is None:
            raise StepRunnerException('Value is required to add evidence')

        self.__evidence[name] = StepResultEvidence(
            name=name,
            value=value,
            description=description
        )

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
        """Setter for success
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
        """Setter for message
        """
        self.__message = message

    def get_sub_step_result_dict(self):
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
                'artifacts': [],
                'evidence': []
            }
        """
        result = {
            'sub-step-implementer-name': self.sub_step_implementer_name,
            'success': self.success,
            'message': self.message,
            'artifacts': self.artifacts_dicts,
            'evidence': self.evidence_dicts
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
                        },
                    "evidence": {
                        "name": {
                            "description": "piece of evidence",
                            "value": "evidence"
                        }
                    }
                    }
                }
            }
        """
        if self.environment:
            result = {
                self.environment: {
                    self.step_name: {
                        self.sub_step_name: self.get_sub_step_result_dict()
                    }
                }
            }
        else:
            result = {
                self.step_name: {
                    self.sub_step_name: self.get_sub_step_result_dict()
                }
            }
        return result

    def __str__(self):
        """Get string representation of the step result.
        """
        return str({
            'step-name': self.step_name,
            'sub-step-name': self.sub_step_name,
            'sub-step-implementer-name': self.sub_step_implementer_name,
            'environment': self.environment,
            'success': self.success,
            'message': self.message,
            'artifacts': self.artifacts_dicts,
            'evidence': self.evidence_dicts
        })

    def __repr__(self):
        """Get representation of the step result.
        """
        return "StepResult(" \
            f"step_name={self.step_name}," \
            f"sub_step_name={self.sub_step_name}," \
            f"sub_step_implementer_name={self.sub_step_implementer_name}," \
            f"environment={self.environment}," \
            f"success={self.success}," \
            f"message={self.message}," \
            f"artifacts={self.artifacts_dicts}" \
            f"evidence={self.evidence_dicts}" \
            ")"

    def __eq__(self, other):
        """StepResult is equal if all properties are equal.
        """
        return (
            isinstance(other, StepResult) and
            self.step_name == other.step_name and
            self.sub_step_name == other.sub_step_name and
            self.sub_step_implementer_name == other.sub_step_implementer_name and
            self.environment == other.environment and
            self.success == other.success and
            self.message == other.message and
            self.artifacts == other.artifacts and
            self.evidence == other.evidence
        )

    def __ne__(self, other):
        """StepResult is not equal if any properties are not equal.
        """
        return not self.__eq__(other)
