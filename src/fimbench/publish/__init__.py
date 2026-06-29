"""
fimbench.publish

Push FIM content out: to the S3 database (s3, upload_catalogntilesintos3,
upload_benchmarkfloodmap) and to ArcGIS Online (arcgis_online).
PublishFIMExtent2ArcGISOnline is lazy so importing this package does not
require the optional ``arcgis`` extra.
"""

from __future__ import annotations

from .upload_benchmarkfloodmap import upload_benchmarkfloodmap

__all__ = [
    "upload_benchmarkfloodmap",
    "PublishFIMExtent2ArcGISOnline",
]


def __getattr__(name: str):
    # Lazy import so `import fimbench.publish` works without the `arcgis` extra.
    if name == "PublishFIMExtent2ArcGISOnline":
        from .arcgis_online import PublishFIMExtent2ArcGISOnline

        return PublishFIMExtent2ArcGISOnline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
