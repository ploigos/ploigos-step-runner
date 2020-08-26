"""tssc.StepImplementers for the 'push-artifacts' TSSC step.

Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Key                 | Description
|---------------------|------------
| `url`               | URL to the artifact repository to push the artifact to.
| `user`              | User to authenticate with the artifact repository.
| `password`          | Password to authenticate with the artifact repository.

Results
-------
All tssc.StepImplementers for this step should
minimally produce the following step results.

| Key                 | Description
|---------------------|------------
| `artifacts`         | An array of dictionaries with information on the pushed artifacts.

"""

from .maven import Maven
from .npm import NPM

__all__ = [
    'maven',
    'npm'
]
