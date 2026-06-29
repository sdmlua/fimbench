"""
fimbench

FIM benchmarking utilities. Pipeline: processing_floodmap (standardize) ->
webcontent_utils (catalog + tiles) -> query (availability) -> publish (S3 /
ArcGIS Online). Public classes are re-exported at the top level
(e.g. fimbench.Tier1Processor) and resolved lazily so `import fimbench` stays
light.
"""

from __future__ import annotations

__version__ = "0.1.0"

# Lazy top-level names (see __getattr__); avoids importing rasterio/geopandas/
# arcgis until a name is actually used.
__all__: list[str] = [
    # subpackages
    "processing_floodmap",
    "webcontent_utils",
    "query",
    "publish",
    # processing_floodmap classes -> fimbench.Tier1Processor, etc.
    "Tier1Processor",
    "Tier2Processor",
    "Tier3Processor",
    "FemaBleProcessor",
    "HwmProcessor",
    # webcontent_utils classes
    "FIMCatalogBuilder",
    "CatalogandTileManager",
    # query
    "benchFIMquery",
    # publish
    "PublishFIMExtent2ArcGISOnline",
    "upload_benchmarkfloodmap",
]

# name -> (submodule, attribute) for lazy top-level re-export.
_LAZY = {
    "Tier1Processor": ("processing_floodmap", "Tier1Processor"),
    "Tier2Processor": ("processing_floodmap", "Tier2Processor"),
    "Tier3Processor": ("processing_floodmap", "Tier3Processor"),
    "FemaBleProcessor": ("processing_floodmap", "FemaBleProcessor"),
    "HwmProcessor": ("processing_floodmap", "HwmProcessor"),
    "FIMCatalogBuilder": ("webcontent_utils", "FIMCatalogBuilder"),
    "CatalogandTileManager": ("webcontent_utils", "CatalogandTileManager"),
    "benchFIMquery": ("query", "benchFIMquery"),
    "PublishFIMExtent2ArcGISOnline": ("publish", "PublishFIMExtent2ArcGISOnline"),
    "upload_benchmarkfloodmap": ("publish", "upload_benchmarkfloodmap"),
}


def __getattr__(name: str):
    import importlib

    target = _LAZY.get(name)
    if target is not None:
        submod, attr = target
        module = importlib.import_module(f"{__name__}.{submod}")
        return getattr(module, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__)
