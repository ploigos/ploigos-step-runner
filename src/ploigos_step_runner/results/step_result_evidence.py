"""Defines a StepResultEvidence object which represents an evidence included in the StepResult
of a invocation of a StepImplementer#run.
"""

class StepResultEvidence:
    """Defines a StepResultEvidence object which represents an evidence included in the StepResult
    of a invocation of a StepImplementer#run.

    Parameters
    ----------
    name : str
        Name of the result evidence.
    value : str
        Arbitrary value of the evidence.
    description : str, optional
        Human readable description of the result evidence (defaults to empty).
    """
    def __init__(self, name, value, description=''):
        self.__name = name
        self.__value = value
        self.__description = description

    @property
    def name(self):
        """Getter for name step result evidence name.

        Returns
        -------
        str
            Step result evidence name.
        """
        return self.__name

    @property
    def value(self):
        """Getter for name step result evidence value.

        Returns
        -------
        object
            Step result evidence value.
        """
        return self.__value

    @property
    def description(self):
        """Getter for name step result evidence description.

        Returns
        -------
        str
            Step result evidence description.
        """
        return self.__description

    def as_dict(self):
        """Dictionary representation of this evidence.

        Returns
        -------
        dict
            Representation of this evidence.
        """
        return {
            'name': self.name,
            'value': self.value,
            'description': self.description
        }

    def __str__(self):
        """Get string representation of the evidence.
        """
        return str({
            'name': self.name,
            'value': self.value,
            'description': self.description
        })

    def __repr__(self):
        """Get representation of the evidence.
        """
        return "StepResultEvidence(" \
            f"name={self.name}," \
            f" value={self.value}," \
            f" description={self.description}" \
            ")"

    def __eq__(self, other):
        """StepResultEvidence is equal if all properties are equal.
        """
        return (
            isinstance(other, StepResultEvidence) and
            self.name == other.name and
            self.value == other.value and
            self.description == other.description
        )

    def __ne__(self, other):
        """StepResultEvidence is not equal if any properties are not equal.
        """
        return not self.__eq__(other)
