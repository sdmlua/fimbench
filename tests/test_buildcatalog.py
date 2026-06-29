"""
Test: build the FIM catalog (fimbench.webcontent_utils.FIMCatalogBuilder).

Crawls S3 and writes catalog_core.json + FIM_extents.geojson.
Run with pytest; comment out any test function you do not want to run.

AWS credentials: pass aws_access_key_id + aws_secret_access_key to use explicit
keys; leave them None to use the credentials already configured on the device
(env vars / `aws configure` / IAM role). If none are found, it raises.
"""

from pathlib import Path

import fimbench

out_dir = Path("./out")
aws_access_key_id = None          # None -> use the device's configured credentials
aws_secret_access_key = None
region = None                     # e.g. "us-east-1"


def test_build_catalog():
    builder = fimbench.FIMCatalogBuilder(
        bucket="sdmlab",
        prefix="FIM_Database/",
        out_dir=out_dir,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region=region,
    )
    builder.build_catalog()
