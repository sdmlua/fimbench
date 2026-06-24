"""
fimbench
========

Flood Inundation Map (FIM) benchmarking utilities: preprocessing, S3-backed
database interaction, web-content creation/publishing, and querying for the
FIMbench project.

The package is organised into focused subpackages, each owning one stage of
the FIM data lifecycle:

- :mod:`fimbench.processing_floodmap`  -- standardize a raw flood map for the database
  (normalize -> metadata + GeoPackage).
- :mod:`fimbench.webcontent_utils`  -- create web-servable content: build the catalog,
  make tiles, serve/inspect them locally, and interact with S3 (S3 layer lives
  in :mod:`fimbench.publish.s3`).
- :mod:`fimbench.query`       -- query availability of data in the database.
- :mod:`fimbench.publish`     -- publish standardized extents to external
  services (e.g. ArcGIS Online).

A typical end-to-end flow:

    raw flood map
        -> processing_floodmap  (standardize -> metadata.json + .gpkg)
        -> webcontent_utils  (build catalog -> make tiles -> upload to S3 database)
        -> query       (discover what is available)
        -> publish     (optional: push to ArcGIS Online)

Modules are intentionally left as thin stubs in places; they will be populated
incrementally.
"""

from __future__ import annotations

__version__ = "0.1.0"

# Public API is re-exported lazily as submodules are populated.
# Keep this list in sync with what each subpackage exposes.
__all__: list[str] = [
    "processing_floodmap",
    "webcontent_utils",
    "query",
    "publish",
]
