"""
Test: make vector tiles (fimbench.webcontent_utils.CatalogandTileManager).

Builds tiles from FIM extents and optionally uploads tiles + catalog to S3.
"""


import fimbench

def test_work_with_tiles():
    manager = fimbench.CatalogandTileManager(
        out_dir="./out",
        s3_bucket="sdmlab",
        s3_prefix="FIM_Database/FIM_Viz",
        min_zoom=3,
        max_zoom=14,
    )
    manager.execute(
        source_path="./out/FIM_extents.geojson",
        catalog_path="./out/catalog_core.json",
        run_tiling=True,
        upload_tiles=True,
        upload_json=True,
    )


if __name__ == "__main__":
    # test_work_with_tiles()
    pass
