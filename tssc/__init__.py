"""
Trusted Software Supply Chain Library (tssc-lib) main entry point.

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
