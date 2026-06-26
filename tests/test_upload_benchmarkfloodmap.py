"""
Test: push a standardized flood map to S3 (fimbench.publish.upload_benchmarkfloodmap).

Optional AWS keys; leave None to use the device's configured credentials.
Run with pytest; comment out any test function you do not want to run.
"""

import fimbench

local_upload_path = "path/to/local/standardized/folder"


def test_upload_benchmarkfloodmap():
    fimbench.upload_benchmarkfloodmap(
        local_upload_path,
        bucket="sdmlab",
        prefix="FIM_Database/",
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region=None,
    )
