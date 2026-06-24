"""
Test for building the FIM catalog (`fimbench.webcontent_utils.FIMCatalogBuilder`).

It crawls S3 and produces the output catalog JSON and the FIM extents GeoJSON.
"""

import os

import pytest

from fimbench.webcontent_utils import FIMCatalogBuilder


def test_builder_constructs():
    """The catalog builder is importable and constructible."""
    builder = FIMCatalogBuilder(
        bucket="sdmlab",
        prefix="FIM_Database/",
        out_dir="./out",
    )
    assert builder is not None


@pytest.mark.skipif(
    os.environ.get("FIMBENCH_LIVE") != "1",
    reason="crawls S3; set FIMBENCH_LIVE=1 to run",
)
def test_build_catalog():
    # It will build the catalog and give the output json and FIM extents geojson file
    builder = FIMCatalogBuilder(
        bucket="sdmlab",
        prefix="FIM_Database/",
        out_dir="./out",
    )
    builder.build_catalog()
