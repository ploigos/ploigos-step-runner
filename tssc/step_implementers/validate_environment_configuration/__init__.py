"""tssc.StepImplementers for the 'security-static-code-analysis' TSSC step.

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
| `TODO`           | TODO
"""

from .configlint import Configlint

__all__ = [
    'configlint'
]
