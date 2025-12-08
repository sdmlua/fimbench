## **Flood Inundation Mapping Benchmark (FIMbench) Repository**

This repository provides a curated collection of benchmark **Flood Inundation Maps (FIMs)** derived from multiple high-quality sources, including remote sensing imagery, aerial observations, and high-fidelity hydrodynamic model outputs. The complete FIM inventory is organized into **four quality-based tiers** (Fig. 1), along with an additional category containing **High Water Mark (HWM)–derived flood maps**. All benchmark datasets are hosted in an **AWS S3 bucket** and can be accessed through an **open API**, enabling seamless integration into research pipelines, visualization tools, and operational workflows.

<p align="center">
  <img src="images/Flowchart.png" alt="FIM Visualizer UI" width="600"><br>
  <em>Fig. 1. Structure of FIMbench.</em>
</p>

---

### **FIM Visualizer Interface**

The FIM Visualizer provides an interactive interface to browse and explore FIM benchmark datasets across all tiers of the database.  
A preview of the interface is shown below:

The Interface of FIM Vizualizer which shows all the FIM benchmark for all Tiers of FIM database that looks like:

<a href="https://fimbench.streamlit.app/">
  <img src="images/FIM_vizualizerpage.png" alt="FIM Visualizer UI" width="900">
</a>
Each FIM location is shows in the map, zoom into gives the more detailed location. If user clicks the location, it will pops up the metadata of this benchmark and Users can directly download the FIM  in raster (.tif) format and meta data as well as all for FIM evaluation, AOI and other required information. User can directly download from the pops up or seamlessly using the framework.

Here is how it looks when user clicks each FIM location: it will show data of flood, FIM tier, resolution and all other information.
<a href="https://fimbench.streamlit.app/">
  <img src="images/Metadata_Viz.png" alt="FIM Visualizer UI" width="900">
</a>

On the left pane user can filter based on tier, date, and even activate the FIM extent. Note that the FIM extent is simplified just for rendering purpose, it doenot necessarily reflect the actual accurate delineation, So download tif raster to get actual resolution. 

Here is how it shows up when FIM extent is activated.
<a href="https://fimbench.streamlit.app/">
  <img src="images/FIM_vizualization.png" alt="FIM Visualizer UI" width="900">
</a>

This is still on development phase and live at This app is live at: https://fimbench.streamlit.app/

The final version will be released soon. 

**For more information**

Email: sdhital@crimson.ua.edu
