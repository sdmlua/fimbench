<div align="center">
  <img src="assets/fimbench-logo.png" alt="FIMbench" width="150" />
  <h2>FIMbench — an Extensive Benchmark Flood Inundation Mapping Database</h2>
  <p>
    <a href="https://github.com/sdmlua/fimbench/releases"><img src="https://img.shields.io/github/v/release/sdmlua/fimbench?include_prereleases" alt="Release" /></a>
    <a href="https://github.com/sdmlua/fimbench/issues"><img src="https://img.shields.io/github/issues/sdmlua/fimbench" alt="Issues" /></a>
    <a href="https://opensource.org/licenses/GPL-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License: GPL v3" /></a><br>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" /></a>
    <a href="https://tethys.ciroh.org/apps/fimbench-gui/"><img src="https://img.shields.io/badge/GUI-live-brightgreen.svg" alt="GUI live" /></a><br>
    <a href="https://pypi.org/project/fimbench/"><img src="https://badge.fury.io/py/fimbench.svg?icon=si%3Apython" alt="PyPI version" /></a>
    <a href="https://pepy.tech/projects/fimbench"><img src="https://static.pepy.tech/badge/fimbench" alt="PyPI Downloads" /></a>
  </p>
</div>

### **FIMbench - an Extensive Benchmark Flood Inundation Mapping Database**
<hr style="border: 1px solid black; margin: 0;">

| | |
| --- | --- |
| <a href="https://sdml.ua.edu"><img src="assets/sdml-logo.png" alt="SDML Logo" width="400"></a> | FIMbench is an **extensive, multi-tier, multi-source benchmark Flood Inundation Mapping (FIM) database** and the toolkit that powers it. It brings benchmark flood maps from many sources into one **standardized**, **programmatically queryable** database, and connects **seamlessly to evaluation frameworks such as [FIMeval](https://github.com/sdmlua)** so model predictions can be benchmarked against as many reliable reference maps as possible. It is developed under the Surface Dynamics Modeling Lab (SDML) at The University of Alabama as part of a project funded by the Cooperative Institute for Research to Operations in Hydrology (CIROH). |

### **Background**
<hr style="border: 1px solid black; margin: 0;">

Reliable evaluation of flood inundation models depends on having reliable benchmark
maps to evaluate against — and those maps are scattered across many sources, formats,
resolutions, and levels of confidence. **FIMbench** consolidates them into a single
**extensive benchmark database** that is **multi-source** (remote-sensing-derived maps,
high-resolution airborne imagery, machine-learning-derived maps, and more) and
**multi-tier** (organized by source, confidence, and resolution), so users can reason
about *which* benchmark to trust for a given location and event.

Beyond storing data, FIMbench is built to be **used programmatically**. The `fimbench`
Python package lets you **query** the database to discover what benchmark maps exist for
a region or event, **access and download** the matching assets, and feed them straight
into an evaluation workflow. This makes FIMbench **seamlessly connected to evaluation
frameworks such as [FIMeval](https://github.com/sdmlua)** — the standardized maps it
serves are evaluation-ready, enabling robust benchmarking of model predictions against
**as many reference maps as possible**, automatically and at scale.

In one toolkit, FIMbench **standardizes** raw benchmark flood maps to a common format,
builds the **tiles and web content** consumed by the GUI, and **publishes** everything
into the database. The published data is served through the
**[FIM Database](https://sdmlab.ciroh.org/index.html#FIM_Database/)** and explored
interactively in the live **[FIMbench GUI](https://tethys.ciroh.org/apps/fimbench-gui/)**.

### How the data is created

<div align="center">
  <img src="assets/fimbench-flowchart.png" alt="FIMbench data creation flowchart" width="90%" />
</div>

## Architecture

`fimbench` is deployed as Python library organised into four groups that follow
the FIM data lifecycle- content is **created** in one group and **pushed out** by
another, with a single shared S3 access layer.

<div align="center">
  <img src="assets/fimbench-arct.png" alt="FIMbench architecture" width="90%" />
</div>

The codebase is as follows:
```
fimbench/
├── docs/                        # documentation + per-module notebooks
├── assets/                      # logos, diagrams, screenshots
├── src/fimbench/
│   ├── processing_floodmap/     # raw flood map -> standardized, DB-compatible artifact
│   ├── webcontent_utils/        # CREATE catalog, tiles & web content
│   ├── query/                   # QUERY availability + download assets
│   └── publish/                 # PUSH content to S3 / ArcGIS Online (incl. the S3 layer)
└── tests/
```

> For the detailed architecture — group responsibilities, dependency direction, and
> design principles — see **[./docs/architecture.md](./docs/architecture.md)**.

## FIMbench in the web- GUI

Alongside programmatic access, the benchmark database can be explored visually through
the live FIMbench GUI, built on the CIROH Tethys Platform. Explore it at
**[tethys.ciroh.org/apps/fimbench-gui](https://tethys.ciroh.org/apps/fimbench-gui/)**
and read more in the **[GUI docs](https://tethys.ciroh.org/apps/fimbench-gui/docs)**.

<div align="center">
  <img src="assets/fimbench-intropage.png" alt="FIMbench GUI — intro page" width="75%" />
</div>

The **landing page** introduces the database and its scope, giving newcomers a quick
sense of what benchmark flood maps are available and how the collection is organized.

<div align="center">
  <img src="assets/fimbench-interactivemapwithfilters.png" alt="FIMbench GUI — interactive map with filters" width="75%" />
</div>

The **interactive map** lets users browse the full extent of the database and **filter**
benchmark maps by source, location, and event — making it easy to find the right
reference map across the multi-source, multi-tier collection.

<div align="center">
  <img src="assets/fimbench-floodextentvizz.png" alt="FIMbench GUI — flood extent visualization" width="75%" />
</div>

Selecting a benchmark renders its **flood extent visualization** on the map, so the
inundated area can be inspected in detail and compared against the underlying terrain
and surrounding layers.

<div align="center">
  <img src="assets/fimbench-documentationpage.png" alt="FIMbench GUI — documentation page" width="75%" />
</div>

The built-in **documentation page** explains the data sources, methodology, and how to
work with the database — both interactively through the GUI and programmatically with
the `fimbench` package.

## Usage

Install and set up the package by following **[docs/getting-started.md](docs/getting-started.md)**.

Each lifecycle stage has a runnable notebook walkthrough under `docs/`:

| Notebook | Stage |
| --- | --- |
| [`fimbench_processingfloodmap.ipynb`](docs/fimbench_processingfloodmap.ipynb) | Standardize a raw flood map into a DB-compatible artifact |
| [`fimbench_webcontent.ipynb`](docs/fimbench_webcontent.ipynb) | Build the catalog, make tiles & web content |
| [`fimbench_query.ipynb`](docs/fimbench_query.ipynb) | Query availability and download assets |
| [`fimbench_publish.ipynb`](docs/fimbench_publish.ipynb) | Push catalog/tiles to S3 and extents to ArcGIS Online |

## Citing this tool

1. Cohen, S., Baruah, A., Nikrou, P., Tian, D., & Liu, H. (2025). Toward robust evaluations of flood inundation predictions using remote sensing derived benchmark maps. *Water Resources Research*, 61(8), e2024WR039574.
2. Munasinghe, D., Cohen, S., Tian, D., Liu, H., Baruah, A., and Devi, D. (2025). A Database of Flood Maps using high-resolution Airborne Imagery and Machine Learning Models. In: *CIROH Developers' Conference*, May 28–30, 2025.
3. Devi, D., Dhital, S., Munasinghe, D., Cohen, S., Baruah, A., Chen, Y., ... & Pruitt, C. (2025). A Framework for the Evaluation of Flood Inundation Predictions Over Extensive Benchmark Databases.
4. Tian, D., Liu, H., Wang, L., Cohen, S., Thapa, P. (2024). Enhancing satellite image-derived flood maps with hydrologically guided region growing method and high-resolution DEMs. *Chapman Conference on Remote Sensing of the Water Cycle*.

## Contributing

Contributions are welcome- see **[CONTRIBUTING.md](CONTRIBUTING.md)** for how to set
up a development environment, run the tests and linters, and submit changes.

### **Acknowledgements**
<hr style="border: 1px solid black; margin: 0;">

| | |
| --- | --- |
| <a href="https://ciroh.ua.edu/"><img src="assets/CIROH-logo.jpg" alt="CIROH Logo" width="400"></a> | Funding for this project was provided by the National Oceanic & Atmospheric Administration (NOAA), awarded to the Cooperative Institute for Research to Operations in Hydrology (CIROH) through the NOAA Cooperative Agreement with The University of Alabama. |
| | We would like to acknowledge [Aquaveo](https://aquaveo.com/), who helped develop the interactive [FIMbench GUI](https://tethys.ciroh.org/apps/fimbench-gui/) on the CIROH Tethys Platform. |

### **For More Information**
<hr style="border: 1px solid black; margin: 0;">

#### **Contact**

<a href="https://geography.ua.edu/people/sagy-cohen/" target="_blank">Dr. Sagy Cohen</a> (sagy.cohen@ua.edu),
Supath Dhital (sdhital@ua.edu),
Dipsikha Devi (ddevi@ua.edu)
</content>
</invoke>
