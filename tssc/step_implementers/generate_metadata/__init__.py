"""tssc.StepImplementers for the 'generate-metadata' TSSC step.

Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Parameter       | Description
|-----------------|------------
| `TODO`          | TODO

Step Results
------------
The combination of tssc.StepImplementers for this step should
minimally produce the following step results.

| Result Key  | Description
|-------------|------------
| `version`   | Constructed semantic version (https://semver.org/).
| `image-tag` | Constructed semantic version (https://semver.org/) modified \
                to work as a container image tag.
"""

from .maven import Maven
from .git import Git
from .semantic_version import SemanticVersion

__all__ = [
    'maven',
    'git',
    'semantic_version'
]
