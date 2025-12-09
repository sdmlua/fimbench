"""
Main Home page for FIM Benchmark Viewer app.
"""

import streamlit as st
from utilis.ui import inject_globalfont
from utilis.home_page import (
    apply_page_style,
    render_sticky_header,  # Import the new function
    render_hero_section,
    render_about_section,
    render_explore_row,
    render_footer,
)

# Page Configuration
st.set_page_config(
    page_title="FIMBench Viewer",
    page_icon="💧",
    layout="wide",
)

inject_globalfont(font_size_px=18, sidebar_font_size_px=22)

# At the very beginning of your page (after imports)
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# Then in your main code, right after render_sticky_header():
render_sticky_header()

# Add this ONE line to push content down cleanly
st.markdown(
    f"""
    <style>
        .main > .block-container {{
            padding-top: calc(var(--banner-height) + 1.5rem) !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Apply Styles
apply_page_style()

# Render Sticky Header
render_sticky_header("./images/banner.jpg", height_px=120)

# Render Page Sections
render_hero_section()
render_about_section()
render_explore_row()
render_footer()
