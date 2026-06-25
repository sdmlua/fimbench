"""
fimbench.query

Query benchmark FIM availability in the database and download matched assets.
benchFIMquery (in access_benchfim) is the entry point; utilis has the catalog
and S3 helpers.
"""

from __future__ import annotations

from .access_benchfim import benchFIMquery

__all__ = [
    "benchFIMquery",
]
