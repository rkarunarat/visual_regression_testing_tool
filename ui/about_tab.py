"""About tab rendering README content."""
from pathlib import Path

import streamlit as st

from ui.theme import render_page_header


def about_tab():
    """Render the README.md content as an About page."""
    render_page_header("About", "Documentation and overview for this visual testing tool.")
    try:
        readme_path = Path(__file__).resolve().parent.parent / "README.md"
        content = readme_path.read_text(encoding="utf-8")
        st.markdown(content, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not load README.md: {e}")
