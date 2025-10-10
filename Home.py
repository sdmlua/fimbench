import streamlit as st

# Page and Global Styles
st.set_page_config(page_title="FIM Benchmark Viewer", page_icon="🌊", layout="wide")

from utilis.ui import inject_globalfont
inject_globalfont(font_size_px=18, sidebar_font_size_px=20)

st.markdown(
    """
    <style>
      /* --- Page background: blue → white → crimson, fixed --- */
      .stApp {
        background:
          radial-gradient(1200px 600px at 10% 0%, rgba(44,127,184,0.18) 0%, rgba(44,127,184,0.06) 55%, transparent 75%),
          radial-gradient(1200px 600px at 90% 100%, rgba(166,15,45,0.18) 0%, rgba(166,15,45,0.06) 55%, transparent 75%),
          linear-gradient(180deg, #e9f4fb 0%, #ffffff 45%, #fff4f6 100%);
        background-attachment: fixed, fixed, fixed;
      }

      /* compact page padding */
      .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }

      /* title divider: blue→crimson */
      .title-rule {
        height: 4px; border: none;
        background: linear-gradient(90deg, #2c7fb8 0%, #a60f2d 100%);
        border-radius: 3px;
        margin: 0.35rem 0 1.0rem;
      }

      /* shared panel look for both columns */
      .panel {
        border-radius: 14px;
        border: 1px solid rgba(0,0,0,0.08);
        background: rgba(255,255,255,0.92);
        padding: 1.0rem 1.1rem;
        box-shadow:
          0 6px 14px rgba(44,127,184,0.08),
          0 2px 6px rgba(166,15,45,0.06);
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
        background: linear-gradient(90deg, rgba(44,127,184,0.12), rgba(166,15,45,0.12));
      }
      .stButton > button:hover {
        background: linear-gradient(90deg, rgba(44,127,184,0.18), rgba(166,15,45,0.18));
        border-color: rgba(166,15,45,0.35);
      }
    </style>
    """,
    unsafe_allow_html=True
)

# Header
st.title("FIM Benchmark Viewer")
st.caption("Browse, inspect and seamless integrate benchmark Flood Inundation Maps (FIMs) into your workflow to evaluate flood map predictions.")
st.markdown('<hr class="title-rule">', unsafe_allow_html=True)

# Two-column hero (both boxed equally)
left, right = st.columns([1.6, 1.0], vertical_alignment="top")

with left:
    st.markdown(
        """
        <div class="panel">
          <h3 style="margin-top:0;margin-bottom:0.25rem;">
            Flood Inundation Mapping Predictions Evaluation Framework (FIMeval)
          </h3>
          <div class="muted" style="margin-top:0.25rem;">
            Powerful tools to visualize, benchmark, and evaluate flood inundation maps (FIMs)
            for hydrologic modeling, preparedness, and response.
          </div>
          <div style="margin-top:0.6rem;">
            <span class="pill">CSI</span>
            <span class="pill">POD</span>
            <span class="pill">FAR</span>
            <span class="pill">F1</span>
            <span class="pill">Accuracy</span>
            <span class="pill">Buildings overlay</span>
            <span class="pill">AOI & waterbody masking</span>
            <span class="pill">Seamless Benchmark FIM Integration</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
        <div class="panel">
          <b>What FIMeval does</b>
          <ul style="margin-top: 0.5rem;">
            <li>Compares predicted FIMs to benchmark datasets</li>
            <li>Computes evaluation metrics automatically</li>
            <li>Integrates building footprint impacts (optional)</li>
            <li>Supports AOI boundaries + permanent waterbody masks</li>
            <li>Connects to SDML’s benchmark FIM repository seamlessly</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
st.write("")
st.markdown("<hr style='border:0.5px solid rgba(44,127,184,0.35); margin:1rem 0;' />", unsafe_allow_html=True)
st.write("")

# About section
st.subheader("About the FIM Predictions Evaluation Framework")
st.markdown(
    """
Evaluating flood maps is essential—but doing it by hand is tedious and error-prone.  
**FIMeval** streamlines the workflow so you can focus on insights, not mechanics.
"""
)

st.write("")
st.markdown("<hr style='border:0.5px solid rgba(44,127,184,0.35); margin:1rem 0;' />", unsafe_allow_html=True)
st.write("")

# Styles for container-panels
st.markdown("""
<style>
/* Turn any st.container that contains .panel-scope into a rounded card */
div[data-testid="stVerticalBlock"]:has(> .panel-scope) {
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.92);
  padding: 1.0rem 1.1rem !important;
  box-shadow: 0 6px 14px rgba(44,127,184,0.08), 0 2px 6px rgba(166,15,45,0.06);
}
</style>
""", unsafe_allow_html=True)

# Explore row
ex_left, ex_right = st.columns([1.6, 1.0], vertical_alignment="top")

with ex_left:
    with st.container():
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
            "Read the step-by-step guide and examples for working with benchmark FIMs and the **fimeval** toolkit."
        )
        if st.button("Open Documentation", key="open_docs"):
            st.switch_page("pages/2_Documentation.py")
    
st.write("")
st.markdown("<hr style='border:0.5px solid rgba(44,127,184,0.35); margin:1rem 0;' />", unsafe_allow_html=True)
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
st.markdown("<hr style='border:0.5px solid rgba(44,127,184,0.35); margin:1rem 0;' />", unsafe_allow_html=True)
st.write("")

# Footer CSS
col_left, col_right = st.columns(2)

with col_left:
    l1, l2 = st.columns([0.18, 0.82], vertical_alignment="center")
    with l1:
        st.image("images/SDML_logo.png", width=80)
    with l2:
        st.markdown(
            """
            <div class="footer-container">
              <b>Surface Dynamics Modeling Lab (SDML)</b><br/>
              Department of Geography & the Environment, The University of Alabama<br/>
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_right:
    r1, r2 = st.columns([0.18, 0.82], vertical_alignment="center")
    with r1:
        st.image("images/ciroh_logo.png", width=80)
    with r2:
        st.markdown(
            """
            <div class="footer-container">
              Funding for this project was provided by the National Oceanic & Atmospheric Administration (NOAA),
              awarded to the Cooperative Institute for Research to Operations in Hydrology (CIROH) through the NOAA
              Cooperative Agreement with The University of Alabama.
            </div>
            """,
            unsafe_allow_html=True,
        )
