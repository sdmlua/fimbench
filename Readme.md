## **Flood Inundation Mapping Benchmark (FIMbench) Repository**

This repository provides a curated collection of benchmark **Flood Inundation Maps (FIMs)** derived from multiple high-quality sources, including remote sensing imagery, aerial observations, and high-fidelity hydrodynamic model outputs. The complete FIM inventory is organized into **four quality-based tiers** (Fig. 1), along with an additional category containing **High Water Mark (HWM)–derived flood maps**. All benchmark datasets are hosted in an **AWS S3 bucket** and can be accessed through an **open API**, enabling seamless integration into research pipelines, visualization tools, and operational workflows.

<p align="center">
  <img src="images/Flowchart.png" alt="FIM Visualizer UI" width="600"><br>
  <em>Fig. 1. Structure of FIMbench.</em>
</p>

---

### **FIM Visualizer Interface**

The FIM Visualizer offers an interactive platform for browsing and exploring benchmark FIM datasets across all quality tiers.👉 **Click here to open the FIMbench Visualizer**
A preview of the interface is shown below:

<p align="center">
  <a href="https://fimbench.streamlit.app/">
    <img src="images/FIM_vizualizerpage.png" alt="FIM Visualizer UI" width="600">
  </a>
  <br>
  <em>Fig. 2. FIMbench Visualizer Interface.</em>
</p>

### **Downloading Data from FIMbench Visualizer**

Each FIM location is displayed on the map, and zooming in reveals finer spatial detail. When a user clicks on a location, a pop-up window appears containing the full metadata for that benchmark. From this panel, users can directly download the flood inundation raster (.tif), metadata files, AOI layers, and other resources required for FIM evaluation. Downloads can be initiated either through the pop-up itself or seamlessly through the framework.
Below is an example of the information displayed when a user selects a FIM location, including flood details, FIM tier, spatial resolution, and additional metadata:

<p align="center">
  <a href="https://fimbench.streamlit.app/">
    <img src="images/Metadata_Viz.png" alt="FIM Visualizer UI" width="600">
  </a>
  <br>
  <em>Fig. 3. Downloading FIM from the FIMbench Visualizer Interface.</em>
</p>

On the left pane user can filter based on tier, date, and even activate the FIM extent. Note that the FIM extent is simplified just for rendering purpose, it doenot necessarily reflect the actual accurate delineation, So download tif raster to get actual resolution. 

Here is how it shows up when FIM extent is activated.
<a href="https://fimbench.streamlit.app/">
  <img src="images/FIM_vizualization.png" alt="FIM Visualizer UI" width="900">
</a>

This is still on development phase and live at This app is live at: https://fimbench.streamlit.app/

The final version will be released soon. 

**For more information**

Email: sdhital@crimson.ua.edu
