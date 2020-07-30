"""tssc.StepImplementers for the 'tag-source' TSSC step.

Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Configuration Key | Description
|-------------------|------------
| `url`             | URL to the artifact repository to push the artifact to.
| `user`            | User to authenticate with the artifact repository.
| `password`        | Password to authenticate with the artifact repository.

Results
-------
All tssc.StepImplementers for this step should
minimally produce the following step results.

| Result Key       | Description
|------------------|------------
| `artifacts`      | An array of dictionaries with information on the pushed artifacts.

**artifacts**
Keys in the dictionary elements in the `artifacts` array in the step results.

| `artifacts`Key | Description
|----------------|------------
| `url`          | URL to the artifact pushed to the artifact repository
"""

from .maven import Maven
from .npm import NPM

__all__ = [
    'maven',
    'npm'
]
