# fimbench.webcontent_utils

This module **creates** the web-servable content for the FIMbench database. It
runs *after* a raw flood map has been standardized by
[`fimbench.processing_floodmap`](../processing_floodmap/README.md): it crawls the
standardized maps in the bucket, gathers all their metadata into a unified
catalog core, and turns the extents into vector tiles the viewer / web app
consume. Pushing that content out (to S3 or ArcGIS Online) is the job of
[`fimbench.publish`](../publish/README.md), and reading it back is
[`fimbench.query`](../query/README.md).

## What it does

- **Build the catalog core** — crawl the bucket, normalize per-map metadata, and write `catalog_core.json` + `FIM_extents.geojson`.
- **Make vector tiles** — turn the FIM extents into MBTiles / tiles (via `tippecanoe`).
- **Smooth extents** — simplify geometry for cleaner rendering.
- **Inspect locally** — serve and view the tiles before publishing.

## AWS credentials

Building the catalog reads the bucket, and uploading tiles writes to it, so
those steps need credentials; making tiles locally does not. Credentials are
**optional** and resolve the same way as elsewhere in the package:

1. **Explicit keys** — `aws_access_key_id` + `aws_secret_access_key` (+ `region`), if you pass them.
2. **Device credentials** — whatever is already configured (env vars, default profile, IAM role). This is the default.

`FIMCatalogBuilder` also accepts a named `profile`. Leave the keys out for the
usual case; pass them only when the device is not configured.

## Use

```python
from fimbench.webcontent_utils import FIMCatalogBuilder, CatalogandTileManager

# Scenario 1 — build the catalog core from the bucket.
# (creds optional; defaults to the device's configured credentials)
builder = FIMCatalogBuilder(bucket="sdmlab", prefix="FIM_Database/", out_dir="./out")
builder.build_catalog()                 # writes catalog_core.json + FIM_extents.geojson

# Scenario 2 — make vector tiles locally (no S3, no credentials needed).
manager = CatalogandTileManager(out_dir="./out", min_zoom=3, max_zoom=14)
manager.execute(
    source_path="./out/FIM_extents.geojson",
    catalog_path="./out/catalog_core.json",
    run_tiling=True,
    upload_tiles=False,                 # keep everything local
    upload_json=False,
)

# Scenario 3 — make tiles and upload them (+ catalog) to S3.
manager = CatalogandTileManager(
    out_dir="./out",
    s3_bucket="sdmlab",                 # setting a bucket turns on uploads
    s3_prefix="FIM_Database/FIM_Viz",
    min_zoom=3,
    max_zoom=14,
    # aws_access_key_id / aws_secret_access_key / region optional (device creds by default)
)
manager.execute(
    source_path="./out/FIM_extents.geojson",
    catalog_path="./out/catalog_core.json",
    run_tiling=True,
    upload_tiles=True,
    upload_json=True,
)
```

`execute` flags let you run *catalog only*, *tiles only*, or *both*
(`run_tiling`, `upload_tiles`, `upload_json`, `cleanup`).

## Files

- `build_catalog.py` — `FIMCatalogBuilder`: crawl S3, normalize metadata, build the catalog core.
- `tiling.py` — `CatalogandTileManager`: extents → vector tiles, with optional S3 upload.
- `smoothen_fimextent.py` — geometry smoothing / simplification helpers.
- `viewtile_locally/` — minimal local tile server + viewer.

> **Tiling needs** [`tippecanoe`](https://github.com/felt/tippecanoe) on your
> `PATH` (`brew install tippecanoe`) and the `tiling` extra:
> `pip install -e ".[tiling]"`.

**For more usage notes refer to the [tests](../../../tests/) or [docs](../../../docs/) for the fimbench python package**
