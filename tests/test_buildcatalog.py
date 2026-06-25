"""
Test: build the FIM catalog (fimbench.webcontent_utils.FIMCatalogBuilder).

Crawls S3 and writes catalog_core.json + FIM_extents.geojson.
"""


import fimbench


def test_build_catalog():
    builder = fimbench.FIMCatalogBuilder(
        bucket="sdmlab",
        prefix="FIM_Database/",
        out_dir="./out",
    )
    builder.build_catalog()


if __name__ == "__main__":
    # test_build_catalog()
    pass
