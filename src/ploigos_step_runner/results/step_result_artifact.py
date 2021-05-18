"""Defines a StepResultArtifact object which represents an artifact included in the StepResult
of a invocation of a StepImplementer#run.
"""

class StepResultArtifact:
    """Defines a StepResultArtifact object which represents an artifact included in the StepResult
    of a invocation of a StepImplementer#run.

    Parameters
    ----------
    name : str
        Name of the result artifact.
    value : str
        Arbitrary value of the artifact.
    description : str, optional
        Human readable description of the result artifact (defaults to empty).
    """
    def __init__(self, name, value, description=''):
        self.__name = name
        self.__value = value
        self.__description = description

    @property
    def name(self):
        """Getter for name step result artifact name.

        Returns
        -------
        str
            Step result artifact name.
        """
        return self.__name

    @property
    def value(self):
        """Getter for name step result artifact value.

        Returns
        -------
        object
            Step result artifact value.
        """
        return self.__value

    @property
    def description(self):
        """Getter for name step result artifact description.

        Returns
        -------
        str
            Step result artifact description.
        """
        return self.__description

    def as_dict(self):
        """Dictionary representation of this artifact.

        Returns
        -------
        dict
            Representation of this artifact.
        """
        return {
            'name': self.name,
            'value': self.value,
            'description': self.description
        }

    def __str__(self):
        """Get string representation of the artifact.
        """
        return str({
            'name': self.name,
            'value': self.value,
            'description': self.description
        })

    def __repr__(self):
        """Get representation of the artifact.
        """
        return "StepResultArtifact(" \
            f"name={self.name}," \
            f" value={self.value}," \
            f" description={self.description}" \
            ")"

    def __eq__(self, other):
        """StepResultArtifact is equal if all properties are equal.
        """
        return (
            isinstance(other, StepResultArtifact) and
            self.name == other.name and
            self.value == other.value and
            self.description == other.description
        )

    def __ne__(self, other):
        """StepResultArtifact is not equal if any properties are not equal.
        """
        return not self.__eq__(other)
