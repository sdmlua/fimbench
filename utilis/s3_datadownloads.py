from __future__ import annotations
import urllib.parse
from typing import Optional

import requests
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import NoCredentialsError, ClientError

BUCKET = "sdmlab"

# helpers for direct S3 file links
def s3_http_url(bucket: str, key: str) -> str:
    """Build a public-style S3 HTTPS URL (works for public buckets)."""
    return f"https://{bucket}.s3.amazonaws.com/{urllib.parse.quote(key, safe='/')}"

def _head_ok(url: str, timeout: float = 5.0) -> bool:
    """Lightweight existence check using HTTP HEAD (no creds needed)."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        return r.status_code == 200
    except requests.RequestException:
        return False

def find_json_in_folder(bucket: str, folder: str, tif_filename: str | None) -> str | None:
    """
    Find a metadata .json in the same folder without requiring AWS credentials.

    Strategy:
      1) Try <tif_basename>.json next to the .tif (HTTP HEAD).
      2) Try to list via anonymous (UNSIGNED) boto3 if the bucket allows public ListBucket.
      3) If listing isn't allowed, probe common names via HTTP HEAD.

    Returns the JSON key (e.g., "FIM_Database/.../foo.json") or None.
    """
    folder = (folder or "").rstrip("/")

    # Prefer <basename>.json adjacent to the .tif
    if tif_filename:
        base = tif_filename.rsplit(".", 1)[0]
        candidate = f"{folder}/{base}.json"
        if _head_ok(s3_http_url(bucket, candidate)):
            return candidate

    # Attempt public ListObjectsV2 via UNSIGNED client (no creds)
    try:
        s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=f"{folder}/"):
            for obj in page.get("Contents", []) or []:
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                if key.lower().endswith(".json"):
                    return key
    except (NoCredentialsError, ClientError):
        # If listing is forbidden for anonymous users, fall through to HEAD probes.
        pass

    # Probe a few common JSON filenames via HTTP HEAD
    candidates = [
        f"{folder}/metadata.json",
        f"{folder}/meta.json",
        f"{folder}/info.json",
        f"{folder}/{folder.split('/')[-1] or 'metadata'}.json",
    ]
    for key in candidates:
        if _head_ok(s3_http_url(bucket, key)):
            return key

    return None
