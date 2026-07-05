"""Global UI theme and layout helpers for the Streamlit app."""

import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --vrt-green: #2f855a;
    --vrt-green-hover: #276749;
    --vrt-green-soft: #f0fdf4;
    --vrt-green-muted: #dcfce7;
    --vrt-green-ring: rgba(47, 133, 90, 0.18);
    --vrt-surface: #ffffff;
    --vrt-bg: #fafafa;
    --vrt-border: #e5e7eb;
    --vrt-text: #111827;
    --vrt-muted: #6b7280;
    --vrt-radius: 8px;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--vrt-text);
}

.stApp {
    background: var(--vrt-bg);
}

.block-container {
    padding-top: 1.25rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* Header — clean, no gradient */
.vrt-hero {
    background: var(--vrt-surface);
    border: 1px solid var(--vrt-border);
    border-left: 4px solid var(--vrt-green);
    border-radius: var(--vrt-radius);
    padding: 1.35rem 1.5rem;
    margin-bottom: 1.25rem;
}
.vrt-hero-eyebrow {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--vrt-green);
    margin: 0 0 0.4rem 0;
}
.vrt-hero-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 0 0.3rem 0;
    line-height: 1.25;
    color: var(--vrt-text);
}
.vrt-hero-subtitle {
    font-size: 0.9rem;
    margin: 0;
    color: var(--vrt-muted);
    max-width: 560px;
    line-height: 1.5;
}

/* Page headers */
.vrt-page-header {
    margin: 0 0 1rem 0;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--vrt-border);
}
.vrt-page-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--vrt-text);
    margin: 0 0 0.2rem 0;
}
.vrt-page-subtitle {
    font-size: 0.875rem;
    color: var(--vrt-muted);
    margin: 0;
    line-height: 1.45;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--vrt-surface);
    border-right: 1px solid var(--vrt-border);
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}
.vrt-sidebar-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--vrt-muted);
    margin: 0.85rem 0 0.4rem 0;
}
.vrt-sidebar-divider {
    border: none;
    border-top: 1px solid var(--vrt-border);
    margin: 0.85rem 0;
}

/* Navigation */
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: transparent;
    border: 1px solid transparent;
    border-radius: var(--vrt-radius);
    padding: 0.4rem 0.6rem;
    font-weight: 500;
    font-size: 0.9rem;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: var(--vrt-bg);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: var(--vrt-green-soft) !important;
    border-color: var(--vrt-green-muted) !important;
    color: var(--vrt-green) !important;
    font-weight: 600 !important;
}

/* Tabs — minimal underline style */
.stTabs [data-baseweb="tab-list"] {
    gap: 1.25rem;
    background: transparent;
    border-bottom: 1px solid var(--vrt-border);
}
.stTabs [data-baseweb="tab"] {
    height: 40px;
    padding: 0 0.15rem;
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--vrt-muted);
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    color: var(--vrt-green) !important;
    font-weight: 600 !important;
    border-bottom: 2px solid var(--vrt-green) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: transparent;
    border: none;
    padding: 1.1rem 0 0 0;
}

/* Buttons */
.stButton > button {
    border-radius: var(--vrt-radius) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
}
.stButton > button[kind="primary"] {
    background: var(--vrt-green) !important;
    border: 1px solid var(--vrt-green) !important;
    color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--vrt-green-hover) !important;
    border-color: var(--vrt-green-hover) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--vrt-surface) !important;
    border: 1px solid var(--vrt-border) !important;
    color: var(--vrt-text) !important;
}

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox > div > div,
.stMultiSelect > div > div, div[data-baseweb="select"] > div {
    border-radius: var(--vrt-radius) !important;
    border-color: var(--vrt-border) !important;
    background: var(--vrt-surface) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--vrt-green) !important;
    box-shadow: 0 0 0 3px var(--vrt-green-ring) !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: var(--vrt-surface);
    border: 1px solid var(--vrt-border);
    border-radius: var(--vrt-radius);
    padding: 0.75rem 0.9rem;
}
div[data-testid="stMetric"] label {
    color: var(--vrt-muted) !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--vrt-text) !important;
    font-weight: 600 !important;
}

/* Alerts */
.stAlert {
    border-radius: var(--vrt-radius) !important;
}

/* Dataframes & expanders */
details[data-testid="stExpander"] {
    border: 1px solid var(--vrt-border);
    border-radius: var(--vrt-radius);
    background: var(--vrt-surface);
}

/* File uploader */
section[data-testid="stFileUploader"] {
    border: 1px dashed var(--vrt-border);
    border-radius: var(--vrt-radius);
    padding: 0.5rem;
    background: var(--vrt-surface);
}

/* Progress */
.stProgress > div > div {
    background: var(--vrt-green) !important;
    border-radius: 999px;
}

/* Slider accent */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: var(--vrt-green) !important;
}

/* Chips */
.vrt-chip {
    display: inline-block;
    padding: 0.22rem 0.65rem;
    margin-right: 0.35rem;
    margin-bottom: 0.3rem;
    border: 1px solid var(--vrt-border);
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--vrt-muted);
    background: var(--vrt-surface);
}

/* Sticky bar */
.vrt-sticky-top {
    position: sticky;
    top: 0;
    z-index: 5;
    background: var(--vrt-surface);
    padding: 0.65rem 0;
    border-bottom: 1px solid var(--vrt-border);
    margin-bottom: 0.65rem;
}

/* Images */
.vrt-image-panel [data-testid="stImage"] {
    max-height: 70vh;
    overflow: auto;
    border: 1px solid var(--vrt-border);
    border-radius: var(--vrt-radius);
    padding: 6px;
    background: var(--vrt-surface);
}

/* Footer */
.vrt-footer {
    text-align: center;
    color: var(--vrt-muted);
    font-size: 0.8rem;
    padding: 1.25rem 0 0.25rem;
    border-top: 1px solid var(--vrt-border);
    margin-top: 2rem;
}

/* Auth */
.vrt-auth-wrap {
    max-width: 400px;
    margin: 3rem auto 0;
    padding: 1.75rem;
    background: var(--vrt-surface);
    border: 1px solid var(--vrt-border);
    border-top: 3px solid var(--vrt-green);
    border-radius: var(--vrt-radius);
}
.vrt-auth-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--vrt-text);
    margin: 0 0 0.3rem 0;
}
.vrt-auth-subtitle {
    color: var(--vrt-muted);
    font-size: 0.875rem;
    margin: 0 0 1rem 0;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
"""


def inject_global_styles():
    """Inject application-wide CSS."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_hero():
    """Render the main application header."""
    st.markdown(
        """
        <div class="vrt-hero">
            <p class="vrt-hero-eyebrow">Visual QA</p>
            <h1 class="vrt-hero-title">🔍 Visual Regression Testing</h1>
            <p class="vrt-hero-subtitle">
                Compare staging and production across browsers and devices.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title, subtitle=None):
    """Render a consistent section header inside tabs."""
    subtitle_html = (
        f'<p class="vrt-page-subtitle">{subtitle}</p>' if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="vrt-page-header">
            <h2 class="vrt-page-title">{title}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_label(text):
    """Render a styled sidebar section label."""
    st.markdown(f'<p class="vrt-sidebar-label">{text}</p>', unsafe_allow_html=True)


def sidebar_divider():
    """Render a subtle sidebar divider."""
    st.markdown('<hr class="vrt-sidebar-divider"/>', unsafe_allow_html=True)


def render_footer():
    """Render the application footer."""
    st.markdown(
        '<div class="vrt-footer">Made with ❤️ by Roshan Karunarathna</div>',
        unsafe_allow_html=True,
    )


def status_chip(text):
    """Return HTML for a compact metadata chip."""
    return f'<span class="vrt-chip">{text}</span>'
