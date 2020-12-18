# pylint: disable=W0614,W0401

"""
Ploigos step runner entry point.

Exit Codes
----------
101
    specified -c/--config must exist and not be empty
102
    specified -c/--config is invalid configuration
200
    step completed with unsuccessful results
300
    step failed completion because of an exception
"""

import argparse
import os.path
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout

from ploigos_step_runner.config.config import Config
from ploigos_step_runner.decryption_utils import DecryptionUtils
from ploigos_step_runner.step_runner import StepRunner
from ploigos_step_runner.utils.io import TextIOSelectiveObfuscator


def print_error(msg):
    """
    Prints message to STDERR.

    Parameters
    ----------
    msg : string
        Message to print as an error.
    """
    print(msg, file=sys.stderr)


class ParseKeyValueArge(argparse.Action):  # pylint: disable=too-few-public-methods
    """
    https://gist.github.com/fralau/061a4f6c13251367ef1d9a9a99fb3e8d
    """

    def __call__(self, parser, namespace, values, option_string=None):
        key_value_dict = {}

        if values:
            for item in values:
                split_items = item.split("=", 1)
                key = split_items[
                    0
                ].strip()  # we remove blanks around keys, as is logical
                value = split_items[1]

                key_value_dict[key] = value

        setattr(namespace, self.dest, key_value_dict)


def main(argv=None):
    """Main entry point for Ploigos step runner.
    """
    parser = argparse.ArgumentParser(description='Ploigos Step Runner (psr)')
    parser.add_argument(
        '-s',
        '--step',
        required=True,
        help='Workflow step to run'
    )
    parser.add_argument(
        '-e',
        '--environment',
        required=False,
        help='The environment to run this step against.'
    )
    parser.add_argument(
        '-c',
        '--config',
        required=True,
        nargs='+',
        help='Workflow configuration files, or directories containing files, in yml or json'
    )
    parser.add_argument(
        '-r',
        '--results-dir',
        default='step-runner-results',
        help='Workflow results file in yml or json'
    )
    parser.add_argument(
        '--step-config',
        metavar='STEP_CONFIG_KEY=STEP_CONFIG_VALUE',
        nargs='+',
        help='Override step config provided by the given config-file with these arguments.',
        action=ParseKeyValueArge
    )
    args = parser.parse_args(argv)

    obfuscated_stdout = TextIOSelectiveObfuscator(sys.stdout)
    obfuscated_stderr = TextIOSelectiveObfuscator(sys.stderr)
    DecryptionUtils.register_obfuscation_stream(obfuscated_stdout)
    DecryptionUtils.register_obfuscation_stream(obfuscated_stderr)

    with redirect_stdout(obfuscated_stdout), redirect_stderr(obfuscated_stderr):
        # validate args
        for config_file in args.config:
            if not os.path.exists(config_file) or os.stat(config_file).st_size == 0:
                print_error('specified -c/--config must exist and not be empty')
                sys.exit(101)

        try:
            config = Config(args.config)
        except (ValueError, AssertionError) as error:
            print_error(f"specified -c/--config is invalid configuration: {error}")
            sys.exit(102)

        config.set_step_config_overrides(args.step, args.step_config)
        step_runner = StepRunner(config, args.results_dir)

        try:
            if not step_runner.run_step(args.step, args.environment):
                print_error(f"Step {args.step} not successful")
                sys.exit(200)

        except Exception as error:  # pylint: disable=broad-except
            print_error(f"Fatal error calling step ({args.step}): {str(error)}")
            track = traceback.format_exc()
            print(track)
            sys.exit(300)


def init():
    """
    Notes
    -----
    See https://medium.com/opsops/how-to-test-if-name-main-1928367290cb
    """
    if __name__ == "__main__":
        sys.exit(main())


init()
