"""
One-stop utility to:
- Read FIM extents from Parquet (or GeoJSON)
- (Optionally) merge extra fields from catalog_core.json keyed by 'id'
- Export a minimized GeoJSON (WGS84) with just the needed fields
- Build vector tiles (.mbtiles) with tippecanoe
- Explode to {z}/{x}/{y}.pbf with mb-util
- Upload tiles to S3 with correct headers (boto3)
- Emit a manifest + ready-to-paste Streamlit/Folium VectorGrid snippet

USAGE (example):
upload tiles only
python fim_tiles.py \
  --geojson-in FIM_extents.geojson \
  --catalog catalog_core.json \
  --include tif_url json_url \
  --out-dir out_tiles \
  --s3-bucket sdmlab \
  --s3-prefix FIM_Database/FIM_Viz \
  --min-zoom 3 --max-zoom 14
  
upload tiles and json
python fim_tiles.py \
  --geojson-in FIM_extents.geojson \
  --catalog catalog_core.json \
  --include tif_url json_url \
  --out-dir out_tiles \
  --s3-bucket sdmlab \
  --s3-prefix FIM_Database/FIM_Viz \
  --min-zoom 3 --max-zoom 14 \
  --upload-json --json-target both

upload json (catalog + extents) only
python fim_tiles.py \
  --catalog catalog_core.json \
  --geojson-in FIM_extents.geojson \
  --out-dir out_tiles \
  --s3-bucket sdmlab \
  --s3-prefix FIM_Database/FIM_Viz \
  --upload-json-only

upload catalog core json only
python fim_tiles.py \
  --catalog catalog_core.json \
  --out-dir out_tiles \
  --s3-bucket sdmlab \
  --s3-prefix FIM_Database/FIM_Viz \
  --upload-json-only --json-target catalog


Requirements:
  - Python: geopandas, shapely, pandas, boto3, pyogrio (recommended), pyarrow
  - System: tippecanoe (https://github.com/mapbox/tippecanoe) in PATH
  - Python package 'mbutil' (provides `mb-util` script) in PATH, or use --skip-extract and serve mbtiles via a tile server.
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import geopandas as gpd
import boto3


def info(msg: str):
    print(f"[INFO] {msg}", flush=True)


def warn(msg: str):
    print(f"[WARN] {msg}", flush=True)


def err(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr, flush=True)


def which_or_die(name: str, hint: str):
    path = shutil.which(name)
    if not path:
        err(f"'{name}' not found in PATH. {hint}")
        sys.exit(2)
    return path


# args
def parse_args():
    p = argparse.ArgumentParser(description="Build and upload FIM vector tiles to S3.")

    # NOTE: not required=True anymore so JSON-only can run without sources
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--parquet", type=Path, help="Path to extents.parquet")
    src.add_argument("--geojson-in", type=Path, help="Existing extents GeoJSON to tile")

    p.add_argument(
        "--catalog",
        type=Path,
        help="Path to catalog_core.json to merge/upload",
        default=None,
    )
    p.add_argument(
        "--include",
        nargs="*",
        default=[],
        help="Extra fields from catalog to include in tiles (e.g., tif_url json_url)",
    )

    p.add_argument(
        "--out-dir", type=Path, required=True, help="Output directory (mbtiles → tiles)"
    )
    p.add_argument("--layer-name", default="fim_extents", help="Vector tile layer name")
    p.add_argument("--min-zoom", type=int, default=3)
    p.add_argument("--max-zoom", type=int, default=14)
    p.add_argument(
        "--skip-extract",
        action="store_true",
        help="Do not explode MBTiles; serve with a tile server instead",
    )
    p.add_argument("--keep-temp", action="store_true", help="Keep fimextent.geojson")

    # NEW: flexible JSON upload controls
    p.add_argument(
        "--upload-json",
        action="store_true",
        help="Also upload catalog/geojson JSONs along with tiles",
    )
    p.add_argument(
        "--upload-json-only",
        action="store_true",
        help="Only upload JSONs (catalog/geojson) and exit (skip tiling)",
    )
    p.add_argument(
        "--json-target",
        choices=["catalog", "extents", "both"],
        default="both",
        help="Which JSONs to upload (default: both)",
    )

    p.add_argument("--s3-bucket", type=str, help="S3 bucket to upload to")
    p.add_argument(
        "--s3-prefix", type=str, help="S3 prefix/folder (e.g., FIM_Database/FIM_Viz)"
    )
    return p.parse_args()


# upload helpers
def upload_json_file(path: Path, bucket: str, prefix: str, key_name: str):
    if not path or not path.exists():
        warn(f"File {path} not found — skipping upload for {key_name}")
        return
    s3 = boto3.client("s3")
    ct = (
        "application/geo+json"
        if path.suffix.lower() == ".geojson"
        else "application/json"
    )
    with open(path, "rb") as fh:
        s3.put_object(
            Bucket=bucket, Key=f"{prefix}/{key_name}", Body=fh.read(), ContentType=ct
        )
    info(f"Uploaded {path} → s3://{bucket}/{prefix}/{key_name}")


def upload_selected_jsons(args, extents_path: Optional[Path]):
    if not args.s3_bucket or not args.s3_prefix:
        err("Both --s3-bucket and --s3-prefix are required to upload JSON files.")
        sys.exit(2)

    want_catalog = args.json_target in ("catalog", "both")
    want_extents = args.json_target in ("extents", "both")

    if want_catalog:
        upload_json_file(
            args.catalog, args.s3_bucket, args.s3_prefix, "catalog_core.json"
        )
    if want_extents:
        # prefer the minimized tmp extents if we built it; else fall back to user-provided --geojson-in
        if extents_path:
            upload_json_file(
                extents_path, args.s3_bucket, args.s3_prefix, "FIM_extents.geojson"
            )
        else:
            upload_json_file(
                args.geojson_in, args.s3_bucket, args.s3_prefix, "FIM_extents.geojson"
            )


# rest of your original code


def prepare_input_geojson(
    parquet_path: Path | None,
    geojson_in: Path | None,
    out_dir: Path,
    catalog_json: Path | None,
    include_fields: List[str],
    keep_temp: bool,
) -> Path:
    if parquet_path is None and geojson_in is None:
        err(
            "Provide either --parquet or --geojson-in (unless using --upload-json-only)."
        )
        sys.exit(2)

    # read
    if parquet_path:
        info(f"Reading Parquet: {parquet_path}")
        gdf = gpd.read_parquet(parquet_path)
    else:
        info(f"Reading GeoJSON: {geojson_in}")
        gdf = gpd.read_file(geojson_in)

    if gdf.empty:
        err("Input GeoDataFrame is empty.")
        sys.exit(2)

    if gdf.crs is None:
        warn("Input CRS is None; assuming EPSG:4326 without reprojection.")
        gdf = gdf.set_crs(4326)
    else:
        epsg = getattr(gdf.crs, "to_epsg", lambda: None)()
        if epsg != 4326:
            warn(
                f"Input CRS is EPSG:{epsg}; proceeding without reprojection per request."
            )

    # ensure minimal columns exist before merge
    if "id" not in gdf.columns:
        gdf["id"] = gdf.index.astype(str)
    if "tier" not in gdf.columns:
        gdf["tier"] = "Unknown_Tier"
    if "site" not in gdf.columns:
        gdf["site"] = gdf["id"]

    # optional catalog merge (for tiles only)
    if catalog_json and include_fields:
        info(f"Merging catalog: {catalog_json} for fields {include_fields}")
        with open(catalog_json, "r", encoding="utf-8") as f:
            core = json.load(f)
        records = core.get("records", core)
        cat_df = pd.DataFrame(records if isinstance(records, list) else [records])

        if "id" not in cat_df.columns:
            warn("Catalog has no 'id' column; skipping merge.")
        else:
            keep_cols = ["id"] + [c for c in include_fields if c in cat_df.columns]
            cat_df = cat_df[keep_cols].drop_duplicates("id")
            gdf = gdf.merge(cat_df, on="id", how="left")

    # required, normalized properties for tiles/filters
    gdf["feature_id"] = gdf["id"].astype(str)
    gdf["site_id"] = gdf["site"].astype(str)
    gdf["tier"] = gdf["tier"].fillna("Unknown_Tier").astype(str)

    # event_date: prefer ISO; handle YYYYMMDD compact
    date_source_cols = [
        "event_date",
        "date",
        "eventDate",
        "flood_date",
        "Date of Flood /Synthetic Flooding Event (return period (years))",
    ]
    src = next((c for c in date_source_cols if c in gdf.columns), None)
    if src is None:
        gdf["event_date"] = pd.Series([pd.NA] * len(gdf), dtype="string")
    else:
        s = gdf[src].astype("string").str.strip()
        yy8 = s.str.len().eq(8) & s.str.isnumeric()
        iso_try = pd.to_datetime(s.mask(yy8, pd.NA), errors="coerce", utc=False)
        ymd_try = pd.to_datetime(
            s.where(yy8), format="%Y%m%d", errors="coerce", utc=False
        )
        ed = iso_try.fillna(ymd_try)
        gdf["event_date"] = ed.dt.date.astype("string")

    gdf["event_ts"] = gdf["event_date"].str.replace("-", "", regex=False)
    gdf.loc[gdf["event_ts"].isna(), "event_ts"] = pd.NA
    gdf["event_ts"] = gdf["event_ts"].astype("Int64")

    # metadata pointers
    if "metadata_url" not in gdf.columns:
        gdf["metadata_url"] = pd.NA
    if "s3_prefix" not in gdf.columns:
        gdf["s3_prefix"] = pd.NA

    # version + compact context
    if "geom_version" not in gdf.columns:
        gdf["geom_version"] = 1

    for col in ("resolution_m", "huc8", "state", "basin", "source", "access_rights"):
        if col not in gdf.columns:
            gdf[col] = pd.NA

    # geometry cleanup
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]

    # centroid
    cent = gdf.geometry.centroid
    gdf["centroid"] = list(map(lambda x, y: [float(x), float(y)], cent.x, cent.y))

    # bounds
    b = gdf.geometry.bounds
    gdf["bbox"] = [
        [float(xmin), float(ymin), float(xmax), float(ymax)]
        for xmin, ymin, xmax, ymax in zip(b.minx, b.miny, b.maxx, b.maxy)
    ]

    # write lean GeoJSON for tippecanoe
    tmp_geojson = out_dir / "fimextent.geojson"
    tmp_geojson.parent.mkdir(parents=True, exist_ok=True)
    info(f"Writing GeoJSON for tippecanoe: {tmp_geojson}")

    keep_props = [
        "feature_id",
        "site_id",
        "tier",
        "event_date",
        "event_ts",
        "metadata_url",
        "s3_prefix",
        "geom_version",
        "resolution_m",
        "huc8",
        "state",
        "basin",
        "source",
        "access_rights",
        "centroid",
        "bbox",
    ]
    extra = [
        c for c in (include_fields or []) if c in gdf.columns and c not in keep_props
    ]
    cols = ["geometry"] + keep_props + extra
    gdf[cols].to_file(tmp_geojson, driver="GeoJSON")

    return tmp_geojson


# tiling helpers unchanged…
def build_mbtiles(
    in_geojson: Path,
    out_mbtiles: Path,
    layer_name: str,
    min_z: int,
    max_z: int,
    include_fields: List[str],
    extra_flags: Optional[List[str]] = None,
):
    tippecanoe = which_or_die(
        "tippecanoe", "Install tippecanoe and ensure it is in PATH."
    )
    out_mbtiles.parent.mkdir(parents=True, exist_ok=True)
    info(f"Building MBTiles with tippecanoe → {out_mbtiles}")

    keep, seen = [], set()
    for f in [
        "feature_id",
        "site_id",
        "tier",
        "event_date",
        "event_ts",
        "metadata_url",
        "s3_prefix",
        "geom_version",
        "resolution_m",
        "huc8",
        "state",
        "basin",
        "source",
        "access_rights",
        "centroid",
        "bbox",
    ] + (include_fields or []):
        if f not in seen:
            keep.append(f)
            seen.add(f)

    include_args = []
    for fld in keep:
        include_args += ["--include", fld]

    cmd = [
        tippecanoe,
        "-o",
        str(out_mbtiles),
        "-l",
        layer_name,
        "-Z",
        str(min_z),
        "-z",
        str(max_z),
        "--force",
        "--read-parallel",
        "--exclude-all",
        *include_args,
        "--no-feature-limit",
        "--no-tile-size-limit",
        "--drop-densest-as-needed",
        "--drop-smallest-as-needed",
        "--coalesce",
        "--coalesce-densest-as-needed",
        "--detect-shared-borders",
        "--extend-zooms-if-still-dropping",
        "--generate-ids",
        str(in_geojson),
    ]
    if extra_flags:
        cmd += extra_flags
    info(" ".join(cmd))
    subprocess.check_call(cmd)
    info("MBTiles built.")


def extract_mbtiles_to_dir(mbtiles: Path, out_dir: Path):
    mbutil = shutil.which("mb-util")
    if not mbutil:
        err(
            "`mb-util` not found. Install 'mbutil' (pip install mbutil), or rerun with --skip-extract."
        )
        sys.exit(2)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    info(f"Extracting {mbtiles} → {out_dir}")
    cmd = [mbutil, "--image_format=pbf", str(mbtiles), str(out_dir)]
    info(" ".join(cmd))
    subprocess.check_call(cmd)
    if not any(out_dir.rglob("*.pbf")):
        warn("No PBF tiles extracted — check mb-util version or MBTiles content.")
    else:
        info("Extraction complete.")


def upload_to_s3(local_tiles: Path, bucket: str, prefix: str):
    s3 = boto3.client("s3")

    def guess_headers(p: Path) -> Dict[str, str]:
        if p.suffix == ".pbf":
            return {"ContentType": "application/x-protobuf", "ContentEncoding": "gzip"}
        elif p.suffix == ".json":
            return {"ContentType": "application/json"}
        else:
            return {"ContentType": "application/octet-stream"}

    for root, _, files in os.walk(local_tiles):
        for fname in files:
            fpath = Path(root) / fname
            key = f"{prefix}/tiles/{fpath.relative_to(local_tiles).as_posix()}"
            info(f"Uploading {fpath} → s3://{bucket}/{key}")
            with open(fpath, "rb") as fh:
                s3.put_object(
                    Bucket=bucket, Key=key, Body=fh.read(), **guess_headers(fpath)
                )
    return f"https://{bucket}.s3.amazonaws.com/{prefix}/tiles/{{z}}/{{x}}/{{y}}.pbf"


# main
def main():
    args = parse_args()

    # JSON-only mode (no sources required)
    if args.upload_json_only:
        if not args.s3_bucket or not args.s3_prefix:
            err("Both --s3-bucket and --s3-prefix are required with --upload-json-only")
            sys.exit(2)
        upload_selected_jsons(args, extents_path=None)
        info("Upload complete (JSON-only mode).")
        sys.exit(0)

    # Normal / tiling mode requires a source
    if not args.parquet and not args.geojson_in:
        err("Provide either --parquet or --geojson-in (or use --upload-json-only).")
        sys.exit(2)

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # build minimized extents geojson for tippecanoe
    tmp_geojson = prepare_input_geojson(
        parquet_path=args.parquet,
        geojson_in=args.geojson_in,
        out_dir=out_dir,
        catalog_json=args.catalog,
        include_fields=args.include,
        keep_temp=args.keep_temp,
    )

    out_mbtiles = out_dir / f"{args.layer_name}.mbtiles"
    tiles_dir = out_dir / "tiles"

    # tiles
    build_mbtiles(
        in_geojson=tmp_geojson,
        out_mbtiles=out_mbtiles,
        layer_name=args.layer_name,
        min_z=args.min_zoom,
        max_z=args.max_zoom,
        include_fields=args.include,
    )

    if not args.skip_extract:
        extract_mbtiles_to_dir(out_mbtiles, tiles_dir)

        if args.s3_bucket and args.s3_prefix:
            url_tpl = upload_to_s3(
                local_tiles=tiles_dir, bucket=args.s3_bucket, prefix=args.s3_prefix
            )
            info(f"Tiles ready at: {url_tpl}")
        else:
            info(
                f"Tiles ready at: {tiles_dir.resolve().as_uri()}/{{z}}/{{x}}/{{y}}.pbf"
            )
    else:
        info(f"Serve {out_mbtiles} via a tileserver")

    # Optionally upload JSONs in the same run
    if args.upload_json:
        upload_selected_jsons(args, extents_path=tmp_geojson)

    if not args.keep_temp:
        try:
            tmp_geojson.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
