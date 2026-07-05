"""Playwright browser installation helpers."""
import os
import subprocess
import sys
from pathlib import Path

import streamlit as st

from ui.deps import IMPORTS_OK


def ensure_playwright_browsers_installed():
    """Ensure Playwright browsers are installed (first-run setup)."""
    try:
        if st.session_state.get("_pw_browsers_ready"):
            return True

        if not IMPORTS_OK:
            st.session_state["_pw_browsers_ready"] = False
            return False

        cache_root = Path(
            os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
            or (Path.home() / ".cache/ms-playwright")
        )
        present = []
        if cache_root.exists():
            for name in ("chromium", "firefox", "webkit"):
                if any(cache_root.glob(f"{name}-*")):
                    present.append(name)

        if not present:
            with st.spinner("Installing Playwright browsers (first run only)..."):
                result = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=300,
                )
                if result.returncode != 0:
                    st.warning("Playwright browser installation may have failed. Some features may not work.")
                    st.session_state["_pw_browsers_ready"] = False
                    return False

        st.session_state["_pw_browsers_ready"] = True
        return True
    except Exception as e:
        st.warning(f"Browser setup issue: {e}")
        st.session_state["_pw_browsers_ready"] = False
        return False
