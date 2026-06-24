"""
fimbench.publish.s3
===================

Low-level AWS S3 interaction layer for the FIM database.

Everything that talks to the S3 bucket lives here, so that the rest of the
package depends on a single, well-tested S3 access layer instead of each
module constructing its own boto3 sessions. It backs the S3 push performed by
:mod:`fimbench.publish.upload_catalogntilesintos3` and is also used by
:mod:`fimbench.query` for read-only discovery.

Modules
-------
s3_client
    Session / client construction (signed and anonymous/unsigned access).
s3_io
    Object-level helpers: list, head, get, put, upload/download, presigned URLs.
"""

from __future__ import annotations

__all__: list[str] = []
