"""
Push the FIM catalog + vector tiles to the S3 database.

Takes the catalog (``catalog_core.json`` / ``FIM_extents.geojson``) and the
vector tiles produced by :mod:`fimbench.webcontent_utils` and uploads them to
S3 through :mod:`fimbench.publish.s3`.

One of several uploaders under :mod:`fimbench.publish`; future destinations get
their own ``upload_*`` module here.

To be populated.
"""

from __future__ import annotations

# def upload_catalog_and_tiles(catalog_path, tiles_dir, bucket, prefix): ...
