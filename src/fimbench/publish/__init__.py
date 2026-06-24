"""
fimbench.publish
================

Push FIM content out to its destinations.

This is the "publishing" stage: it takes the catalog + tiles created by
:mod:`fimbench.webcontent_utils` and pushes them out, to the S3 database and to
external consumer-facing platforms.

Subpackages / modules
---------------------
s3
    S3 interaction layer (client construction + object-level helpers) — the
    single place that talks to the bucket.
upload_catalogntilesintos3
    Push the catalog + vector tiles to the S3 database (via ``s3``). Future
    destinations get their own ``upload_*`` module alongside this one.
arcgis_online
    Create / overwrite an ArcGIS Online hosted feature layer from a GeoJSON
    (:class:`PublishFIMExtent2ArcGISOnline`).

Public API
----------
PublishFIMExtent2ArcGISOnline
    ArcGIS Online publisher (from :mod:`fimbench.publish.arcgis_online`).

Note
----
ArcGIS Online publishing depends on the optional ``arcgis`` package::

    pip install -e ".[publish]"

``PublishFIMExtent2ArcGISOnline`` is imported lazily so that importing
``fimbench.publish`` (and using the S3 push) does not require ``arcgis``.
"""

from __future__ import annotations

__all__ = [
    "PublishFIMExtent2ArcGISOnline",
]


def __getattr__(name: str):
    # Lazy import so `import fimbench.publish` works without the `arcgis` extra.
    if name == "PublishFIMExtent2ArcGISOnline":
        from .arcgis_online import PublishFIMExtent2ArcGISOnline

        return PublishFIMExtent2ArcGISOnline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
