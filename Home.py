#Main Home page for FIM Benchmark Viewer app.
import streamlit as st
from utilis.ui import inject_globalfont
from utilis.home_page import (
    apply_page_style,
    render_sticky_header,
    render_hero_section,
    render_about_section,
    render_explore_row,
    render_footer,
)

# Page config ONCE
st.set_page_config(
    page_title="FIMBench Viewer",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Fonts first
inject_globalfont(font_size_px=18, sidebar_font_size_px=22)

# Header
apply_page_style()
render_sticky_header("./images/banner.jpg")

# Content
render_hero_section()
render_about_section()
render_explore_row()
render_footer()
