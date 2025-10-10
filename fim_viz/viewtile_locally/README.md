# FIM Tiles Bundle

This bundle contains a single utility `fim_tiles_cli.py` to convert your **extents** into fast **vector tiles** and (optionally) upload them to **S3 / CloudFront**. It also produces a ready‑to‑paste Leaflet.VectorGrid snippet for your Streamlit/Folium app.

## What it does

1. Reads your `extents.parquet` (or an existing GeoJSON).
2. Keeps minimal properties: `id`, `tier`, `site` (+ optional fields from `catalog_core.json` like `tif_url`, `json_url`).
3. Builds an **MBTiles** vector tileset using **tippecanoe**.
4. Explodes the MBTiles to a `{z}/{x}/{y}.pbf` directory using **mb-util**.
5. Uploads to **S3** with correct `Content-Type` and `Content-Encoding`.
6. Writes:
   - `tile_manifest.json` (URL template & layer name),
   - `integration_snippet.py` (copy into your Streamlit script).

## Requirements

- System:
  - [tippecanoe](https://github.com/mapbox/tippecanoe) in your `PATH`
  - (Optional) `mb-util` script from Python package `mbutil` in your `PATH` (for extracting `{z}/{x}/{y}.pbf`).
- Python packages:
  - `geopandas shapely pandas boto3 pyarrow pyogrio`

On macOS (Homebrew):
```bash
brew install tippecanoe
python -m pip install geopandas shapely pandas boto3 pyarrow pyogrio mbutil
```

On Ubuntu:
```bash
sudo apt-get update
# tippecanoe: either build from source or use prebuilt releases
# then:
python3 -m pip install geopandas shapely pandas boto3 pyarrow pyogrio mbutil
```

## Example usage

```bash
python fim_tiles_cli.py \
  --parquet FIM_Database/extents.parquet \
  --catalog FIM_Database/catalog_core.json \
  --include tif_url json_url \
  --out-dir out_tiles \
  --s3-bucket sdmlab \
  --s3-prefix FIM_Database/fim_tiles \
  --cdn-domain d123abcd.cloudfront.net \
  --min-zoom 3 --max-zoom 14
```

Outputs:
- `out_tiles/extents_min.geojson`
- `out_tiles/fim_extents.mbtiles`
- `out_tiles/tiles/` (if not `--skip-extract`)
- `out_tiles/tile_manifest.json`
- `out_tiles/integration_snippet.py`

## S3 / CloudFront notes

- Ensure your S3 CORS allows `GET,HEAD` from your app’s origin.
- Make sure objects ending with `.pbf` have headers:
  - `Content-Type: application/x-protobuf`
  - `Content-Encoding: gzip`
- The script sets these when using the `--s3-bucket` uploader.
- If you front with CloudFront, pass `--cdn-domain YOUR_DIST_ID.cloudfront.net`.

## Streamlit integration

Open `out_tiles/integration_snippet.py` and copy the `VectorGridProtobuf` MacroElement class and the `m.add_child(VectorGridProtobuf())` call into your app. Replace the tile URL if needed.

## Per‑tier tiles (optional)

To keep tiles ultra-light and filter by tier on the client without JS logic, you can run the utility separately for each subset (Tier_1, Tier_2, …) by pre-filtering your Parquet to a temporary GeoJSON and then calling the CLI; add one VectorGrid layer per tier and toggle based on the sidebar.
