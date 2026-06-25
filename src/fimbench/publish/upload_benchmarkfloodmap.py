"""
Upload a standardized benchmark flood map to the S3 database.

Recursively uploads a local folder (the GeoTIFF + metadata.json + AOI.gpkg
produced by fimbench.processing_floodmap) to s3://<bucket>/<prefix>, mirroring
`aws s3 cp <local> s3://... --recursive`.

AWS credentials: pass aws_access_key_id / aws_secret_access_key / region to use
explicit keys, or leave them None to use the credentials already configured on
the device (env vars, shared profile, IAM role).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import boto3

BUCKET = "sdmlab"
PREFIX = "FIM_Database/"


def _client(aws_access_key_id=None, aws_secret_access_key=None, region=None):
    if aws_access_key_id and aws_secret_access_key:
        return boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )
    # Fall back to the device's configured credentials.
    return boto3.client("s3", region_name=region)


def upload_benchmarkfloodmap(
    local_path,
    bucket: str = BUCKET,
    prefix: str = PREFIX,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    region: Optional[str] = None,
):
    """
    Upload local_path (a file or folder) to s3://bucket/prefix.

    Folders are uploaded recursively, preserving relative paths.
    Returns the list of S3 keys uploaded.
    """
    local_path = Path(local_path)
    s3 = _client(aws_access_key_id, aws_secret_access_key, region)
    base = prefix.rstrip("/")

    if local_path.is_file():
        files = [local_path]
        root = local_path.parent
    else:
        files = sorted(p for p in local_path.rglob("*") if p.is_file())
        root = local_path

    uploaded = []
    for f in files:
        rel = f.name if local_path.is_file() else f.relative_to(root).as_posix()
        key = f"{base}/{rel}" if base else rel
        s3.upload_file(str(f), bucket, key)
        uploaded.append(key)
        print(f"uploaded s3://{bucket}/{key}")

    return uploaded
