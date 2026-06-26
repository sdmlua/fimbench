"""
S3 client / session construction for the FIM database bucket.

Centralizes how the rest of the package obtains a boto3 S3 client so that
credentials, region, profiles and anonymous (UNSIGNED) access are configured
in exactly one place.
"""

from __future__ import annotations

from typing import Optional

import boto3
from botocore import UNSIGNED
from botocore.config import Config

# Default bucket / prefix for the FIM database.
DEFAULT_BUCKET = "sdmlab"
DEFAULT_PREFIX = "FIM_Database/"


def get_s3_client(
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    anonymous: bool = False,
):
    """
    Build a boto3 S3 client.

    Credential precedence:
      1. anonymous=True            -> unsigned access (public reads, no creds).
      2. explicit keys             -> aws_access_key_id + aws_secret_access_key.
      3. profile                   -> a named profile from the AWS config.
      4. otherwise                 -> whatever is already configured on the
                                      device (env vars, default profile, IAM role).
    Raises RuntimeError if none of the above resolve to usable credentials.
    """
    if anonymous:
        return boto3.client("s3", config=Config(signature_version=UNSIGNED), region_name=region)

    if aws_access_key_id and aws_secret_access_key:
        session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )
    elif profile:
        session = boto3.session.Session(profile_name=profile, region_name=region)
    else:
        # Fall back to the device's configured credentials.
        session = boto3.session.Session(region_name=region)

    if session.get_credentials() is None:
        raise RuntimeError(
            "No AWS credentials found. Pass aws_access_key_id and "
            "aws_secret_access_key, set a profile, or configure credentials on "
            "the device (e.g. `aws configure` or environment variables)."
        )

    return session.client("s3")
