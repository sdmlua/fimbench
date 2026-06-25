# fimbench.publish

**Pushes** FIM content out to its destinations. Takes the catalog + vector
tiles created by [`fimbench.webcontent_utils`](../webcontent_utils/README.md)
and publishes them — to the S3 database and to external platforms.

## What it does

- Talk to the S3 bucket (the single S3 access layer for the whole package).
- Push a standardized benchmark flood map to the S3 database.
- Push the catalog + vector tiles to the S3 database.
- Publish standardized extents to ArcGIS Online as a hosted feature layer.

## Use

```python
# Push a standardized flood map folder to S3 (optional keys, else device creds)
from fimbench.publish import upload_benchmarkfloodmap

upload_benchmarkfloodmap("out/AI_..._folder/", bucket="sdmlab", prefix="FIM_Database/")

# Publish extents to ArcGIS Online
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
    geojson_path="FIM_extents.geojson",
    mode="auto",
    # title / tags / summary / description / folder default to FIMbench
    # values; pass your own to override.
)
```

## Files

- `s3/` — S3 interaction layer (`s3_client`, `s3_io`); the one place that builds `boto3` clients.
- `upload_benchmarkfloodmap.py` — `upload_benchmarkfloodmap`: push a standardized flood map (GeoTIFF + metadata.json + AOI.gpkg) to S3.
- `upload_catalogntilesintos3.py` — push the catalog + tiles to S3 (to be populated).
- `arcgis_online.py` — `PublishFIMExtent2ArcGISOnline`: create / overwrite an AGOL hosted feature layer.

> ArcGIS Online publishing needs the `publish` extra: `pip install -e ".[publish]"`.
> The S3 push does **not** require it.
