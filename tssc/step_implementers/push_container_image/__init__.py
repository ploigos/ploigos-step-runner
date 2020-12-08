"""`StepImplementers` for the `push-container-image` step.
"""

from .skopeo import Skopeo

__all__ = [
    'skopeo'
]
