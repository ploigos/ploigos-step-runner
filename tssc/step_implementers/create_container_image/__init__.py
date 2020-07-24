"""tssc.StepImplementers for the 'create-container-image' TSSC step.

Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Parameter       | Description
|-----------------|------------
| `imagespecfile` | Image specification file name
| `context`       | Parent path to the image specification file
| `tlsverify`     | Verify TLS certs when pulling images?

Results
-------
All tssc.StepImplementers for this step should
minimally produce the following step results.

| Result Key       | Description
|------------------|------------
| `image_tag`      | TODO

"""

from .buildah import Buildah

__all__ = [
    'buildah'
]
