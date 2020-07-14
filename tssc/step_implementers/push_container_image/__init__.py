"""
tssc.StepImplementers for the 'create_container_image' TSSC step.
"""

from .skopeo import Skopeo

__all__ = [
    'skopeo'
]
