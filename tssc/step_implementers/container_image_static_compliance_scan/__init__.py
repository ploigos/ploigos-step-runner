"""
tssc.StepImplementers for the 'container-image-static-compliance-scan' TSSC step.
"""

from .openscap import OpenSCAP

__all__ = [
    'openscap'
]
