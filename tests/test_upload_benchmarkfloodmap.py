"""
Test: push a standardized flood map to S3 (fimbench.publish.upload_benchmarkfloodmap).

AWS keys are optional. Leave them None to use the device's configured
credentials; if none are found you are prompted for them on an interactive
terminal. Pass explicit keys (below) to skip that lookup.
Run with pytest; comment out any test function you do not want to run.
"""

import fimbench

local_upload_path = "path/to/local/standardized/folder"


def test_upload_benchmarkfloodmap_device_creds():
    # Use whatever AWS credentials are configured on the device (or be prompted).
    fimbench.upload_benchmarkfloodmap(
        local_upload_path,
        bucket="sdmlab",
        prefix="FIM_Database/",
    )


def test_upload_benchmarkfloodmap_explicit_keys():
    # Provide explicit keys (skips the device lookup / prompt).
    fimbench.upload_benchmarkfloodmap(
        local_upload_path,
        bucket="sdmlab",
        prefix="FIM_Database/",
        aws_access_key_id="AKIA...",
        aws_secret_access_key="...",
        region="us-east-1",
    )
