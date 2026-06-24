"""
fimbench.processing_floodmap
============================

Transform a *raw* flood inundation map into a standardized, database-compatible
artifact.

This is the entry stage of the pipeline: take a heterogeneous input (raster
extent or vector polygons, arbitrary CRS, inconsistent fields) and produce a
normalized GeoPackage plus a standardized metadata document, so that everything
downstream (:mod:`fimbench.webcontent_utils`, :mod:`fimbench.query`,
:mod:`fimbench.publish`) can assume a single, consistent schema.

This package is intentionally empty for now — modules (e.g. flood-map
normalization, metadata building, GeoPackage writing) will be added here as the
standardization workflow is implemented.
"""

from __future__ import annotations

__all__: list[str] = []
