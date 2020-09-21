import sys
import io
from contextlib import redirect_stdout

from tssc.utils.io import TextIOSelectiveObfuscator, TextIOIndenter

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

class TestTextIOSelectiveObfuscator(BaseTSSCTestCase):
    def run_test(self, input, expected, randomize_replacment_length=False, obfuscation_targets=None, replacment_char=None):
        out = io.StringIO()
        with redirect_stdout(out):
            io_obfuscator = TextIOSelectiveObfuscator(
                parent_stream=sys.stdout,
                randomize_replacment_length=randomize_replacment_length
            )

            if obfuscation_targets is not None:
                io_obfuscator.add_obfuscation_targets(obfuscation_targets)
            if replacment_char is not None:
                io_obfuscator.replacement_char = replacment_char

            io_obfuscator.write(input)

            self.assertRegex(out.getvalue(), expected)

    def test_no_obfuscation(self):
        self.run_test(
            input='hello world',
            expected='hello world'
        )

    def test_single_obfuscation(self):
        self.run_test(
            input='hello world secret should be hidden because secret is not for your eyes',
            expected=r'hello world \*\*\*\*\*\* should be hidden because ' \
                     r'\*\*\*\*\*\* is not for your eyes',
            obfuscation_targets='secret'
        )

    def test_multiple_obfuscation(self):
        self.run_test(
            input='hello world secret should be hidden because secret is not for your eyes',
            expected=r'hello world \*\*\*\*\*\* should be \*\*\*\*\*\* because ' \
                     r'\*\*\*\*\*\* is not for your eyes',
            obfuscation_targets=['secret', 'hidden']
        )

    def test_custom_replacement_char(self):
        self.run_test(
            input='hello world secret should be hidden because secret is not for your eyes',
            expected='hello world !!!!!! should be hidden because !!!!!! is not for your eyes',
            obfuscation_targets=['secret'],
            replacment_char='!'
        )

    def test_random_replacement_length(self):
        self.run_test(
            input='hello world secret should be hidden because secret is not for your eyes',
            expected=r'hello world \*\*\*\*\*.* should be hidden because ' \
                     r'\*\*\*\*\*.* is not for your eyes',
            obfuscation_targets=['secret'],
            randomize_replacment_length=True
        )

    def test_byte_obfuscation(self):
        self.run_test(
            input=b'hello world secret should be hidden because secret is not for your eyes',
            expected=r'hello world \*\*\*\*\*\* should be hidden because ' \
                     r'\*\*\*\*\*\* is not for your eyes',
            obfuscation_targets='secret'
        )

class TestTextIOIndenter(BaseTSSCTestCase):
    def __run_test(self, inputs, expected, indent_level=0, indent_size=4, indent_char=' '):
        out = io.StringIO()
        with redirect_stdout(out):
            indenter = TextIOIndenter(
                parent_stream=sys.stdout,
                indent_level=indent_level,
                indent_size=indent_size,
                indent_char=indent_char
            )

            if not isinstance(inputs, list):
                inputs = [inputs]

            for input in inputs:
                indenter.write(input)

            self.assertRegex(out.getvalue(), expected)

    def test_one_line_bytes_no_indent(self):
        self.__run_test(
            inputs=b"hello world",
            expected=r"hello world"
        )

    def test_one_line_no_indent(self):
        self.__run_test(
            inputs="hello world",
            expected=r"hello world"
        )

    def test_one_line_1_indent_leading_newline(self):
        self.__run_test(
            inputs=["\n","hello world"],
            expected=r"hello world",
            indent_level=1
        )

    def test_one_line_1_indent_no_leading_newline(self):
        self.__run_test(
            inputs="hello world",
            expected=r"hello world",
            indent_level=1
        )

    def test_one_line_2_indent_leading_newline(self):
        self.__run_test(
            inputs=["\n","hello world"],
            expected=r"        hello world",
            indent_level=2
        )

    def test_one_line_2_indent_no_leading_newline(self):
        self.__run_test(
            inputs=["hello world"],
            expected=r"hello world",
            indent_level=2
        )

    def test_one_line_trailing_newline_no_indent(self):
        self.__run_test(
            inputs="hello world\n",
            expected=r"hello world\n"
        )

    def test_one_line_trailing_newline_1_indent(self):
        self.__run_test(
            inputs="hello world\n",
            expected=r"hello world\n    ",
            indent_level=1
        )

    def test_one_line_0_indent_2_char_diff_char(self):
        self.__run_test(
            inputs="hello world",
            expected=r"hello world",
            indent_level=0,
            indent_size=2,
            indent_char='-'
        )

    def test_one_line_1_indent_2_char_diff_char(self):
        self.__run_test(
            inputs="hello world",
            expected=r"--hello world",
            indent_level=1,
            indent_size=2,
            indent_char='-'
        )

    def test_one_line_2_indent_2_char_diff_char(self):
        self.__run_test(
            inputs="hello world",
            expected=r"----hello world",
            indent_level=2,
            indent_size=2,
            indent_char='-'
        )

    def test_multi_line_no_indent(self):
        self.__run_test(
            inputs="hello\nworld",
            expected=r"hello\nworld"
        )

    def test_multi_line_1_indent(self):
        self.__run_test(
            inputs="hello\nworld",
            expected=r"    hello\n    world",
            indent_level=1
        )

    def test_multi_line_2_indent(self):
        self.__run_test(
            inputs="hello\nworld",
            expected=r"        hello\n        world",
            indent_level=2
        )

    def test_multi_line_trailing_newline_1_indent(self):
        self.__run_test(
            inputs="hello\nworld\n",
            expected=r"    hello\n    world\n",
            indent_level=1
        )

    def test_multi_line_trailing_newline_2_indent(self):
        self.__run_test(
            inputs="hello\nworld\n",
            expected=r"        hello\n        world\n",
            indent_level=2
        )

    def test_multiple_writes_new_line_on_first_write(self):
        self.__run_test(
            inputs=["hello\nworld\n","foo\nbar"],
            expected=r"    hello\n    world\n    foo\n    bar",
            indent_level=1
        )

    def test_multiple_writes_write_to_same_line_more_then_once(self):
        self.__run_test(
            inputs=[
                "hello world ",
                "foo bar\n",
                "this is a test, ",
                "more testing\n",
                "fortytwo\n"
            ],
            expected=r"    hello world foo bar\n    this is a test, more testing\n    fortytwo\n",
            indent_level=1
        )
