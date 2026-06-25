"""
Test: standardize raw flood maps (fimbench.processing_floodmap).

Each writes the renamed GeoTIFF + metadata.json + AOI.gpkg.
"""

import fimbench

INPUT_ROOT = "path/to/input/folder/with/rasters"
INPUT_TIF = "path/to/raster_file"
BASE_DEST = "path/to/destination_folder"
EVENT = "100"
START_DATE = "160928"
END_DATE = "161009"


def test_processing_tier1():
    fimbench.Tier1Processor().process(INPUT_ROOT, BASE_DEST)


def test_processing_tier2():
    fimbench.Tier2Processor().process(INPUT_ROOT, BASE_DEST)


def test_processing_tier3():
    fimbench.Tier3Processor().process(INPUT_ROOT, BASE_DEST)


def test_processing_fema_ble():
    fimbench.FemaBleProcessor().process(INPUT_ROOT, BASE_DEST, EVENT)


def test_processing_hwm():
    fimbench.HwmProcessor().process(INPUT_TIF, BASE_DEST, START_DATE, END_DATE)


if __name__ == "__main__":
    # Uncomment ONE at a time.
    # test_processing_tier1()
    # test_processing_tier2()
    # test_processing_tier3()
    # test_processing_fema_ble()
    # test_processing_hwm()
    pass
