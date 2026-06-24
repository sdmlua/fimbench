# `fimbench.webcontent_utils`

**Creates** web-servable content for the FIM database. Runs *after* a raw flood
map has been standardized by `processing_floodmap`, and produces the artifacts
the viewer / web app consume. Pushing that content out is the job of
[`fimbench.publish`](publish.md).

## Public API

| Object                  | From            | Purpose                                          |
| ----------------------- | --------------- | ------------------------------------------------ |
| `FIMCatalogBuilder`     | `build_catalog` | Crawl S3, normalize metadata → catalog + extents |
| `CatalogandTileManager` | `tiling`        | Turn FIM extents into vector tiles               |

## Modules

| Module               | Purpose                                            |
| -------------------- | -------------------------------------------------- |
| `build_catalog`      | `FIMCatalogBuilder`                                |
| `tiling`             | `CatalogandTileManager` (tippecanoe / mb-util)     |
| `smoothen_fimextent` | Geometry smoothing / simplification of extents     |
| `viewtile_locally`   | Minimal local server + viewer for generated tiles  |

## Use

```python
from fimbench.webcontent_utils import FIMCatalogBuilder, CatalogandTileManager

builder = FIMCatalogBuilder(bucket="sdmlab", prefix="FIM_Database/", out_dir="./out")
builder.build_catalog()

manager = CatalogandTileManager(out_dir="./out", min_zoom=3, max_zoom=14)
manager.execute(
    source_path="./out/FIM_extents.geojson",
    catalog_path="./out/catalog_core.json",
    run_tiling=True,
)
```

## Requirements

Tiling needs [`tippecanoe`](https://github.com/felt/tippecanoe) and `mb-util`
on your `PATH`:

```bash
brew install tippecanoe
pip install -e ".[tiling]"
```
