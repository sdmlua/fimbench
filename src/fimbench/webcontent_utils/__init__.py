"""
fimbench.webcontent_utils
=========================

Create web-servable content for the FIM database: build the catalog, generate
vector tiles, smooth/prepare extents, and serve/inspect tiles locally.

This is the stage that runs *after* a flood map has been standardized by
:mod:`fimbench.processing_floodmap`. It *produces* the discovery/catalog artifacts and
the tiled representation consumed by the viewer / web app. Pushing that content
out — to S3 or to ArcGIS Online — is the job of :mod:`fimbench.publish`.

Public API
----------
FIMCatalogBuilder
    Crawl S3, normalize metadata, and build ``catalog_core.json`` +
    ``FIM_extents.geojson`` (from :mod:`~fimbench.webcontent_utils.build_catalog`).
CatalogandTileManager
    Process FIM extents into vector tiles and prepare them for upload
    (from :mod:`~fimbench.webcontent_utils.tiling`).

Other modules
-------------
smoothen_fimextent
    Geometry smoothing / simplification of FIM extents for rendering
    (Chaikin smoothing, coordinate-precision rounding).
viewtile_locally
    Minimal local server + viewer for inspecting generated vector tiles.
"""

from __future__ import annotations

from .build_catalog import FIMCatalogBuilder
from .tiling import CatalogandTileManager

__all__ = [
    "FIMCatalogBuilder",
    "CatalogandTileManager",
]
