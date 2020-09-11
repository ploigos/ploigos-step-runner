"""Representation of a TSSC configuration value.
"""

import copy
from tssc.decription_utils import DecryptionUtils

class TSSCConfigValue:
    """Representation of a TSSC configuration value.

    Parameters
    ----------
    value : any
        The value of the config option this is the value for.
    parent_source : str file path or dict
        Path to the YML or JSON file that this value is found in or
        the dict that this value is found in.
    path_parts : list
        List of path to the element that this is the value for.

    Attributes
    ----------
    __value : any
        The value of the config option this is the value for.
    __parent_source : str file path or dict
        Path to the YML or JSON file that this value is found in or
        the dict that this value is found in.
    __path_parts : list
        List of path to the element that this is the value for.
    """

    def __init__(self, value, parent_source=None, path_parts=None):
        self.__value = value
        self.__parent_source = parent_source
        self.__path_parts = path_parts

        if self.__path_parts is None:
            self.__path_parts = []

    @property
    def value(self):
        """Get the value of this configuration value (decrypted if applicable).

        If the value happens to be decrypted then will decrypt and then return the decrypted value.

        Returns
        -------
        obj
            Value (decrypted if applicable) of this configuration value.

        See Also
        --------
        raw_value
        """
        # attemp tto decrypt the value
        decrypted_value = DecryptionUtils.decrypt(self)

        # If this value was able to be decrypted, return the decrypted result
        # else return the raw value
        if decrypted_value is not None:
            value = decrypted_value
        else:
            value = self.raw_value

        return value

    @property
    def raw_value(self):
        """Get the value of this configuration value as originally given.

        If the value happens to be encrypted this will return that raw encrypted value as it was
        given to this configuration value.

        Returns
        -------
        obj
            Value of this configuration value as originally given.

        See Also
        --------
        value
        """
        return copy.deepcopy(self.__value)

    @property
    def path_parts(self):
        """Gets copy of the list of path to the element that this is the value for.

        Returns
        -------
        list
            Copy of the list of path to the element that this is the value for.
        """
        return copy.deepcopy(self.__path_parts)

    @property
    def parent_source(self):
        """Get a copy of the source that this configuration value came from.

        Returns
        -------
        str file path or dict
            Path to the YML or JSON file that this value is found in or
            the dict that this value is found in.
        """
        return copy.deepcopy(self.__parent_source)

    def __eq__(self, other):
        """Equality for this object.

        Parameters
        ----------
        other : object
            other object to determine if equal to this object

        Returns
        -------
        bool
            True if this and the other object are both TSSCConfigValue
                objects and have the same value.
            False otherwise.
        """

        if isinstance(other, TSSCConfigValue):
            equal = self.value == other.value
        else:
            equal = False

        return equal

    def __repr__(self):
        """Human readable representation of the object.

        Returns
        -------
        str
            Human readable representation of the object.
        """
        return f"TSSCConfigValue(value={self.raw_value}, value_path='{self.path_parts}')"

    @staticmethod
    def convert_leaves_to_config_values(values, parent_source=None, path_parts=None):
        """In place recursively change all of the leaves of the given
        object to a TSSCConfigValue objects.

        Parameters
        ----------
        values : dict, list, tuple, TSSCConfigValue, None, obj
            Change all the leaves of the given object to TSSCConfigValue objects.
        parent_source : str file path or dict
            Path to the YML or JSON file that this value is found in or
            the dict that this value is found in.
        path_parts : list
            List of path to the element that this is the value for.

        Returns
        -------
        dict, list, None, or TSSCConfigValue
            If given values is a a dict then returns the same dict with all of the leaf values
                changed to TSSCConfigValue or None if already None.
            If given values is list then returns the same list with all of the leaf values
                changes to TSSCConfigValue or None if already None.
            If given values is None, return None.
            If given values is already a TSSCConfigValue return the same TSSCConfigValue

        See Also
        --------
        TSSCConfigValue.convert_leaves_to_config_values
        """
        if path_parts is None:
            path_parts = []

        if isinstance(values, dict): # pylint: disable=no-else-return
            for child_key in values:
                values[child_key] = TSSCConfigValue.convert_leaves_to_config_values(
                    values=values[child_key],
                    parent_source=parent_source,
                    path_parts=(path_parts + [child_key])
                )

            return values
        elif isinstance(values, (list, tuple)):
            for child_key, child_value in enumerate(values):
                values[child_key] = TSSCConfigValue.convert_leaves_to_config_values(
                    values=child_value,
                    parent_source=parent_source,
                    path_parts=(path_parts + [child_key])
                )

            return values
        elif isinstance(values, TSSCConfigValue):
            return values
        elif values is None:
            return None
        else:
            return TSSCConfigValue(
                value=values,
                parent_source=parent_source,
                path_parts=path_parts
            )

    @staticmethod
    def convert_leaves_to_values(values):
        """Recursively transforms all leaves of type TSSCConfigValue to TSSCConfigValue.value

        Parameters
        ----------
        values : dict, list, TSSCConfigValue, or obj
            A collection where the leaves contain TSSCConfigValue to transform back to
            TSSCConfigValue.value

        Returns
        -------
        dict, list, or obj
            If given a dictionary returns that dictionary with all leaves transformed from
                TSSCConfigValue to TSSCConfigValue.value.
            If given a list returns that dictionary with all leaves transformed from
                TSSCConfigValue to TSSCConfigValue.value.
            If given a TSSCConfigValue returns TSSCConfigValue.value
            If any other object returns that object

        See Also
        --------
        TSSCConfigValue.convert_leaves_to_config_values
        """
        if isinstance(values, dict): # pylint: disable=no-else-return
            for child_key in values:
                values[child_key] = TSSCConfigValue.convert_leaves_to_values(values[child_key])

            return values
        elif isinstance(values, (list, tuple)):
            for child_key, child_value in enumerate(values):
                values[child_key] = TSSCConfigValue.convert_leaves_to_values(child_value)

            return values
        elif isinstance(values, TSSCConfigValue):
            return values.value
        else:
            return values
