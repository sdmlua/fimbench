"""
Test for tiling + S3 upload (`fimbench.webcontent_utils.CatalogandTileManager`).

Builds vector tiles from FIM extents and (optionally) uploads tiles + catalog
to S3.
"""

import os

import pytest

from fimbench.webcontent_utils import CatalogandTileManager


def test_manager_constructs():
    """The tile manager is importable and constructible."""
    manager = CatalogandTileManager(
        out_dir="./out",
        s3_bucket="sdmlab",
        s3_prefix="FIM_Database/FIM_Viz",
        min_zoom=3,
        max_zoom=14,
    )
    assert manager is not None


@pytest.mark.skipif(
    os.environ.get("FIMBENCH_LIVE") != "1",
    reason="needs tippecanoe / mb-util and hits S3; set FIMBENCH_LIVE=1 to run",
)
def test_work_with_tiles():
    manager = CatalogandTileManager(
        out_dir="./out",
        s3_bucket="sdmlab",  # S3 Bucket name if user wants to upload to S3
        s3_prefix="FIM_Database/FIM_Viz",  # Path to upload the catalog and tiles
        min_zoom=3,
        max_zoom=14,
    )

    # Example 1: Upload BOTH Tiles and JSON
    manager.execute(
        source_path="./out/FIM_extents.geojson",  # FIM extent geojson file path
        catalog_path="./out/catalog_core.json",
        run_tiling=True,
        upload_tiles=True,
        upload_json=True,
    )

    # # Example 2: Upload JSON ONLY (No tiling run)
    # manager.execute(
    #     catalog_path="./out/catalog_core.json",
    #     run_tiling=False,
    #     upload_tiles=False,
    #     upload_json=True,       # Upload catalog.core and FIM_Extents both
    # )

    # # Example 3: RUN Locally - No upload into s3
    # manager.execute(
    #     source_path="data.geojson",
    #     run_tiling=True,
    #     upload_tiles=False,
    #     upload_json=False,
    # )
