"""Trusted Software Supply Chain Library (tssc) main entry point.

Command-Line Options
--------------------

    -h, --help                                 show this help message and exit

    -s STEP, --step STEP                       TSSC workflow step to run

    -c CONFIG_FILE, --config-file CONFIG_FILE  TSSC workflow configuration file in yml or json

    -r RESULTS_DIR, --results-dir RESULTS_DIR  TSSC workflow results file in yml or json

    --step-config STEP_CONFIG_KEY=STEP_CONFIG_VALUE [STEP_CONFIG_KEY=STEP_CONFIG_VALUE ...]

                                               Override step config provided by the given TSSC
                                               config-file with these arguments.

Step Config
-----------

test

Examples
--------

Getting Help

>>> python -m tssc --help


Example Running the 'generate-metadata' step

>>> python -m tssc
...     --config-file=my-app-tssc-config.yml
...     --results-file=my-app-tssc-results.yml
...     --step=generate-metadata

"""

import __main__
from .factory import TSSCFactory
from .exceptions import TSSCException
from .step_implementer import DefaultSteps, StepImplementer
