"""tssc.StepImplementers for the 'create_container_image' TSSC step.

Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Configuration Key | Description
|-------------------|------------
| `destination`     | Destination to push image to
| `src-tls-verify`  | Whether to very TLS for source of image
| `dest-tls-verify` | Whether to verify TLS for destination of image

Results
-------
All tssc.StepImplementers for this step should
minimally produce the following step results.

| Result Key  | Description
|-------------|------------
| `container-image-version` | Pushed destination image tag
"""

from .skopeo import Skopeo

__all__ = [
    'skopeo'
]
