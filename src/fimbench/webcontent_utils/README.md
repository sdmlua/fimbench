# fimbench.webcontent_utils

**Creates** web-servable content for the FIM database. Runs *after* a raw flood
map has been standardized by `processing_floodmap`, and produces the artifacts
the viewer / web app consume. Pushing that content out (to S3 or ArcGIS Online)
is the job of [`fimbench.publish`](../publish/README.md).

## What it does

- Build the catalog (`catalog_core.json` + `FIM_extents.geojson`) from the bucket.
- Turn FIM extents into vector tiles (tippecanoe / mb-util).
- Smooth / simplify extents for rendering.
- Serve and inspect tiles locally.

## Use

```python
from fimbench.webcontent_utils import FIMCatalogBuilder, CatalogandTileManager

# 1) Build the catalog
builder = FIMCatalogBuilder(bucket="sdmlab", prefix="FIM_Database/", out_dir="./out")
builder.build_catalog()

# 2) Make vector tiles from the extents
manager = CatalogandTileManager(out_dir="./out", min_zoom=3, max_zoom=14)
manager.execute(
    source_path="./out/FIM_extents.geojson",
    catalog_path="./out/catalog_core.json",
    run_tiling=True,
)
```

## Files

- `build_catalog.py` — `FIMCatalogBuilder`: crawl S3, normalize metadata, build catalog.
- `tiling.py` — `CatalogandTileManager`: extents → vector tiles.
- `smoothen_fimextent.py` — geometry smoothing / simplification helpers.
- `viewtile_locally/` — minimal local tile server + viewer.

> **Tiling needs** [`tippecanoe`](https://github.com/felt/tippecanoe) on your
> `PATH` (`brew install tippecanoe`) and the `tiling` extra:
> `pip install -e ".[tiling]"`.
