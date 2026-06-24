"""
fimbench.query
==============

Query the availability of benchmark flood inundation maps (FIMs) in the FIM
database and download matched assets.

The public entry point is :class:`benchFIMquery`, a high-level access/query
service over ``catalog_core.json`` and the S3 bucket. It supports several
filter combinations:

1. Direct filename download (no AOI / dates).
2. AOI-only search (raster or boundary), with optional overlap statistics.
3. AOI + exact event date.
4. AOI + date range (with optional download).

Example
-------
>>> from fimbench.query import benchFIMquery
>>> response = benchFIMquery(
...     file_name="HWM_10_0m_20160928_20161009_780051W352232N_BM.tif",
...     download=True,
...     out_dir="../downloads/",
... )
>>> print(response)

Modules
-------
access_benchfim
    High-level benchmark FIM access and query service (:class:`benchFIMquery`).
utilis
    Catalog loading, S3 listing/download, date/tier parsing and formatting
    helpers used during querying.
"""

from __future__ import annotations

from .access_benchfim import benchFIMquery

__all__ = [
    "benchFIMquery",
]
