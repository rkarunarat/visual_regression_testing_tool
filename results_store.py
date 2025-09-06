"""Compatibility wrapper exposing `ResultManager` from `result_manager`.

This allows importing `results_store.ResultManager` while the implementation
remains in `result_manager.py`.
"""
# Wrapper module for clearer naming
from result_manager import ResultManager

__all__ = ["ResultManager"]
