"""
This page documents how to access benchmark flood inundation data that were vizualized and are within
the benchmark database. 

Author: Supath Dhital
Date 29 November, 2025
"""
import streamlit as st
from utilis.ui import inject_globalfont
from utilis.home_page import apply_page_style

st.set_page_config(layout="wide")

# Global font styling
inject_globalfont(font_size_px=18, sidebar_font_size_px=20)
apply_page_style()

#Page title and intro
st.title("Accessing Benchmark Data")

st.markdown(
    """
This explains what **benchmark data** is within this app and how you can
access it programmatically- using Python or via the command line. So that user can seamlessly **QUERY**, **DOWNLOAD** 
and **USE** benchmark data for their own analysis. These benchmark datasets are stored on **Surface Dynamics Modeling Lab (SDML) S3 bucket**.

This dataset can be repurposed in multiple ways:
- Accessing **ONLY BENCHMARK DATA**, 
- Accessing seamlessly for [**FIM EVALUATION FRAMEWORK**](https://github.com/sdmlua/fimeval), and
- Accessing for [**FIMSERV**](https://github.com/sdmlua/FIMserv).
"""
)

st.header("Prior to using; INSTALLATION and SETUP")

st.markdown(
    """
We recommend using virtual environments to manage dependencies. 
User can use **conda**, Python’s built-in **venv**, or **uv** — pick *one* of the options below.
"""
)

st.markdown("**Option A – Using conda**")
setup_conda = """
# Create env (For example, using Python 3.11)
conda create -n fimbench python=3.11

# Activate env
conda activate fimbench
"""
st.code(setup_conda, language="bash")

st.markdown("**Option B – Using venv (built-in Python)**")
setup_venv =  """
# Create env in folder .venv
python -m fimbench .venv

# Activate on macOS / Linux
source .venv/bin/activate

# Activate on Windows (PowerShell)
.venv\\Scripts\\Activate.ps1
"""
st.code(setup_venv, language="bash")

st.markdown("**Option C – Using uv**")
st.markdown("""
            `uv` is a lightweight tool for creating and managing virtual environments and can be installed via pip:
            `pip install uv`.
            """)
setup_uv = """
# Create and activate env in one step
uv venv
source .venv/bin/activate  # macOS / Linux
.venv\\Scripts\\Activate.ps1  # Windows
"""
st.code(setup_uv, language="bash")

st.markdown(
    """
Once the environment is active, install the `fimeval` package to access the modules and dependencies needed to work with benchmark data.

```bash
pip install fimeval
```
OR
```bash
uv pip install fimeval      #This makes way much faster installation.
```
""")

python_onlybenchmark = '''
# Import the fimeval package you installed in your virtual environment
import fimeval as fe

# User inputs: either model FIM raster, boundary AOI, or both
raster_path = "./paths/to/your/model_fim.tif"
boundary_path = "./paths/to/your/boundary.gpkg"

"""
Supports multiple combinations of filters. Choose ONE pattern and set the
others to None:

a) AOI-only search (raster or boundary), optional overlap stats.
b) AOI + exact date.
c) AOI + date range (with optional download).
d) Direct filename to download (no AOI/dates) – usually once you know
   the exact benchmark FIM name.
NOTE: if no date: returns all available benchmark FIMs for the AOI.

Common parameters
-----------------
raster_path:
    Optional path to user raster (e.g., model FIM).
boundary_path:
    Optional vector AOI file (can be used with or without raster).
huc8:
    Optional HUC8 filter (mainly for US basins).
event_date:
    Exact event date (optionally with hour).
start_date, end_date:
    Inclusive date range filter.
file_name:
    Exact benchmark FIM filename from the catalog.
area:
    If True and AOI given, return % overlap and km² vs benchmark AOI.
download:
    If True, download matched rasters/GPKGs to ``out_dir``.
out_dir:
    Directory for downloads (required if ``download=True``).
"""

# a) AOI-only search (no dates, no filename)
log_aoi_only = fe.benchFIMquery(
    raster_path = raster_path,   # or None, if you only have boundary
    boundary_path = None,        # or boundary_path
    huc8 = None,
    event_date = None,
    start_date = None,
    end_date = None,
    file_name = None,
    area = True,                 # returns overlap stats vs benchmark AOI
    download = False,
    out_dir = None,
)
print("AOI-only search:", log_aoi_only)

# b) AOI + exact date
log_aoi_exact_date = fe.benchFIMquery(
    raster_path = raster_path,
    boundary_path = None,
    huc8 = None,
    event_date = "2017-05-01",   # YYYY-MM-DD or YYYY-MM-DD HH:MM
    start_date = None,
    end_date = None,
    file_name = None,
    area = True,
    download = False,
    out_dir = None,
)
print("AOI + exact date:", log_aoi_exact_date)

# c) AOI + date range (with optional download)
log_aoi_daterange = fe.benchFIMquery(
    raster_path = raster_path,
    boundary_path = None,
    huc8 = None,
    event_date = None,
    start_date = "2017-04-01",
    end_date = "2017-05-01",
    file_name = None,
    area = True,
    download = True,              # download all matches in this range
    out_dir = "./benchmark_downloads",
)
print("AOI + date range:", log_aoi_daterange)

# d) Direct filename download (no AOI, no dates)
log_by_filename = fe.benchFIMquery(
    raster_path = None,
    boundary_path = None,
    huc8 = None,
    event_date = None,
    start_date = None,
    end_date = None,
    file_name = "BENCHMARK_FIM_03020202_20170501.tif",  # example name
    area = False,               # ignored when no AOI is provided
    download = True,
    out_dir = "./benchmark_downloads",
)
print("Direct filename download:", log_by_filename)
'''

python_fimevalwithbench = '''
# continuing from previous step, if user have intend to use FIM Evaluation Framework for evaluation
import fimeval as fe
from pathlib import Path
"""
01. Case Directory Structure
------------------------
The important understanding is for multi-case evaluation, the user need to have a main directory where each subfolder is a test case containing model FIMs to be evaluated.
For single case evaluation, user can provide the path to that single case folder.

Parameters
----------
Main_dir: root folder where each subfolder is a *test case*.
Example structure:
  Main_dir/
      HUC11110203_AR/
          model_fim_1.tif
          model_fim_2.tif
      HUC11110204_TX/
          model_fim_1.tif

For instance,
Main_dir = "path/to/your/Main_dir"

02. Positioning benchmark FIMs for evaluation
------------------------------
Now from Step 01, user will access the benchmark FIM for each case. Finding each case by running QUERY is precise way. However, the automation based on
area overlap, FIM tier and resolution priority is ongoing.

and finally make a dictionary mapping each test case folder to the benchmark FIM filename obtained from Step 01.

benchmark_dict = {
    "HUC11110203_AR": "benchmark_01.tif"
    "HUC11110204_TX": "benchmark_02.tif"
}

03. Evaluation methods
------------------------------
While accessing the benchmark FIM, It will get all the benchmark boundary along with this, and use this boundary as `AOI` method for evaluation.

However, If user explicitly mention other methods like `smallest_extent` or `convex_hull`, FIMeval will use that method instead of benchmark AOI.

Evaluation methods:
"smallest_extent"  -> intersection of all FIM extents
"convex_hull"      -> convex hull around all FIM extents
"AOI"              -> use AOI shapefile as evaluation domain

method_name = "smallest_extent"  #for example

04. Other parameters
------------------------------
output_dir = "./path/to/output" # Optional: Directory to save evaluation results

Optional: user PWB (Permanent Water Bodies) dataset if not using the default one for the US.
PWB_dir = "./path/to/PWB"

target_crs = "EPSG:5070" # Optional: Target CRS (e.g., EPSG code or proj string, here for example is Albers Equal Area)

Optional: Target resolution in meters. If not provided, FIMeval can use the coarsest resolution among the inputs.
target_resolution = 10
"""

# Evaluation usage examples
# Basic evaluation using default method & default PWB
fe.EvaluateFIM(
    Main_dir=Main_dir,
    benchmark_dict=benchmark_dict,
)

# Enforce target CRS / resolution and user AOI
fe.EvaluateFIM(
    Main_dir=Main_dir,
    method_name=method_name,
    target_resolution=target_resolution,
    target_crs=target_crs,
    PWB_dir=PWB_dir,
    output_dir=output_dir,
    benchmark_dict=benchmark_dict,
)

#Other results after evaluation

#For using default benchmark FIMs, method_name is AOI
#Print contingency maps (true/false positives, etc.)
fe.PrintContingencyMap(Main_dir, method_name, output_dir) 

#Plot evaluation metrics (CSI, POD, FAR, etc.)
fe.PlotEvaluationMetrics(Main_dir, method_name, output_dir)

#FIM evaluation with building footprints
countryISO = "US"  # e.g., "US" for United States
building_footprint = "./path/to/your/building_footprint.shp"

fe.EvaluationWithBuildingFootprint(
    Main_dir,
    method_name,
    output_dir,
    country=countryISO,
    geeprojectID="supathdh",
)
#OR use local building footprint, using benchmark FIM, We are working on automating this step.
fe.EvaluationWithBuildingFootprint(
    Main_dir,
    method_name,
    output_dir,
    building_footprint=building_footprint,
)
'''

python_fimevalwithfimserve = '''
"""
Example documentation for using FIMSERV to:

1. Query and download the correct benchmark FIM (and optional HAND-FIM)
   for a given HUC8 and event date using `fim_lookup`.
2. Immediately run the FIM evaluation on the outputs using `run_evaluation`.

The typical workflow is:
- Choose a HUC8 and event datetime.
- Decide where results from `fim_lookup` should be written (`out_dir`).
- Call `fim_lookup` with `run_handfim=True` to generate OWP HAND-FIM.
- Pass the same `out_dir` as `Main_dir` into `run_evaluation`.
"""
#Install FIMSERV if not already installed

uv pip install fimserve
import fimserve as fm

"""
Query and optionally generate HAND-FIM if not generated already for a given HUC8 and event date.

This is usually the first step in a FIMSERV-based workflow.

Parameters
----------
HUCID : str
    8-digit HUC ID for the basin of interest. In this example, "10170203".
date_input : str
    Event datetime used to search for the correct benchmark FIM.
    Format should be "YYYY-MM-DD HH:MM:SS".
run_handfim : bool
    If True, FIMSERV will look for an OWP HAND-FIM for the given HUC8
    and date. If not found, it will download the necessary inputs and
    generate the HAND-FIM automatically.
date_input : str
    Event datetime used to search for the correct benchmark FIM.
    Format should be "YYYY-MM-DD HH:MM:SS" and incase of run_handfim is true this is required to generate HAND-FIM.
start_date : str, optional
    Start date for an optional date range filter when searching for
    benchmark FIMs. Format: "YYYY-MM-DD".
end_date : str, optional
    End date for an optional date range filter when searching for
    benchmark FIMs. Format: "YYYY-MM-DD".
file_name : str, optional
    If provided, FIMSERV will download this specific benchmark FIM file
    and assume it is the correct benchmark for the case. If omitted,
    the benchmark is selected based on HUCID + date filters.
out_dir : str, optional
    Directory where `fim_lookup` will save the benchmark FIM, HAND-FIM,
    and any metadata. This same directory will later be passed to
    `run_evaluation` as `Main_dir`.
"""

# Optional: Directory where benchmark FIM and HAND-FIM will be saved
out_dir = "path/to/fimserve_case_output"

#User can pass either exact date or date range
result = fm.fim_lookup(
    HUCID="10170203",
    date_input="2019-09-19 12:00:00", # Optional event datetime--> look at the exact date/hour match for the benchmark FIM
    start_date="2019-09-18",        # optional date range start
    end_date="2019-09-20",          # optional date range end
)
print("Lookup result from fim_lookup:")
print(result)

#Once the benchmark FIM is decided, generate the OWP HAND-FIM if not already present and get the benchmark FIM filename
fm.fim_lookup(
    HUCID="10170203",
    date_input="2019-09-19 12:00:00", # Optional event datetime to run HAND-FIM generation
    run_handfim=True,               # generate HAND-FIM if not already present
    file_name=specific_benchmark_fim_filename.tif,              # from fim_look up result previous step with HUCID and date
    out_dir=out_dir,    # Optional: directory to save benchmark FIM and HAND-FIM
)
    
"""
Run the FIM evaluation; once the benchmark FIM file name is decided.

Parameters
----------
Main_dir : str
    Directory containing FIM outputs to evaluate. This should be the
    same path that was used as `out_dir` in `fim_lookup`. Typically,
    it contains:
    - benchmark FIM(s) selected from the catalog
    - OWP HAND-FIM generated when `run_handfim=True`
    - any intermediate products created by FIMSERV

Notes
-----
- `output_dir` controls where evaluation results (CSV, plots, etc.)
    are saved.
- If `shapefile_path` is None, FIMSERV will use its internal AOI
    (e.g., derived from the benchmark/FIMs) for evaluation.
- Most parameters are optional and can be left as None to use
    sensible defaults.
"""
#Use the right combination of parameters as needed, it is almost similar to FIMeval EvaluateFIM function mentioned [**FIM Evaluation Framework**](https://github.com/sdmlua/fimeval).
fm.run_evaluation(
    Main_dir=Main_dir,
    output_dir="./fimserve_eval_results",
    shapefile_path=None,
    PWB_dir=None,
    building_footprint=None,
    target_crs=None,
    target_resolution=None,
    method_name=None,   # default is 'AOI' inside FIMSERV
    countryISO=None,
    geeprojectID=None,
    print_graphs=True,  # generate and save contingency maps / plots
    Evalwith_BF=False,  # set True if evaluating with building footprints
)
'''

#Expanders for each section
with st.expander("**1. Accessing ONLY BENCHMARK DATA**"):
    st.markdown(
        """
This section explains how to access benchmark flood inundation data stored in the **SDML S3** bucket  
based on user-defined filters (event date, location, etc.).  
Use the **`benchFIMquery()`** function from `fimeval`.
        """
    )
    st.code(python_onlybenchmark, language="python")

with st.expander("**2. Accessing seamlessly for FIM EVALUATION FRAMEWORK**"):
    st.markdown(
        """
This dataset can be used directly with the [**FIM Evaluation Framework**](https://github.com/sdmlua/fimeval) to  
compare model FIMs against benchmark FIMs and compute metrics. The entire evaluation workflow is automated with the 
right benchmark FIMs fetched based on user-defined AOI and event date on the step 1.

In this step to proceed, The user decide all the benchmark FIMs for all the cases to be evaluated.  
        """
    )
    st.code(python_fimevalwithbench, language="python")

with st.expander("**3. Accessing for FIMSERV**"):
    st.markdown(
        """
The [**FIM as a Service (FIMSERV)**](https://github.com/sdmlua/FIMserv) platform allows users to generate FIM using NOAA Office of Water Prediction FIM framework based on Height Above Nearest Drainage (HAND) approach. 
This can also use as a test bed for investigating the multiple components of FIM (like river slope, geometry, and so on.). For those investigation 
and even to evaluate the performance of OWP HAND FIM approach overall, the seamless evaluation makes the task much easier. This step is mainly for FIMSERV users who
want to evaluate their generated FIMs against benchmark datasets.

This FIMserv runs on HUC8 basis, so the user need to provide HUC8 and event date to query and download the benchmark FIMs.
        """
    )
    st.code(python_fimevalwithfimserve, language="python")  