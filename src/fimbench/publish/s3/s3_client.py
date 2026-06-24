"""
S3 client / session construction for the FIM database bucket.

Centralizes how the rest of the package obtains a boto3 S3 client so that
credentials, region, profiles and anonymous (UNSIGNED) access are configured
in exactly one place.

To be populated.
"""

from __future__ import annotations

# Default bucket / prefix for the FIM database. Adjust as the schema settles.
DEFAULT_BUCKET = "sdmlab"
DEFAULT_PREFIX = "FIM_Database/"


# def get_s3_client(profile=None, anonymous=False, region=None): ...
