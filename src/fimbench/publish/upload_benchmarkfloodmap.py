"""
Upload a standardized benchmark flood map to the S3 database.

Recursively uploads a local folder (the GeoTIFF + metadata.json + AOI.gpkg
produced by fimbench.processing_floodmap) to s3://<bucket>/<prefix>, mirroring
`aws s3 cp <local> s3://... --recursive`.

AWS credentials are optional: pass aws_access_key_id / aws_secret_access_key /
region to use explicit keys, or leave them None to use the credentials already
configured on the device (env vars, shared profile, IAM role). If none are
found, you are prompted for them on an interactive terminal.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .._log import log
from .s3.s3_client import DEFAULT_BUCKET, DEFAULT_PREFIX, get_s3_client

BUCKET = DEFAULT_BUCKET
PREFIX = DEFAULT_PREFIX


def upload_benchmarkfloodmap(
    local_path,
    bucket: str = BUCKET,
    prefix: str = PREFIX,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    region: Optional[str] = None,
    profile: Optional[str] = None,
):
    """
    Upload local_path (a file or folder) to s3://bucket/prefix.

    Folders are uploaded recursively, preserving relative paths.
    Returns the list of S3 keys uploaded.

    Credentials resolve through fimbench.publish.s3.get_s3_client: explicit
    keys -> named profile -> device credentials -> interactive prompt.
    """
    local_path = Path(local_path)
    s3 = get_s3_client(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region=region,
        profile=profile,
    )
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
        log(f"uploaded s3://{bucket}/{key}")

    return uploaded
