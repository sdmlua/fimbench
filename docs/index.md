# fimbench documentation

`fimbench` provides flood inundation map (FIM) preprocessing, S3-backed
database interaction, and querying for the FIMbench project.

## Contents

- [Architecture](architecture.md) — how the package is organised and how data
  flows through it.
- [Getting started](getting-started.md) — install and a first run.
- Group guides (one per stage of the lifecycle):
  - [`processing_floodmap`](subpackages/processing_floodmap.md) — standardize a raw flood map.
  - [`webcontent_utils`](subpackages/webcontent_utils.md) — create web content: catalog, tiles, local viewer.
  - [`query`](subpackages/query.md) — query data availability + download.
  - [`publish`](subpackages/publish.md) — push to S3 and to external services (incl. the S3 layer).

## The data lifecycle

```
raw flood map
   └─ processing_floodmap : standardize       → metadata.json + .gpkg
        └─ webcontent_utils : build catalog    → make tiles → (smooth extents)
             └─ query        : discover what is available
                  └─ publish : push tiles/catalog to S3 · push extents to AGOL
```

`publish/s3/` is the single S3 layer every stage uses to talk to the bucket.

> This documentation tracks the package as it is built out; sections are filled
> in as the corresponding modules are populated.
