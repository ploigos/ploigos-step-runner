"""tssc.StepImplementers for the 'tag-source' TSSC step.

Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Configuration Key | Required? | Description
|-------------------|-----------|-----------
| `url`             | False     | URL to the source repository to tag. Default to current directory
                                  source repository URL if not specified.
| `username`        | False     | Username to authenticate with the source repository if needed
| `password`        | False     | Password to authenticate with the source repository if needed

Results
-------
All tssc.StepImplementers for this step should
minimally produce the following step results.

| Result Key | Description
|------------|------------
| `tag`      | This is the value that was used to tag the source.
"""

from .git import Git

__all__ = [
    'git'
]
