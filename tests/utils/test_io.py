import sys
import io
from contextlib import redirect_stdout

from tssc.utils.io import TextIOSelectiveObfuscator

from tests.helpers.base_tssc_test_case import BaseTSSCTestCase

class TestTextIOSelectiveObfuscator(BaseTSSCTestCase):
    def run_test(self, input, expected, randomize_replacment_length=False, obfuscation_targets=None, replacment_char=None):
        out = io.StringIO()
        with redirect_stdout(out):
            old_stdout = sys.stdout
            io_obfuscator = TextIOSelectiveObfuscator(
                parent_stream=old_stdout,
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
