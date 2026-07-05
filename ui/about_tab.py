"""About tab rendering README content."""
from pathlib import Path

import streamlit as st


def about_tab():
    """Render the README.md content as an About page."""
    st.header("About This App")
    try:
        readme_path = Path(__file__).resolve().parent.parent / "README.md"
        content = readme_path.read_text(encoding="utf-8")
        st.markdown(content, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not load README.md: {e}")
