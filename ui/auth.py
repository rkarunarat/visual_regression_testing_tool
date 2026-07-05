"""Optional password gate for network-exposed deployments."""
import hmac
import os

import streamlit as st

from ui.theme import inject_global_styles


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

    inject_global_styles()
    st.markdown(
        """
        <div class="vrt-auth-wrap">
            <h1 class="vrt-auth-title">Visual Regression Testing</h1>
            <p class="vrt-auth-subtitle">Sign in to access the testing dashboard</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    password = st.text_input("Password", type="password", key="auth_password")
    if st.button("Sign in", type="primary", use_container_width=True):
        if hmac.compare_digest(password, expected):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid password")
    st.info("Set APP_PASSWORD in your environment to enable this gate.")
    return False
