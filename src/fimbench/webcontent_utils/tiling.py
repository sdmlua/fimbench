"""
Author: Supath Dhital (sdhital@ua.edu)
Date Created: January 2026

CatalogandTileManager: A class-based utility to process and upload FIM vector tiles.
"""

import os
import sys
import json
import shutil
import subprocess
import time
import math
import logging
from queue import Queue
from threading import Thread
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import geopandas as gpd
import boto3
from botocore.config import Config
from boto3.s3.transfer import TransferConfig


# Handle the FIMTile and Catalog processing_floodmap
class CatalogandTileManager:
    def __init__(
        self,
        out_dir: str | Path,
        s3_bucket: Optional[str] = None,
        s3_prefix: Optional[str] = None,
        layer_name: str = "fim_extents",
        min_zoom: int = 3,
        max_zoom: int = 14,
    ):
        """
        Initializes the manager with workspace and S3 configurations.
        """
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.layer_name = layer_name
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom

        # S3 client only initialized if bucket is provided
        self.s3_client = None
        if s3_bucket:
            bcfg = Config(
                retries={"max_attempts": 10, "mode": "adaptive"},
                max_pool_connections=256,
            )
            self.s3_client = boto3.client("s3", config=bcfg)

        # Internal paths for intermediate files
        self.tmp_geojson = self.out_dir / "fimextent.geojson"
        self.out_mbtiles = self.out_dir / f"{self.layer_name}.mbtiles"
        self.tiles_dir = self.out_dir / "tiles"

    # Logging
    def _info(self, msg: str):
        print(f"[INFO] {msg}", flush=True)

    def _warn(self, msg: str):
        print(f"[WARN] {msg}", flush=True)

    def _err(self, msg: str):
        print(f"[ERROR] {msg}", file=sys.stderr, flush=True)

    # Upload helpers
    def _auto_workers(self) -> int:
        cpu = os.cpu_count() or 4
        return min(64, max(8, cpu * 4))

    def _render_progress(self, done: int, total: int, t0: float, width: int = 30) -> str:
        if total <= 0:
            return "[no work]"
        pct = done / total
        filled = int(width * pct)
        bar = "█" * filled + "░" * (width - filled)

        elapsed = max(1e-6, time.time() - t0)
        rate = done / elapsed
        eta = (total - done) / rate if rate > 1e-9 else float("inf")

        def fmt_sec(s: float) -> str:
            if not math.isfinite(s):
                return "?"
            m, sec = divmod(int(s), 60)
            h, m = divmod(m, 60)
            if h > 0:
                return f"{h}h{m:02d}m"
            if m > 0:
                return f"{m}m{sec:02d}s"
            return f"{sec}s"

        return f"[{bar}] {pct*100:6.2f}% ({done:,}/{total:,}) | {rate:6.1f} files/s | ETA {fmt_sec(eta)}"

    def _iter_tile_files(self) -> List[Path]:
        files: List[Path] = []
        for root, _, fnames in os.walk(self.tiles_dir):
            for fname in fnames:
                files.append(Path(root) / fname)
        return files

    #Parallel upload of tiles for faster upload
    def _upload_tiles_parallel(self, max_workers: Optional[int] = None):
        if not self.s3_client:
            self._warn("S3 bucket not configured. Skipping upload.")
            return
        if not self.s3_prefix:
            raise ValueError("s3_prefix must be provided when uploading to S3.")
        if not (self.tiles_dir.exists() and self.tiles_dir.is_dir()):
            self._warn("Tile directory not found. Skipping tile upload.")
            return

        files = self._iter_tile_files()
        total = len(files)
        if total == 0:
            self._warn("No tiles found to upload.")
            return

        workers = int(max_workers or self._auto_workers())
        workers = max(8, min(64, workers))
        self._info(f"Uploading tiles to s3://{self.s3_bucket}/{self.s3_prefix}/tiles/")
        self._info(f"Found {total:,} files. Using max_workers={workers}")

        tcfg = TransferConfig(
            max_concurrency=workers,
            use_threads=True,
            multipart_threshold=64 * 1024 * 1024,
            multipart_chunksize=16 * 1024 * 1024,
        )

        q = Queue(maxsize=workers * 4)
        t0 = time.time()
        done = 0
        last_print = 0.0
        err = []

        def _one(fpath: Path):
            rel = fpath.relative_to(self.tiles_dir).as_posix()
            key = f"{self.s3_prefix}/tiles/{rel}"

            headers = {}
            if fpath.suffix == ".pbf":
                headers["ContentType"] = "application/x-protobuf"
                headers["ContentEncoding"] = "gzip"

            self.s3_client.upload_file(
                Filename=str(fpath),
                Bucket=self.s3_bucket,
                Key=key,
                ExtraArgs=headers if headers else None,
                Config=tcfg,
            )

        def worker_fn():
            nonlocal done, last_print
            while True:
                fpath = q.get()
                if fpath is None:
                    q.task_done()
                    break
                try:
                    _one(fpath)
                except Exception as e:
                    err.append((str(fpath), repr(e)))
                finally:
                    q.task_done()
                    done += 1
                    now = time.time()
                    if now - last_print >= 0.25 or done == total:
                        last_print = now
                        print("\r" + self._render_progress(done, total, t0), end="", flush=True)

        threads = [Thread(target=worker_fn, daemon=True) for _ in range(workers)]
        for t in threads:
            t.start()

        for f in files:
            q.put(f)

        for _ in threads:
            q.put(None)

        q.join()
        print("", flush=True)

        if err:
            # show first few only
            self._err(f"{len(err)} uploads failed. First 5:\n" + "\n".join(map(str, err[:5])))
            raise RuntimeError(f"{len(err)} uploads failed. See logs.")

        self._info("Tile upload complete.")

    # Data preparation
    def prepare_data(
        self,
        parquet_path: Optional[Path] = None,
        geojson_in: Optional[Path] = None,
        catalog_path: Optional[Path] = None,
        include_fields: List[str] = [],
    ) -> Path:
        """
        Reads source data, cleans it, merges catalog info, and writes a lean GeoJSON for tiling.
        """
        if not parquet_path and not geojson_in:
            raise ValueError("You must provide either parquet_path or geojson_in.")

        # Read input
        if parquet_path:
            self._info(f"Reading Parquet: {parquet_path}")
            gdf = gpd.read_parquet(parquet_path)
        else:
            self._info(f"Reading GeoJSON: {geojson_in}")
            gdf = gpd.read_file(geojson_in)

        if gdf.empty:
            raise ValueError("Input GeoDataFrame is empty.")

        # CRS Validation (Targeting WGS84)
        if gdf.crs is None:
            self._warn("Input CRS is None; assuming EPSG:4326.")
            gdf = gdf.set_crs(4326)
        elif gdf.crs.to_epsg() != 4326:
            self._warn(f"Input CRS is EPSG:{gdf.crs.to_epsg()}; tiling expects 4326.")

        # Standardize Columns
        if "id" not in gdf.columns:
            gdf["id"] = gdf.index.astype(str)
        if "tier" not in gdf.columns:
            gdf["tier"] = "Unknown_Tier"
        if "site" not in gdf.columns:
            gdf["site"] = gdf["id"]

        # Merge Catalog (if provided)
        if catalog_path:
            self._info(f"Merging catalog core from: {catalog_path}")
            with open(catalog_path, "r", encoding="utf-8") as f:
                core = json.load(f)
            records = core.get("records", core)
            cat_df = pd.DataFrame(records if isinstance(records, list) else [records])

            if "id" in cat_df.columns:
                base_catalog_cols = [
                    "id",
                    "site_id",
                    "tier",
                    "date_ymd",
                    "start_date_ymd",
                    "end_date_ymd",
                    "event_ts",
                    "return_period",
                    "json_url",
                    "tif_url",
                    "gpkg_url",
                    "s3_prefix",
                    "resolution_m",
                    "huc8",
                    "state",
                    "basin",
                    "source",
                    "access_rights",
                    "quality",
                    "description",
                    "file_name",
                    "centroid",
                    "bbox",
                ]

                keep_cols = [c for c in (base_catalog_cols + include_fields) if c in cat_df.columns]
                keep_cols = list(dict.fromkeys(keep_cols))

                cat_df = cat_df[keep_cols].drop_duplicates("id")
                gdf = gdf.merge(cat_df, on="id", how="left", suffixes=("", "_cat"))

                # Prefer catalog values for overlapping columns
                for col in keep_cols:
                    if col == "id":
                        continue
                    cat_col = f"{col}_cat"
                    if cat_col in gdf.columns:
                        if col in gdf.columns:
                            gdf[col] = gdf[cat_col].combine_first(gdf[col])
                            gdf = gdf.drop(columns=[cat_col])
                        else:
                            gdf = gdf.rename(columns={cat_col: col})

        # Logical normalization
        gdf["id"] = gdf["id"].astype(str)

        if "site_id" not in gdf.columns:
            if "site" in gdf.columns:
                gdf["site_id"] = gdf["site"].astype(str)
            else:
                gdf["site_id"] = gdf["id"]

        gdf["site_id"] = gdf["site_id"].astype(str)
        gdf["tier"] = gdf["tier"].fillna("Unknown_Tier").astype(str)

        # Keep these fields if they exist; otherwise create them as null
        for col in [
            "date_ymd",
            "start_date_ymd",
            "end_date_ymd",
            "event_ts",
            "return_period",
            "huc8",
        ]:
            if col not in gdf.columns:
                gdf[col] = None

        # Standardize date strings only for date columns
        for col in ["date_ymd", "start_date_ymd", "end_date_ymd"]:
            if col in gdf.columns:
                dt = pd.to_datetime(gdf[col], errors="coerce")
                gdf[col] = dt.dt.strftime("%Y-%m-%d")
                gdf.loc[dt.isna(), col] = None

        # Keep event_ts only if valid input exists; do not derive from date_ymd
        if "event_ts" in gdf.columns:
            gdf["event_ts"] = pd.to_numeric(gdf["event_ts"], errors="coerce").astype("Int64")
        else:
            gdf["event_ts"] = pd.Series([None] * len(gdf), dtype="Int64")

        # Spatial Cleanup & Metadata
        gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
        cent = gdf.geometry.centroid
        gdf["centroid"] = list(map(lambda x, y: [float(x), float(y)], cent.x, cent.y))
        b = gdf.geometry.bounds
        gdf["bbox"] = [
            [float(x1), float(y1), float(x2), float(y2)]
            for x1, y1, x2, y2 in zip(b.minx, b.miny, b.maxx, b.maxy)
        ]

        # Write lean GeoJSON for Tippecanoe
        keep_props = [
            "id",
            "site_id",
            "tier",
            "date_ymd",
            "start_date_ymd",
            "end_date_ymd",
            "event_ts",
            "return_period",
            "json_url",
            "tif_url",
            "gpkg_url",
            "s3_prefix",
            "resolution_m",
            "huc8",
            "state",
            "basin",
            "source",
            "access_rights",
            "quality",
            "description",
            "file_name",
            "centroid",
            "bbox",
        ]
        # Dynamically add extra fields from merge
        extra = [c for c in include_fields if c in gdf.columns and c not in keep_props]

        self._info(f"Writing temporary GeoJSON: {self.tmp_geojson}")
        gdf[["geometry"] + [c for c in keep_props if c in gdf.columns] + extra].to_file(
            self.tmp_geojson, driver="GeoJSON"
        )
        return self.tmp_geojson

    # Tiling engine
    def build_vector_tiles(self, include_fields: List[str] = []):
        """Runs tippecanoe to generate the .mbtiles file."""
        tippecanoe = shutil.which("tippecanoe")
        if not tippecanoe:
            raise RuntimeError("tippecanoe not found in PATH.")

        self._info(f"Building MBTiles (Zoom {self.min_zoom}-{self.max_zoom})")

        # Build the property inclusion list
        props = set(
            [
                "id",
                "site_id",
                "tier",
                "date_ymd",
                "start_date_ymd",
                "end_date_ymd",
                "event_ts",
                "return_period",
                "json_url",
                "tif_url",
                "gpkg_url",
                "s3_prefix",
                "resolution_m",
                "huc8",
                "state",
                "basin",
                "source",
                "access_rights",
                "quality",
                "description",
                "file_name",
                "centroid",
                "bbox",
            ]
            + include_fields
        )
        include_args = []
        for p in props:
            include_args += ["--include", p]

        cmd = [
            tippecanoe,
            "-o",
            str(self.out_mbtiles),
            "-l",
            self.layer_name,
            "-Z",
            str(self.min_zoom),
            "-z",
            str(self.max_zoom),
            "--force",
            "--read-parallel",
            "--exclude-all",
            *include_args,
            "--no-feature-limit",
            "--no-tile-size-limit",
            "--drop-densest-as-needed",
            "--generate-ids",
            str(self.tmp_geojson),
        ]
        subprocess.check_call(cmd)

    def extract_tiles(self):
        """Uses mb-util to explode .mbtiles into Z/X/Y.pbf structure."""
        mbutil = shutil.which("mb-util")
        if not mbutil:
            raise RuntimeError("mb-util not found. Install via 'pip install mbutil'.")

        if self.tiles_dir.exists():
            shutil.rmtree(self.tiles_dir)

        # Silence mbutil INFO/DEBUG spam ("flipping", etc.) while still running the command
        logging.getLogger("mbutil").setLevel(logging.WARNING)

        self._info(f"Extracting tiles to directory: {self.tiles_dir}")
        subprocess.check_call(
            [mbutil, "--image_format=pbf", str(self.out_mbtiles), str(self.tiles_dir)]
        )

    # S3 Upload
    def upload_to_s3(
        self,
        upload_tiles: bool = True,
        upload_json: bool = False,
        catalog_path: Optional[Path] = None,
        max_workers: Optional[int] = None,
    ):
        """Handles multi-part upload to S3 for tiles and/or JSON assets."""
        if not self.s3_client:
            self._warn("S3 bucket not configured. Skipping upload.")
            return

        # Upload the Tile Directory
        if upload_tiles and self.tiles_dir.exists():
            self._upload_tiles_parallel(max_workers=max_workers)

        # Upload JSON assets (Catalog and/or Extents)
        if upload_json:
            if catalog_path and catalog_path.exists():
                self._upload_file(catalog_path, "catalog_core.json", "application/json")
            if self.tmp_geojson.exists():
                self._upload_file(
                    self.tmp_geojson, "FIM_extents.geojson", "application/geo+json"
                )

    def _upload_file(self, path: Path, key_suffix: str, content_type: str):
        key = f"{self.s3_prefix}/{key_suffix}"
        self._info(f"Uploading asset: {key}")
        with open(path, "rb") as fh:
            self.s3_client.put_object(
                Bucket=self.s3_bucket, Key=key, Body=fh.read(), ContentType=content_type
            )

    def cleanup(self):
        """Removes the intermediate GeoJSON and MBTiles files."""
        for f in [self.tmp_geojson, self.out_mbtiles]:
            if f.exists():
                f.unlink()
        self._info("Cleaned up temporary workspace files.")

    # Execution Pipeline
    def execute(
        self,
        source_path: Optional[str] = None,
        catalog_path: Optional[str] = None,
        include_fields: List[str] = [
            "json_url",
            "tif_url",
            "gpkg_url",
            "date_ymd",
            "start_date_ymd",
            "end_date_ymd",
            "event_ts",
            "return_period",
            "resolution_m",
            "huc8",
            "state",
            "basin",
            "source",
            "access_rights",
            "quality",
            "description",
            "file_name",
        ],
        run_tiling: bool = True,
        upload_tiles: bool = True,
        upload_json: bool = True,
        cleanup: bool = True,
        max_workers: Optional[int] = None,
    ):
        """
        Main entry point to run the pipeline.
        Adjust flags to handle 'json only', 'tiles only', or 'both'.
        """
        try:
            # Tiling Phase
            if run_tiling and source_path:
                source = Path(source_path)
                self.prepare_data(
                    parquet_path=(
                        source if source.suffix.lower() == ".parquet" else None
                    ),
                    geojson_in=source if source.suffix.lower() == ".geojson" else None,
                    catalog_path=Path(catalog_path) if catalog_path else None,
                    include_fields=include_fields,
                )
                self.build_vector_tiles(include_fields=include_fields)
                self.extract_tiles()
            elif run_tiling and not source_path:
                self._err("Cannot run tiling without a valid source_path.")

            # Upload Phase
            self.upload_to_s3(
                upload_tiles=upload_tiles,
                upload_json=upload_json,
                catalog_path=Path(catalog_path) if catalog_path else None,
                max_workers=max_workers,
            )

            self._info("Execution complete.")

        except Exception as e:
            self._err(f"Pipeline failed: {str(e)}")
            raise
        finally:
            if cleanup:
                self.cleanup()