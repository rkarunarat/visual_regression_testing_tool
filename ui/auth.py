"""Optional password gate for network-exposed deployments."""
import hmac
import os

import streamlit as st


def _configured_password():
    """Return the configured app password, or empty string if auth is disabled."""
    return os.environ.get("APP_PASSWORD", "").strip()


def require_auth():
    """Return True when the user may access the app.

    When APP_PASSWORD is unset, authentication is skipped (local dev default).
    """
    expected = _configured_password()
    if not expected:
        return True

    if st.session_state.get("authenticated"):
        return True

    st.title("Visual Regression Testing Tool")
    st.caption("Authentication required")
    password = st.text_input("Password", type="password", key="auth_password")
    if st.button("Sign in", type="primary"):
        if hmac.compare_digest(password, expected):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid password")
    st.info("Set APP_PASSWORD in your environment to enable this gate.")
    return False
