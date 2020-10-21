"""Shared utilities for dealing with IO
"""

import io
import random
import re


def create_sh_redirect_to_multiple_streams_fn_callback(streams):
    """Creates and returns a function callback that will write given data to multiple given streams.

    AKA: this essentially allows you to do 'tee' for sh commands.

    Parameters
    ----------
    streams : list of io.IOBase
        Streams to write to.

    Examples
    --------
    Will write output directed at stdout to stdout and a results file and output directed
    at stderr to stderr and a results file.
    >>> with open('/tmp/results_file', 'w') as results_file:
    ...     out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
    ...         sys.stdout,
    ...         results_file
    ...     ])
    ...     err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
    ...         sys.stderr,
    ...         results_file
    ...     ])
    ...     sh.echo('hello world')
    hello world

    Returns
    -------
    function(data)
        Function that takes one parameter, data, and writes that value to all the given streams.
    """

    def sh_redirect_to_multiple_streams(data):
        for stream in streams:
            stream.write(data)

    return sh_redirect_to_multiple_streams


class TextIOSelectiveObfuscator(io.TextIOBase):
    """Extends the base class for text streams to allow the obfuscation of given patterns.

    This is useful to prevent accidentally writing "sensitive" information to stdout/stderr.

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
    __obfuscation_patterns : list
    __replacement_char : char
    __randomize_replacement_length : bool
    __random_replacement_length_min : int
    __random_replacement_length_max : int
    """

    def __init__(self, parent_stream, randomize_replacment_length=True, replacement_char='*'):
        self.__parent_stream = parent_stream
        self.__obfuscation_patterns = []
        self.__replacement_char = replacement_char
        self.__randomize_replacement_length = randomize_replacment_length
        self.__random_replacement_length_min = 5
        self.__random_replacement_length_max = 40
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
    def randomize_replacement_length(self):
        """
        Returns
        -------
        bool
            True if this stream is randomizing the length of the text being obfuscated.
            False if this stream is using the same length replacement for any obfuscated text.
        """
        return self.__randomize_replacement_length

    def add_obfuscation_targets(self, targets):
        """Adds a target pattern to be obfuscated whenever writing to this stream.

        Notes
        -----
        This is a bit involved to deal with secrets that span multiple lines and various ways they
        can be printed. so the regex gets pretty involved to escape the right things and ignore
        whitespace, so forth and so on.

        There are unit tests covering the scenarios this is dealing with, if you are messing in
        here be sure you don't break any of the existing unit tests.

        Parameters
        ----------
        targets : list or pattern
            The target patterns to be obfuscated when writing to this stream.
        """
        if not isinstance(targets, list):
            targets = [targets]

        for target in targets:
            target_pattern = target

            # replace any amount of whitespace with a single space
            target_pattern = re.sub(r'\s+', ' ', target_pattern)

            # strip off leading and trialing whitespace
            target_pattern = target_pattern.strip()

            # escape for use in regex pattern
            target_pattern = re.escape(target_pattern)

            # the spaces we added in now got escaped, so unescape them and turn them into .*
            target_pattern = re.sub(r'\\ ', r'.*', target_pattern)

            # eat up pre and post newlines
            # target_pattern = f"(\s*)({target_pattern})(\s*)"

            # compile the pattern for re-use and make sure that .* matches accross lines
            target_compiled_pattern = re.compile(target_pattern, re.DOTALL)

            # add the pattern
            self.__obfuscation_patterns.append(target_compiled_pattern)

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

        if self.randomize_replacement_length:
            replacement_length = random.randint(
                self.__random_replacement_length_min,
                self.__random_replacement_length_max
            )
        else:
            replacement_length = len(match.group())

        return self.replacement_char * replacement_length

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

        if isinstance(given, bytes):
            obfuscated = given.decode('utf-8')
        else:
            obfuscated = given

        for obfuscation_pattern in self.__obfuscation_patterns:
            obfuscated = obfuscation_pattern.sub(self.__obfuscator, obfuscated)

        return self.parent_stream.write(obfuscated)

    def flush(self):
        """Flush the parent stream.

        See Also
        --------
        io.TextIOBase.flush
        """
        self.parent_stream.flush()


class TextIOIndenter(io.TextIOBase):
    """Adds an indent to the first string written and after every new line written to this stream.

    Notes
    -----
    WARNING:    There will be a dangling indent after the last new line written to this stream
                because there is no "good" way of knowing the last new line ever written to this
                stream.

    Parameters
    ----------
    parent_stream : IOBase
        Stream to write to after indenting what is written to this stream
    indent_level : int, optional
        Level to indent to.
        Will be multiplied by the indent_size.
    indent_size : int, optional
        Size of each indent.
        Will be multipled by the indent_level.
    indent_char : str, optional
        Character to use for indent.
        Will be multiplied by the indent_size and the ident_level and prepended before
        each line written to this stream.
    """

    def __init__(self, parent_stream, indent_level=0, indent_size=4, indent_char=' '):
        self.__parent_stream = parent_stream
        self.__indent_level = indent_level
        self.__indent_size = indent_size
        self.__indent_char = indent_char
        self.__unwritten_to = True
        super().__init__()

    @property
    def parent_stream(self):
        """Returns parent stream that this stream wraps

        Returns
        -------
        IOBase
            Stream to write to after indenting what is written to this stream
        """
        return self.__parent_stream

    @property
    def indent_level(self):
        """Level to indent to.

        Returns
        -------
        int
            Level to indent to.
        """
        return self.__indent_level

    @property
    def indent_size(self):
        """Size of each indent.

        Returns
        -------
        int
            Size of each indent.
        """
        return self.__indent_size

    @property
    def indent_char(self):
        """Character to use for indent.

        Will be multiplied by the indent_size and the ident_level and prepended before
        each line written to this stream.

        Returns
        -------
        str
            Character to use for indent.
        """
        return self.__indent_char

    def write(self, given):
        """Indents the begining of the given text as well as every new line in the given text
        and then writes it to this steams parent_stream.

        Notes
        -----
        If there is a new line at the end of the given string there will not be an indent
        written after that new line assuming that the next line will be written by this stream
        and therefor get indented as being initially written to this stream.

        Parameters
        ----------
        given : str or bytes (utf-8)
            String to indent every line of before writing to parent stream.

        Examples
        --------
        >>> TextIOIndenter(sys.stdout).write("hello world\\n")
        hello world
        <BLANKLINE>

        >>> TextIOIndenter(sys.stdout, 1).write("hello world\\n")
            hello world
            <BLANKLINE>

        >>> TextIOIndenter(sys.stdout, 2).write("hello world\\n")
                hello world
                <BLANKLINE>

        >>> TextIOIndenter(sys.stdout).write("\\nhello world\\n")
        <BLANKLINE>
        hello world
        <BLANKLINE>

        >>> TextIOIndenter(sys.stdout, 1).write("\\nhello world\\n")
            <BLANKLINE>
            hello world
            <BLANKLINE>

        >>> TextIOIndenter(sys.stdout, 2).write("\\nhello world\\n")
                <BLANKLINE>
                hello world
                <BLANKLINE>

        >>> TextIOIndenter(sys.stdout, 0, 2, '-').write("hello world")
        hello world

        >>> TextIOIndenter(sys.stdout, 1, 2, '-').write("hello world")
        --hello world

        >>> TextIOIndenter(sys.stdout, 2, 2, '-').write(hello world")
        ----hello world

        >>> TextIOIndenter(sys.stdout, 1).write("hello\\nworld\\n")
            hello
            world
            <BLANKLINE>


        >>> TextIOIndenter(sys.stdout, 2).write("hello\\nworld\\n")
                hello
                world
                <BLANKLINE>

        >>> indenter = TextIOIndenter(sys.stdout, 1)
        ... indenter.write("hello\\nworld\\n")
        ... indenter.write("foo bar\\n")
            hello
            world
            foo bar

        >>> indenter = TextIOIndenter(sys.stdout, 1)
        ... indenter.write("hello world ")
        ... indenter.write("foo bar\\n")
        ... indenter.write("this is a test, ")
        ... indenter.write("more testing\\n")
        ... indenter.write("fortytwo\\n")
            hello world foo bar
            this is a test more testing
            fortytwo

        Returns
        -------
        int
            Number of characters written.

        See Also
        --------
        io.TextIOBase.write
        """
        if isinstance(given, bytes):
            indented = given.decode('utf-8')
        else:
            indented = given

        # create the indent to insert at begining of given text and every new line in that text
        indent_chars = self.indent_char * (self.indent_size * self.indent_level)

        if self.__unwritten_to:
            self.__unwritten_to = False
            indented = f"{indent_chars}{indented}"

        # add indent after every new line
        # NOTE: \1 is capture group one and contains the original new line character
        indented = re.sub(r"(\r\n|\r|\n)", r"\1" + indent_chars, indented)

        return self.parent_stream.write(indented)

    def flush(self):
        """Flush the parent stream.

        See Also
        --------
        io.TextIOBase.flush
        """
        self.parent_stream.flush()
