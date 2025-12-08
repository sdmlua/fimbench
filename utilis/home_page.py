"""
This module contains functions to render the Home page of the FIM Benchmark Viewer app.
"""
import base64
from pathlib import Path
import streamlit as st

#Styles for Home Page
def apply_page_style() -> None:
    """Inject all CSS for the Home page."""
    st.markdown(
        """
        <style>
          /* --- Page background: blue → white → blue, fixed, light --- */
          .stApp {
            background:
              /* soft blue glow top-left */
              radial-gradient(
                1200px 600px at 10% 0%,
                rgba(44,127,184,0.14) 0%,
                rgba(44,127,184,0.04) 55%,
                transparent 75%
              ),
              /* soft blue glow bottom-right */
              radial-gradient(
                1200px 600px at 90% 100%,
                rgba(44,127,184,0.16) 0%,
                rgba(44,127,184,0.05) 55%,
                transparent 75%
              ),
              /* main vertical gradient: blue → white → blue */
              linear-gradient(
                180deg,
                #e9f4fb 0%,
                #ffffff 45%,
                #e9f4fb 100%
              );
            background-attachment: fixed, fixed, fixed;
          }

          /* compact page padding */
          .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }

          /* title divider: blue→blue (kept as-is; you can tweak if you want) */
          .title-rule {
            height: 4px; border: none;
            background: linear-gradient(90deg, #2c7fb8 0%, #2c7fb8 100%);
            border-radius: 3px;
            margin: 0.35rem 0 1.0rem;
          }

          /* shared panel look for both columns */
          .panel {
            border-radius: 14px;
            border: 1px solid rgba(0,0,0,0.08);
            background: rgba(255,255,255,1);
            padding: 1.0rem 1.1rem;
            box-shadow:
              0 6px 14px rgba(44,127,184,0.08),
              0 2px 6px rgba(44,127,184,0.06);
          }

          .muted { color: #555; }

          .pill {
            display: inline-block;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            border: 1px solid rgba(0,0,0,0.08);
            font-size: 0.9rem;
            background: #fff;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
          }

          /* buttons */
          .stButton > button {
            border-radius: 12px;
            padding: 0.6rem 1.0rem;
            font-weight: 600;
            border: 1px solid rgba(44,127,184,0.25);
            background: linear-gradient(
              90deg,
              rgba(44,127,184,0.12),
              rgba(44,127,184,0.12)
            );
          }
          .stButton > button:hover {
            background: linear-gradient(
              90deg,
              rgba(44,127,184,0.18),
              rgba(44,127,184,0.18)
            );
            border-color: rgba(44,127,184,0.35);
          }

          /* Turn any st.container that contains .panel-scope into a rounded card */
          div[data-testid="stVerticalBlock"]:has(> .panel-scope) {
            border-radius: 14px;
            border: 1px solid rgba(0,0,0,0.08);
            background: rgba(255,255,255,0.96);
            padding: 1.0rem 1.1rem !important;
            box-shadow:
              0 6px 14px rgba(44,127,184,0.08),
              0 2px 6px rgba(44,127,184,0.06);
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Header section--> includes title, caption, and two-column hero
#def render_hero_section() -> None:
    # Header
   # st.title("Flood Inundation Mapping Benchmark (FIMBench) Repository")
    #st.markdown(
   # """
    #This repository contains benchmark Flood Inundation Maps (FIM)s from
   # multiple sources including remote sensing and high-fidelity model predicted maps.
    #The FIM inventory is classified into four quality-based tiers (Fig. 1) and a High Water Mark (HWM) maps.
    #The database is stored in an AWS S3 bucket with an open API.

   # **Each folder in the S3 Bucket includes:**

   # a. A flood inundation raster (GeoTIFF; .tiff)  
   # b. A vector layer illustrating the bounding box of the flood domain (Geopackage; .gpkg)  
    #c. Metadata file (JSON; .json)

   # """
#)
def render_hero_section() -> None:

    # ---------- HERO BANNER ----------
    st.markdown(
        """
        <style>
            .hero-container {
                position: relative;
                width: 100%;
                height: 260px;
                overflow: hidden;
                border-radius: 12px;
                margin-bottom: 1.5rem;
            }

            .hero-bg {
                width: 100%;
                height: 100%;
                object-fit: cover;
                filter: brightness(65%);
            }

            .hero-title {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: white;
                font-size: 32px;
                font-weight: 700;
                text-align: center;
                text-shadow: 0px 2px 6px rgba(0,0,0,0.55);
                width: 90%;
            }
        </style>

        <div class="hero-container">
            <img class="hero-bg" src="images/banner.png">
            <div class="hero-title">
                Flood Inundation Mapping Benchmark (FIMBench) Repository
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- DESCRIPTION SECTION ----------
    st.markdown(
        """
        This repository hosts **benchmark Flood Inundation Maps (FIMs)** sourced from **remote sensing imagery**, **aerial observations**, 
        and **high-fidelity hydrodynamic model predictions**.The complete FIM inventory is categorized into **four quality-based tiers** (Fig. 1),along with an 
        additional class of **High Water Mark (HWM)**–derived maps.All benchmark datasets are stored in an **AWS S3 bucket**, accessible through an **open API** 
        for seamless integration into workflows.

        ### **Each folder in the S3 bucket contains:**
        - **Flood inundation raster** (GeoTIFF: `.tif`)  
        - **Bounding box vector layer** for the flood domain (GeoPackage: `.gpkg`)  
        - **Metadata file** describing acquisition and dataset details (JSON: `.json`)
        """
    )

 # Inject CSS to perfectly center ALL st.image elements
    st.markdown(
    """
    <style>
    .stImage > img {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display image normally — Streamlit will center it automatically now
    st.image("images/Flowchart.png", width=900)

# Center caption
    st.markdown(
    "<p style='text-align: center; font-size: 14px; color: grey;'><b>Fig. 1: Structure of FIMbench</b></p>",
    unsafe_allow_html=True
)
 #   st.markdown('<hr class="title-rule">', unsafe_allow_html=True)

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
The benchmark FIM rasters are available for four tiers and one seperate class for High Water Marks generated FIM.  
**Tier 1:** This category includes FIMs derived from very high resolution NOAA Emergency Response Imegery.
 1. Flood rasters are generated by classifying raw images into two classes: **flood pixels (1)** and **non-flooded pixels (0)**, using a combination of automated and hand-labelled processing (https://storms.ngs.noaa.gov).
 2. **Spatial Resolution :** 20-50 cm.
 3. **Nodata Value:** -9999

**Tier 2:** This tier consists of FIM generated from PlanetScope Scenes integrated with a hydrologically guided algorithm.
 1. The flood rasters contains three class: **non-flooded pixels(0)**, **flooded pixels from remote sensing sensor (1)**, **flooded pixels from gap-filled algorithm (2)**.
 2. **Spatial Resolution :** 3-5 m.
 3. **Nodata Value:** -9999

**Tier 3:** : This category of FIMs contains flood rasters derived from Sentinel-1A integrated with the hydrologically guided gap-filled algorithm.
 1. Similar to Tier 2, the flood rasters contains the same three classes: **non-flooded pixels(0)**, **flooded pixels from remote sensing sensor (1)**, **flooded pixels from gap-filled algorithm (2)**.
 2. **Spatial Resolution :** 10 m.
 3. **Nodata Value:** -9999

**Tier 4:**: This tier contains FEMA’s Base Level Engineering (BLE) flood maps representing synthetic flood events.
 1. Includes HEC RAS derived FIM of 100-year and 500-year floods containing two classes: **flooded pixels (1)** and **non-flooded pixels(0)**.
 2. **Spatial Resolution:** 10 m.
 3. **Nodata Value:** -9999

**High Water Marks-FIM**: This category of FIM contains the flood maps derived from surveyed USGS high water marks.
 1. Contains two classes:  **flooded pixels (1)** and **non-flooded pixels(0)**.
 2. **Spatial Resolution:** 10 m.
 3. **Nodata Value:** -9999
"""
    )
    st.markdown('<hr class="title-rule">', unsafe_allow_html=True)


# ---- Custom CSS for pretty scrollable panels ----
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

# ---- Two equal columns ----
    col1, col2 = st.columns(2)

    with col1:  
      st.markdown(
        """
        <div class="scroll-panel">
            <div class="scroll-panel-title">
                <span class="icon">🗂️</span>
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
                <span class="icon">📊</span>
                <span> File Naming Convention </span>
            </div>
            <ul>
                The benchmark raster filenames encode key metadata, including location, data type, resolution, and the date and time of the flood event. The following naming convention is used:
                <li> <b>SS : Sensor Name<b>
                <ul>
                    <li>S1 – Sentinel-1</li>
                    <li>AI – Aerial Imagery</li>
                    <li>BLE – Base Level Engineering</li>
                </ul>
                <li> <b>SR<b>: Spatial resolution of the imagery
                <ul>
                    <li> 10m for 10 meters
                    <li> 0_5m for 50 centimeters.</li>
                </ul>
                <li> YYYYMMDD : Acquisition date 
                <ul>
                    <li> Year, month, and day of the flood event
                </ul>
                <li> TT: Time of Acquisition in UTC.
                <li> UU: Unique Identifier of the Location.
                <ul>
                    <li> Latitude and longitude (formatted as W/E + N/S) of the centroid for actual flood events.
                    <li> HUC-8 ID for BLE flood maps
                </ul>
                <li> BM: Indicates Benchmark.
                <li> Example : S1A_10m_20190527T00265_ 953144W310436N_BM.tif 

                

        </div>
        """,
        unsafe_allow_html=True,
    )

## Display image normally — Streamlit will center it automatically now
    #st.image("images/Folder.png", width=450)

# Center caption
    #st.markdown(
   # "<p style='text-align: center; font-size: 14px; color: grey;'><b>Fig. 2: Folder</b></p>",
   # unsafe_allow_html=True
#)
 #   st.markdown('<hr class="title-rule">', unsafe_allow_html=True)



#Explore row (Map + Docs) section
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

    #Logos
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
