"""tssc.StepImplementers for the 'push-artifacts' TSSC step.

Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Key                 | Description
|---------------------|------------


Results
-------
All tssc.StepImplementers for this step should
minimally produce the following step results.

| Key                | Description
|--------------------|------------
| `result`           | Dictionary of results
| `report-artifacts` | An array of dictionaries describing the push results

Elements in the `result` dictionary:
| `success`          | True or False
| `message`          | Overall status

"""

from .maven import Maven
from .npm import NPM

__all__ = [
    'maven',
    'npm'
]
