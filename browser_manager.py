"""Compatibility wrapper exposing `BrowserManager` from `browser_automation`.

Allows importing `browser_manager.BrowserManager` with implementation in
`browser_automation.py`.
"""
# Wrapper module for clearer naming
from browser_automation import BrowserManager

__all__ = ["BrowserManager"]
