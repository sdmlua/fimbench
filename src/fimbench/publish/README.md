# fimbench.publish

This is the shared module that **pushes** FIMbench content out to its
destinations. It takes a benchmark flood map already standardized by
[`fimbench.processing_floodmap`](../processing_floodmap/README.md) and the
catalog core & vector tiles built by
[`fimbench.webcontent_utils`](../webcontent_utils/README.md), and publishes
them, to the S3 database and to ArcGIS Online, so every uploader shares one
S3 access layer and one set of metadata defaults.

## What it does

- **Talk to S3** - `s3/` is the single S3 access layer for the whole package; it is the one place that builds `boto3` clients.
- **Publish a benchmark flood map** - push a ready-made map folder (GeoTIFF + `metadata.json` + `AOI.gpkg`) from `processing_floodmap` to the S3 database.
- **Prepare the catalog core** — gather all per-map metadata into a unified place (`catalog_core.json` + `FIM_extents.geojson`) and push it to S3.
- **Make and upload tiles** - take the vector tiles produced by `webcontent_utils` and upload them alongside the catalog.
- **Publish to ArcGIS Online** - create / overwrite a hosted feature layer of the standardized extents.

## AWS credentials

All S3 publishing goes through the single access layer
(`fimbench.publish.s3.get_s3_client`), so credentials resolve the same way
everywhere and are **optional**:

1. **Explicit keys** - `aws_access_key_id` + `aws_secret_access_key` (+ `region`), if you pass them.
2. **Device credentials** - whatever is already configured (env vars, default profile, IAM role). This is the default.
3. **Interactive prompt** - if none of the above are found and you are on a terminal, you are asked to enter the keys.

So the usual call passes **no** credentials and relies on the device; pass keys
only when the device is not configured.

## Use

```python
# Scenario 1 — publish a single standardized flood map folder to S3.
# (folder is the per-map output of fimbench.processing_floodmap)
from fimbench.publish import upload_benchmarkfloodmap

# (a) Use the device's configured credentials (or be prompted if none found):
upload_benchmarkfloodmap("out/AI_..._folder/", bucket="sdmlab", prefix="FIM_Database/")

# (b) Or pass explicit keys to skip the device lookup / prompt:
upload_benchmarkfloodmap(
    "out/AI_..._folder/",
    bucket="sdmlab",
    prefix="FIM_Database/",
    aws_access_key_id="AKIA...",
    aws_secret_access_key="...",
    region="us-east-1",
)

# Scenario 2 — push the catalog core + tiles (from webcontent_utils) to S3.
from fimbench.publish import upload_catalogntilesintos3

upload_catalogntilesintos3(
    catalog_path="out/catalog_core.json",
    tiles_dir="out/tiles/",
    bucket="sdmlab",
    prefix="FIM_Database/",
)

# Scenario 3 — publish the standardized extents to ArcGIS Online.
from fimbench.publish import PublishFIMExtent2ArcGISOnline

gis = PublishFIMExtent2ArcGISOnline.connect_gis_oauth(client_id="...")
publisher = PublishFIMExtent2ArcGISOnline(
    mode_used="init",
    geojson_item_id=None,
    feature_layer_item_id="",
    feature_layer_url=None,
    feature_layer_title=None,
)
result = publisher.upsert_geojson_feature_layer(
    gis=gis,
    geojson_path="out/FIM_extents.geojson",
    mode="auto",
    # title / tags / summary / description / folder default to FIMbench
    # values; pass your own to override.
)
```

## Files

- `s3/` — S3 interaction layer (`s3_client`, `s3_io`); the one place that builds `boto3` clients.
- `upload_benchmarkfloodmap.py` — `upload_benchmarkfloodmap`: push a standardized flood map (GeoTIFF + `metadata.json` + `AOI.gpkg`) to S3.
- `upload_catalogntilesintos3.py` — push the catalog core + vector tiles to S3.
- `arcgis_online.py` — `PublishFIMExtent2ArcGISOnline`: create / overwrite an AGOL hosted feature layer.

> ArcGIS Online publishing needs the `publish` extra: `pip install -e ".[publish]"`.
> The S3 push does **not** require it.

**For more usage notes refer to the [tests](../../../tests/) or [docs](../../../docs/) for the fimbench python package**
