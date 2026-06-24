# fimbench

Flood Inundation Map (FIM) benchmarking toolkit for the [SDML](https://github.com/sdmlua) FIMbench project.

**`fimbench`** — a Python package (under `src/fimbench/`) for FIM
*preprocessing*, web-content creation, S3-backed *database interaction*, and
*querying*: standardize a flood map, build its catalog/tiles, push them to the
S3 database, and query what is available.

## Repository layout

The package is organised into four groups that follow the FIM data lifecycle.
Content is **created** in one group and **pushed out** by another; the S3
access layer lives with the push side (`publish/s3/`).

```
fimbench/
├── pyproject.toml              # fimbench package definition
├── README.md  ·  LICENSE  ·  CONTRIBUTING.md
├── docs/                       # documentation
├── assets/                     # images / logos / diagrams
├── src/
│   └── fimbench/
│       ├── __init__.py
│       ├── processing_floodmap/   # raw flood map -> standardized, DB-compatible
│       │                          #   (normalize, metadata, geopackage — to be populated)
│       ├── webcontent_utils/      # CREATE web content
│       │   ├── build_catalog.py       #   FIMCatalogBuilder
│       │   ├── tiling.py              #   CatalogandTileManager (extents -> tiles)
│       │   ├── smoothen_fimextent.py  #   geometry smoothing
│       │   └── viewtile_locally/      #   local vector-tile server + viewer
│       ├── query/                 # QUERY availability + download
│       │   ├── access_benchfim.py     #   benchFIMquery
│       │   └── utilis.py
│       └── publish/               # PUSH content out
│           ├── s3/                    #   S3 layer (only boto3 clients)
│           ├── upload_catalogntilesintos3.py   #   push catalog + tiles to S3
│           └── arcgis_online.py       #   PublishFIMExtent2ArcGISOnline (AGOL)
└── tests/
```

## The data lifecycle

The four groups map onto the stages a flood map goes through:

```
raw flood map
   └─ processing_floodmap : standardize       → metadata.json + .gpkg
        └─ webcontent_utils : build catalog    → make tiles → (smooth extents)
             └─ query        : discover what is available
                  └─ publish : push tiles/catalog to S3 · push extents to AGOL
```

`publish/s3/` is the single S3 layer every stage uses to talk to the bucket.

## Install (development)

```bash
# editable install of the package + dev tools
pip install -e ".[dev]"

# add optional capabilities as needed:
pip install -e ".[tiling]"    # vector tiles (also needs `tippecanoe` + `mb-util`)
pip install -e ".[publish]"   # ArcGIS Online publishing
```

> **Tiling note:** tile generation requires `tippecanoe` on your PATH —
> `brew install tippecanoe`.

## Status

Early development — the package modules are being populated incrementally.

**Contact:** Supath Dhital — sdhital@ua.edu
