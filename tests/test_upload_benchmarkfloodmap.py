"""
Test: push a standardized flood map to S3 (fimbench.publish.upload_benchmarkfloodmap).

Optional AWS keys; leave None to use the device's configured credentials.
"""

LOCAL_UPLOAD_PATH = "path/to/local/standardized/folder"

import fimbench


def test_upload_benchmarkfloodmap():
    fimbench.upload_benchmarkfloodmap(
        LOCAL_UPLOAD_PATH,
        bucket="sdmlab",
        prefix="FIM_Database/",
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region=None,
    )


if __name__ == "__main__":
    # test_upload_benchmarkfloodmap()
    pass
