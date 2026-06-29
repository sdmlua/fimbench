# Architecture

`fimbench` is a `src/`-layout Python library, organised into four groups that
follow the FIM data lifecycle. Content is **created** in one group and **pushed
out** by another; the S3 access layer lives with the push side.

## Layout

```
src/fimbench/
├── __init__.py
├── processing_floodmap/    # raw flood map -> standardized, DB-compatible artifact
│                           #   (normalize, metadata, geopackage — to be populated)
├── webcontent_utils/       # CREATE web-servable content
│   ├── build_catalog.py        # FIMCatalogBuilder: crawl S3 -> catalog + extents
│   ├── tiling.py               # CatalogandTileManager: extents -> vector tiles
│   ├── smoothen_fimextent.py   # geometry smoothing / simplification
│   └── viewtile_locally/       # local vector-tile server + viewer
├── query/                  # QUERY availability + download assets
│   ├── access_benchfim.py      # benchFIMquery
│   └── utilis.py
└── publish/                # PUSH content out
    ├── s3/                     # S3 interaction layer (the only boto3 clients)
    │   ├── s3_client.py
    │   └── s3_io.py
    ├── upload_catalogntilesintos3.py   # push catalog + tiles to the S3 database
    └── arcgis_online.py        # PublishFIMExtent2ArcGISOnline (AGOL)
```

## The four groups

| Group                 | Role   | Responsibility                                              |
| --------------------- | ------ | ----------------------------------------------------------- |
| `processing_floodmap` | input  | Raw flood map → standardized artifact (metadata + gpkg)     |
| `webcontent_utils`    | create | Build catalog, make/serve tiles, smooth extents             |
| `query`               | read   | Query availability of data in the database, download assets |
| `publish`             | push   | Push catalog/tiles to S3 and extents to ArcGIS Online       |

## Dependency direction

```
processing_floodmap ──► webcontent_utils ──► publish (S3 push / AGOL)
                                              ▲
                              query ──────────┘  (reads via publish.s3)
```

- **`publish/s3` depends on nothing else in the package.** It is the only place
  that constructs `boto3` clients. The S3 push (`upload_catalogntilesintos3`)
  and read-only discovery (`query`) both go through it, so credentials, region,
  and signed/unsigned access are configured in one place.
- **`processing_floodmap` is the entry stage** — raw map → standardized artifact
  with a consistent schema. (Empty for now; to be populated.)
- **`webcontent_utils` creates** the catalog and tiled representation consumed by
  the viewer / web app. It does not push anything out itself.
- **`publish` pushes** that content to its destinations: the S3 database
  (`upload_catalogntilesintos3`) and external services (`arcgis_online`).
- **`query` is read-only**: it loads the catalog (and lists the bucket via
  `publish.s3`) to answer "what data do we have?" and fetch matched assets.

## Design principles

1. **Create vs. push.** `webcontent_utils` makes content; `publish` sends it
   out. New destinations are just new `upload_*` modules under `publish`.
2. **One S3 layer.** No group constructs its own `boto3` session; all S3 access
   goes through `fimbench.publish.s3`.
3. **Standardize early.** Normalization and metadata happen in
   `processing_floodmap`, so the create/query/push stages never deal with raw,
   inconsistent inputs.
