import streamlit as st

"""
Utility functions for Streamlit UI customization.
"""


def inject_globalfont(font_size_px=16, sidebar_font_size_px=20, sidebar_width_px=340):
    st.markdown(
        f"""
        <style>
        /* Global font */
        html, body, [class*="css"] {{
            font-family: "Arial Narrow", Arial, sans-serif !important;
            font-size: {font_size_px}px;
        }}

        /* Sidebar nav items */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li a * ,
        section[data-testid="stSidebar"] nav li a,
        section[data-testid="stSidebar"] nav li a * {{
            font-family: "Arial Narrow", Arial, sans-serif !important;
            font-size: {sidebar_font_size_px}px !important;
            font-weight: 800 !important;
            line-height: 1.2 !important;
            color: #1f2937 !important;
        }}

        /* Sidebar hover & active */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li a:hover *,
        section[data-testid="stSidebar"] nav li a:hover * {{
            color: #2563eb !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li a[aria-current="page"] *,
        section[data-testid="stSidebar"] nav li a[aria-current="page"] * {{
            color: #1d4ed8 !important;
        }}

        /* Control header sizes */
        h1 {{
            font-size: 28px !important;   /* title */
        }}
        h2 {{
            font-size: 22px !important;   /* header */
        }}
        h3 {{
            font-size: 18px !important;   /* subheader */
        }}

        /* Footer captions smaller */
        .stCaption, footer, .st-emotion-cache-183lzff p {{
            font-size: 14px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
