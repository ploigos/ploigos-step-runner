"""Shared utilities for dealing with IO
"""

import io
import random
import re

class TextIOSelectiveObfuscator(io.TextIOBase):
    """Extends the base class for text streams to allow the obfuscation of given patterns.

    This is useful to prevent accidently writing "sensitive" information to stdout/stderr.

    Parameters
    ----------
    parent_stream : IOBase
        IO stream to write to after obfuscating any text written to this stream.
    randomize_replacment_length : bool, optional
        True to randomize the length of the text being obfuscated in the stream.
        False to use the same length replacement for any obfuscated text in the stream.
    replacement_char : char
        Character to replace the target strings to obfuscate with.

    Attributes
    ----------
    __parent_stream : IOBase
    __obfuscation_targets : list
    __replacement_char : char
    __randomize_replacment_length : bool
    __random_replacement_length_min : int
    __random_replacment_length_max : int
    """

    def __init__(self, parent_stream, randomize_replacment_length=True, replacement_char='*'):
        self.__parent_stream = parent_stream
        self.__obfuscation_targets = []
        self.__replacement_char = replacement_char
        self.__randomize_replacment_length = randomize_replacment_length
        self.__random_replacement_length_min = 5
        self.__random_replacment_length_max = 40
        super().__init__()

    @property
    def parent_stream(self):
        """
        Returns
        -------
        IOBase
            IO stream this stream writes to after obfuscating any text written to this stream.
        """
        return self.__parent_stream

    @property
    def replacement_char(self):
        """
        Returns
        -------
        char
            Character to replace the target strings to obfuscate with.
        """
        return self.__replacement_char

    @replacement_char.setter
    def replacement_char(self, replacement_char):
        """
        Parameters
        ----------
        replacement_char : char
            Character to replace the target strings to obfuscate with.
        """
        self.__replacement_char = replacement_char

    @property
    def randomize_replacment_length(self):
        """
        Returns
        -------
        bool
            True if this stream is randomizing the length of the text being obfuscated.
            False if this stream is using the same length replacement for any obfuscated text.
        """
        return self.__randomize_replacment_length

    def add_obfuscation_targets(self, targets):
        """Adds a target pattern to be obfuscated whenever writing to this stream.

        Parameters
        ----------
        targets : list or pattern
            The target patterns to be obfuscated when writing to this stream.
        """
        if isinstance(targets, list):
            self.__obfuscation_targets += targets
        else:
            self.__obfuscation_targets.append(targets)

    def __obfuscator(self, match):
        """Given a regex match returns a corresponding obfuscated string.

        Parameters
        ----------
        match : re.Match
            re.Match to replace with obfuscated text

        Returns
        -------
        str
            String to replace the given match with.

        Also See
        --------
        re.sub
        """

        if self.randomize_replacment_length:
            replacment_length = random.randint(
                self.__random_replacement_length_min,
                self.__random_replacment_length_max
            )
        else:
            replacment_length = len(match.group())

        return self.replacement_char * replacment_length

    def write(self, given):
        """Writes to this streams parent stream after obfuscating all of the obfuscation targets.

        Parameters
        ----------
        given : str
            Given string to write to the parent stream after obfuscating.

        Returns
        -------
        int
            Number of characters written.

        See Also
        --------
        io.TextIOBase.write
        """
        obfuscated = given
        for obfuscation_target in self.__obfuscation_targets:
            obfuscated = re.sub(obfuscation_target, self.__obfuscator, obfuscated)

        return self.parent_stream.write(obfuscated)
