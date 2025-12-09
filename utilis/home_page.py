"""
This module contains functions to render the Home page and shared UI elements
like the sticky header.
"""

import base64
from pathlib import Path
import streamlit as st

# Font Awesome
st.markdown(
    """
    <link rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    """,
    unsafe_allow_html=True,
)


# Utility Functions
def image_to_base64_raw(image_path: str) -> str:
    """Return base64 of file bytes (no re-encode -> no quality change)."""
    data = Path(image_path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def guess_mime_from_suffix(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }.get(ext, "application/octet-stream")


def render_img_html(image_path: str, alt: str = "", max_width: str = "100%"):
    """Helper to render standard inline images."""
    b64 = image_to_base64_raw(image_path)
    mime = guess_mime_from_suffix(image_path)
    st.markdown(
        f"""
        <div style="line-height:0; overflow:visible; margin:0; padding:0;">
            <img src="data:{mime};base64,{b64}" alt="{alt}"
            style="width:{max_width}; height:auto; display:block; max-width:none; image-rendering:auto;" />
        </div>
        """,
        unsafe_allow_html=True,
    )


# Sticky Header Function: height from aspect ratio + sidebar width
def render_sticky_header(image_path: str = "./images/banner.jpg", height_px: int = 120):
    try:
        b64 = image_to_base64_raw(image_path)
        mime = guess_mime_from_suffix(image_path)
    except FileNotFoundError:
        st.error(f"Banner image not found at: {image_path}")
        return

    st.markdown(
        f"""
    <style>
        /* Sticky banner */
        .sticky-header-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: var(--banner-height);
            z-index: 99999;
            background-color: white;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .sticky-header-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            display: block;
        }}

        /* NEW 2025+ way: push content down without huge gap */
        [data-testid="stAppViewContainer"] > .main > .block-container {{
            padding-top: calc(var(--banner-height) + 1rem) !important;  /* reduced offset */
        }}

        /* Alternative (even cleaner) – use Streamlit's own top padding */
        .main > div[data-testid="stVerticalBlock"]:first-child {{
            padding-top: calc(var(--banner-height) + 1rem) !important;
        }}

        /* Hide default header */
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
            z-index: 100000;
        }}

        :root {{
            --banner-height: clamp(80px, 12vh, 160px);
        }}
    </style>
    <div class="sticky-header-container">
        <img class="sticky-header-img"
            src="data:{mime};base64,{b64}"
            alt="Sticky Banner">
    </div>
    """,
        unsafe_allow_html=True,
    )


# Standard Page Styles
def apply_page_style() -> None:
    """Inject all CSS for the Home page (Backgrounds, Panels, etc.)."""
    st.markdown(
        """
        <style>
        /* --- Page background --- */
        .stApp {
            background:
                radial-gradient(1200px 600px at 10% 0%, rgba(44,127,184,0.14) 0%, rgba(44,127,184,0.04) 55%, transparent 75%),
                radial-gradient(1200px 600px at 90% 100%, rgba(44,127,184,0.16) 0%, rgba(44,127,184,0.05) 55%, transparent 75%),
                linear-gradient(180deg, #e9f4fb 0%, #ffffff 45%, #e9f4fb 100%);
            background-attachment: fixed, fixed, fixed;
        }
        
        /* Shared Panel Styling */
        .title-rule {
            height: 4px; border: none;
            background: linear-gradient(90deg, #2c7fb8 0%, #2c7fb8 100%);
            border-radius: 3px;
            margin: 0.35rem 0 1.0rem;
        }
        .panel {
            border-radius: 14px;
            border: 1px solid rgba(0,0,0,0.08);
            background: rgba(255,255,255,1);
            padding: 1.0rem 1.1rem;
            box-shadow: 0 6px 14px rgba(44,127,184,0.08), 0 2px 6px rgba(44,127,184,0.06);
        }
        /* Scoped Panel */
        div[data-testid="stVerticalBlock"]:has(> .panel-scope) {
            border-radius: 14px;
            border: 1px solid rgba(0,0,0,0.08);
            background: rgba(255,255,255,0.96);
            padding: 1.0rem 1.1rem !important;
            box-shadow: 0 6px 14px rgba(44,127,184,0.08), 0 2px 6px rgba(44,127,184,0.06);
        }
        /* Buttons */
        .stButton > button {
            border-radius: 12px;
            border: 1px solid rgba(44,127,184,0.25);
            background: linear-gradient(90deg, rgba(44,127,184,0.12), rgba(44,127,184,0.12));
        }
        .stButton > button:hover {
            background: linear-gradient(90deg, rgba(44,127,184,0.18), rgba(44,127,184,0.18));
            border-color: rgba(44,127,184,0.35);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Content Sections
def render_hero_section():
    st.markdown("## Flood Inundation Mapping Benchmark (FIMBench) Repository")
    st.markdown(
        """
        This repository hosts **benchmark Flood Inundation Maps (FIMs)** sourced from **remote sensing imagery**, **aerial observations**, 
        and **high-fidelity hydrodynamic model predictions**. The complete FIM inventory is categorized into **four quality-based tiers** (Fig. 1), along with an 
        additional class of **High Water Mark (HWM)**–derived maps. All benchmark datasets are stored in an **AWS S3 bucket**, accessible through an **open API** for seamless integration into workflows.
        
        ### **Each folder in the S3 bucket contains:**
        - **Flood inundation raster** (GeoTIFF: `.tif`) 
        - **Bounding box vector layer** for the flood domain (GeoPackage: `.gpkg`) 
        - **Metadata file** describing acquisition and dataset details (JSON: `.json`)
        """
    )
    # Flowchart Image
    render_img_html("images/Flowchart.png", alt="FIMbench flowchart", max_width="900px")
    st.markdown(
        "<p style='text-align: center; font-size: 14px; color: grey;'><b>Fig. 1: Structure of FIMbench</b></p>",
        unsafe_allow_html=True,
    )


# About FIMbench Data Sources
def render_about_section() -> None:
    """Middle 'About' section."""
    st.write("")
    st.markdown(
        "<hr style='border:0.5px solid rgba(44,127,184,0.35); margin:1rem 0;' />",
        unsafe_allow_html=True,
    )
    st.write("")

    st.subheader("FIMbench Data Sources and Content")
    st.markdown(
        """
    The benchmark FIM rasters are available for four tiers and one separate class for High Water Marks–generated FIM.  

    **Tier 1:** This category includes FIMs derived from very high resolution NOAA Emergency Response Imagery.
    <ul style="margin-left: 1.5rem; margin-bottom: 0.75rem;">
    <li>Flood rasters are generated by classifying raw images into two classes: <b>flood pixels (1)</b> and <b>non-flooded pixels (0)</b>, using a combination of automated and hand-labelled processing (<a href="https://storms.ngs.noaa.gov" target="_blank">storms.ngs.noaa.gov</a>).</li>
    <li><b>Spatial Resolution:</b> 20–50 cm.</li>
    <li><b>NoData Value:</b> -9999.</li>
    </ul>

    **Tier 2:** This tier consists of FIMs generated from PlanetScope scenes integrated with a hydrologically guided algorithm.
    <ul style="margin-left: 1.5rem; margin-bottom: 0.75rem;">
    <li>The flood rasters contain three classes: <b>non-flooded pixels (0)</b>, <b>flooded pixels from remote-sensing sensor (1)</b>, <b>flooded pixels from gap-filled algorithm (2)</b>.</li>
    <li><b>Spatial Resolution:</b> 3–5 m.</li>
    <li><b>NoData Value:</b> -9999.</li>
    </ul>

    **Tier 3:** This category of FIMs contains flood rasters derived from Sentinel-1A integrated with the hydrologically guided gap-filled algorithm.
    <ul style="margin-left: 1.5rem; margin-bottom: 0.75rem;">
    <li>Similar to Tier 2, the flood rasters contain the same three classes: <b>non-flooded pixels (0)</b>, <b>flooded pixels from remote-sensing sensor (1)</b>, <b>flooded pixels from gap-filled algorithm (2)</b>.</li>
    <li><b>Spatial Resolution:</b> 10 m.</li>
    <li><b>NoData Value:</b> -9999.</li>
    </ul>

    **Tier 4:** This tier contains FEMA’s Base Level Engineering (BLE) flood maps representing synthetic flood events.
    <ul style="margin-left: 1.5rem; margin-bottom: 0.75rem;">
    <li>Includes HEC-RAS-derived FIMs of 100-year and 500-year floods containing two classes: <b>flooded pixels (1)</b> and <b>non-flooded pixels (0)</b>.</li>
    <li><b>Spatial Resolution:</b> 10 m.</li>
    <li><b>NoData Value:</b> -9999.</li>
    </ul>

    **High Water Marks – FIM:** This category of FIM contains the flood maps derived from surveyed USGS high water marks.
    <ul style="margin-left: 1.5rem; margin-bottom: 0.75rem;">
    <li>Contains two classes: <b>flooded pixels (1)</b> and <b>non-flooded pixels (0)</b>.</li>
    <li><b>Spatial Resolution:</b> 10 m.</li>
    <li><b>NoData Value:</b> -9999.</li>
    </ul>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="title-rule">', unsafe_allow_html=True)

    # Custom CSS for pretty scrollable panels
    st.markdown(
        """
    <style>
    .scroll-panel {
        height: 260px;
        padding: 1rem 1.1rem;
        border-radius: 14px;
        background: #ffffff;
        border: 1px solid rgba(180, 200, 220, 0.6);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
        overflow-y: auto;
        font-size: 0.92rem;
        line-height: 1.45;
    }

    .scroll-panel-title {
        font-weight: 600;
        font-size: 1.05rem;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
        color: #0f172a;
    }

    .scroll-panel-title span.icon {
        font-size: 1.1rem;
    }

    .scroll-panel ul {
        padding-left: 1.1rem;
        margin: 0;
    }

    .scroll-panel li {
        margin-bottom: 0.35rem;
    }

    /* Pretty scrollbar (WebKit browsers) */
    .scroll-panel::-webkit-scrollbar {
        width: 6px;
    }
    .scroll-panel::-webkit-scrollbar-track {
        background: transparent;
    }
    .scroll-panel::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.9);
        border-radius: 999px;
    }
    .scroll-panel::-webkit-scrollbar-thumb:hover {
        background: rgba(100, 116, 139, 1);
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Two columns for Folder Structure and Naming Convention
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        <div class="scroll-panel">
            <div class="scroll-panel-title">
                <span class="icon"><i class="fa-solid fa-folder" style="color: #d58400;"></i></span>
                <span> FIMbench Folder Structure </span>
            </div>
            <ul>
                <li>The folder structure in the database S3 Bucket is organized by quality levels labelled as Tier 1, Tier 2, Tier 3, Tier 4 and HWM-FIM (Fig. 2).</li>
                <li>Under each Level folder, there are subfolders consisting of flood maps for different case studies.</li>
                <li>The naming convention of these subfolders is based on the date of the flood event, followed by the coordinates of the centroid of the flood map (e.g. 20161009T150712_0775815W352133N).</li>
            </ul>
            
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="scroll-panel">
            <div class="scroll-panel-title">
                <span class="icon"><i class="fa-solid fa-book" style="color: #ff8647;"></i></span>
                <span> File Naming Convention </span>
            </div>
            <ul>
                The benchmark raster filenames encode key metadata, including location, data type, resolution, and the date and time of the flood event. The following naming convention is used:
                <li> <b>SS</b>: Sensor Name
                <ul>
                    <li>S1 – Sentinel-1</li>
                    <li>AI – Aerial Imagery</li>
                    <li>BLE – Base Level Engineering</li>
                </ul>
                <li> <b>SR</b>: Spatial resolution of the imagery
                <ul>
                    <li> 10m for 10 meters</li>
                    <li> 0_5m for 50 centimeters.</li>
                </ul>
                <li> <b>YYYYMMDD</b>: Acquisition date 
                <ul>
                    <li>Year, month, and day of the flood event</li>
                </ul>
                <li> <b>TT</b>: Time of acquisition in UTC.</li>
                <li> <b>UU</b>: Unique Identifier of the location.
                <ul>
                    <li>Latitude and longitude (formatted as W/E + N/S) of the centroid for actual flood events.</li>
                    <li>HUC-8 ID for BLE flood maps</li>
                </ul>
                <li> <b>BM</b>: Indicates Benchmark.</li>
                <li> <b>Example</b>: S1A_10m_20190527T002655_953144W310436N_BM.tif</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )


# Explore row (Map + Docs) section
def render_explore_row() -> None:
    """Row with 'Open Interactive Viewer' and 'Open Documentation' cards."""
    st.write("")
    st.markdown(
        "<hr style='border:0.5px solid rgba(44,127,184,0.35); margin:1rem 0;' />",
        unsafe_allow_html=True,
    )
    st.write("")

    ex_left, ex_right = st.columns([1.6, 1.0], vertical_alignment="top")

    with ex_left:
        with st.container():
            # panel style is applied by CSS using .panel-scope
            st.markdown('<div class="panel-scope"></div>', unsafe_allow_html=True)

            st.markdown("**Explore the Benchmark FIMs**")
            st.markdown(
                "Open the **Interactive Map** to browse available benchmark FIMs on multiple basemaps, "
                "overlay boundaries, and inspect results interactively."
            )
            if st.button("Open Interactive Viewer", key="open_viewer_explore"):
                st.switch_page("pages/1_Interactive Map.py")

    with ex_right:
        with st.container():
            st.markdown('<div class="panel-scope"></div>', unsafe_allow_html=True)

            st.markdown("**Get to know how to use the data seamlessly**")
            st.markdown(
                "Read the step-by-step guide and examples for working with benchmark FIMs "
                "and the **fimeval** toolkit."
            )
            if st.button("Open Documentation", key="open_docs"):
                st.switch_page("pages/2_Documentation.py")


def _img_to_base64(path: str) -> str:
    """Read an image file and return a base64 data URL fragment."""
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def render_footer() -> None:
    """Contribute section + logos footer."""
    st.write("")
    st.markdown(
        "<hr style='border:0.5px solid rgba(44,127,184,0.35); margin:1rem 0;' />",
        unsafe_allow_html=True,
    )
    st.write("")

    # GitHub / Docs
    st.subheader("Contribute & Learn More")
    st.markdown(
        """
This FIM benchmark viewer is built to explore the available benchmark FIM and is seamlessly integrated with the open-source **[fimeval](https://github.com/sdmlua/fimeval)** framework by SDML.  
More detailed information about installation, documentation, and contribution, see the **FIMeval GitHub Repo**: https://github.com/sdmlua/fimeval
"""
    )
    st.markdown(
        """
        <div class="footer-container">
          <b>For More Information:</b><br/>
          Contact: 
          <a href="https://geography.ua.edu/people/sagy-cohen/" target="_blank">Sagy Cohen</a> |
          <a href="mailto:sdhital@crimson.ua.edu">Supath Dhital</a> |
          <a href="mailto:ddevi@ua.edu">Dipsikha Devi</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown(
        "<hr style='border:0.5px solid rgba(44,127,184,0.35); margin:1rem 0;' />",
        unsafe_allow_html=True,
    )
    st.write("")

    # Logos
    sdml_b64 = _img_to_base64("images/SDML_logo.png")
    ciroh_b64 = _img_to_base64("images/ciroh_logo.png")

    st.markdown(
        f"""
        <style>
        .footer-logos-row {{
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 16px;               
          margin-top: 0.5rem;
          margin-bottom: 0.5rem;
        }}
        .footer-logos-row img {{
          max-height: 100px;         
          height: auto;
          width: auto;
          border-radius: 0 !important; 
          image-rendering: auto;
        }}
        </style>

        <div class="footer-logos-row">
          <img src="data:image/png;base64,{sdml_b64}" alt="SDML logo" />
          <img src="data:image/png;base64,{ciroh_b64}" alt="CIROH logo" />
        </div>
        """,
        unsafe_allow_html=True,
    )
