"""
Test: query benchmark FIMs from the catalog (fimbench.query.benchFIMquery).

Supports direct filename, AOI (raster/boundary), exact date, or date range,
with optional area overlap and download.
"""

RASTER_PATH = "path/to/raster"
BOUNDARY_PATH = "path/to/boundary"


import fimbench


def test_benchmark_fimquery():
    response = fimbench.benchFIMquery(
        raster_path=RASTER_PATH,
        # boundary_path=BOUNDARY_PATH,
        # huc8="03020201",
        # event_date="2016-05-01",
        # start_date="2016-04-01",
        # end_date="2026-01-01",
        file_name="HWM_10_0m_20160928_20161009_780051W352232N_BM.tif",
        # tier="tier4",
        # area=True,
        download=True,
        # out_dir="../downloads/",
    )
    print(response)


if __name__ == "__main__":
    # test_benchmark_fimquery()
    pass
