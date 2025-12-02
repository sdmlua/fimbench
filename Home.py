"""
Main Home page for FIM Benchmark Viewer app.
"""

import streamlit as st

from utilis.ui import inject_globalfont
from utilis.home_page import (
    apply_page_style,
    render_hero_section,
    render_about_section,
    render_explore_row,
    render_footer,
)

# Page and Global Styles
st.set_page_config(
    page_title="FIM Benchmark Viewer",
    page_icon="💧",
    layout="wide",
)

# Global font (your existing helper)
inject_globalfont(font_size_px=18, sidebar_font_size_px=20)

# Home-page layout
apply_page_style()
render_hero_section()
render_about_section()
render_explore_row()
render_footer()
