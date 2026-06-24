# `fimbench.publish`

**Pushes** FIM content out to its destinations. Takes the catalog + vector
tiles created by [`fimbench.webcontent_utils`](webcontent_utils.md) and
publishes them — to the S3 database and to external platforms. This group also
holds the package's single S3 access layer.

## Modules

| Module                        | Purpose                                                       |
| ----------------------------- | ------------------------------------------------------------- |
| `s3`                          | S3 interaction layer — the only place that builds `boto3` clients |
| `upload_catalogntilesintos3`  | Push the catalog + vector tiles to the S3 database            |
| `arcgis_online`               | `PublishFIMExtent2ArcGISOnline` — create / overwrite an AGOL layer |

New destinations get their own `upload_*` module here.

## The S3 layer — `fimbench.publish.s3`

The single place that constructs `boto3` clients. The S3 push and
`fimbench.query` both go through it rather than talking to S3 directly.

| Module      | Purpose                                                        |
| ----------- | -------------------------------------------------------------- |
| `s3_client` | Session / client construction (signed and anonymous/unsigned) |
| `s3_io`     | Object-level helpers: list, head, get, put, upload, presign    |

```python
from fimbench.publish.s3.s3_client import DEFAULT_BUCKET, DEFAULT_PREFIX
# "sdmlab", "FIM_Database/"
```

## ArcGIS Online

```python
from fimbench.publish import PublishFIMExtent2ArcGISOnline

gis = PublishFIMExtent2ArcGISOnline.connect_gis_oauth(client_id="...")
publisher = PublishFIMExtent2ArcGISOnline(
    mode_used="init", geojson_item_id=None, feature_layer_item_id="",
    feature_layer_url=None, feature_layer_title=None,
)
result = publisher.upsert_geojson_feature_layer(
    gis=gis, geojson_path="FIM_extents.geojson", mode="auto", title="BenchFIMExtents",
)
```

GeoJSON inputs should be WGS84 (EPSG:4326). AGOL publishing needs the optional
extra: `pip install -e ".[publish]"` (the S3 push does not).
