"""
Author: Supath Dhital (sdhital@ua.edu)
Date updated: June 2026


S3 client / session construction for the FIM database bucket.

Centralizes how the rest of the package obtains a boto3 S3 client so that
credentials, region, profiles and anonymous (UNSIGNED) access are configured
in exactly one place.
"""

from __future__ import annotations

import getpass
import sys
from typing import Optional

import boto3
from botocore import UNSIGNED
from botocore.config import Config

# Default bucket / prefix for the FIM database.
DEFAULT_BUCKET = "sdmlab"
DEFAULT_PREFIX = "FIM_Database/"


def _prompt_for_credentials(region: Optional[str]):
    """Interactively ask the user for AWS keys (used as a last resort)."""
    print(
        "No AWS credentials found on this device. Enter them below " "(leave blank to abort).",
        file=sys.stderr,
    )
    aws_access_key_id = input("AWS Access Key ID: ").strip()
    aws_secret_access_key = getpass.getpass("AWS Secret Access Key: ").strip()
    if not aws_access_key_id or not aws_secret_access_key:
        raise RuntimeError("AWS credentials are required to continue.")
    region = input(f"AWS region [{region or 'default'}]: ").strip() or region
    return aws_access_key_id, aws_secret_access_key, region


def get_s3_client(
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    anonymous: bool = False,
    prompt_if_missing: bool = True,
):
    """
    Build a boto3 S3 client.

    Credential precedence:
      1. anonymous=True            -> unsigned access (public reads, no creds).
      2. explicit keys             -> aws_access_key_id + aws_secret_access_key.
      3. profile                   -> a named profile from the AWS config.
      4. otherwise                 -> whatever is already configured on the
                                      device (env vars, default profile, IAM role).
      5. prompt_if_missing         -> if 1-4 resolve to nothing and we are on an
                                      interactive terminal, ask the user for keys.

    Credentials are therefore optional: pass them explicitly only when the
    device is not already configured. Raises RuntimeError if nothing usable
    resolves (and prompting is disabled or unavailable).
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

    # Nothing configured: ask the user as a last resort (interactive only).
    if session.get_credentials() is None and prompt_if_missing and sys.stdin.isatty():
        key_id, secret, region = _prompt_for_credentials(region)
        session = boto3.session.Session(
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
            region_name=region,
        )

    if session.get_credentials() is None:
        raise RuntimeError(
            "No AWS credentials found. Pass aws_access_key_id and "
            "aws_secret_access_key, set a profile, or configure credentials on "
            "the device (e.g. `aws configure` or environment variables)."
        )

    return session.client("s3")
