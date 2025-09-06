"""Compatibility wrapper exposing `ImageComparator` from `image_comparison`.

Keeps external imports stable while allowing the implementation to live in
`image_comparison.py`.
"""
# Wrapper module for clearer naming
from image_comparison import ImageComparator

__all__ = ["ImageComparator"]
