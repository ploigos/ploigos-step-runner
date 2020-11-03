"""tssc.StepImplementers for the 'package' TSSC step.

Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Parameter       | Description
|-----------------|------------
| `TODO`          | TODO

Results
-------
All tssc.StepImplementers for this step should
minimally produce the following step results.

| Result Key       | Description
|------------------|------------
| `artifacts`      | An array of dictionaries with information on the built artifacts.
                     Minimally each dictionary entry should have a `path` key with the absolute path
                     to the built artifact.

**artifacts**

| `artifacts` Key | Description
|-----------------|------------
| `path`          | Absolute path to the built artifact
"""

from .maven import Maven
from .npm import NPM

__all__ = [
    'maven'
]
