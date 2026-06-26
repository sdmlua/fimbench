"""
Test: make vector tiles (fimbench.webcontent_utils.CatalogandTileManager).

Builds tiles from FIM extents and optionally uploads tiles + catalog to S3.
Run with pytest; comment out any test function you do not want to run.

AWS credentials (needed only when uploading to S3): pass aws_access_key_id +
aws_secret_access_key, or leave them None to use the device's configured
credentials.
"""

from pathlib import Path

import fimbench

out_dir = Path("./out")
source_path = out_dir / "FIM_extents.geojson"
catalog_path = out_dir / "catalog_core.json"
aws_access_key_id = None          # None -> use the device's configured credentials
aws_secret_access_key = None
region = None                     # e.g. "us-east-1"


def test_work_with_tiles():
    manager = fimbench.CatalogandTileManager(
        out_dir=out_dir,
        s3_bucket="sdmlab",
        s3_prefix="FIM_Database/FIM_Viz",
        min_zoom=3,
        max_zoom=14,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region=region,
    )
    manager.execute(
        source_path=source_path,
        catalog_path=catalog_path,
        run_tiling=True,
        upload_tiles=True,
        upload_json=True,
    )
