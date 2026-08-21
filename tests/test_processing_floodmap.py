"""
Test: standardize raw flood maps (fimbench.processing_floodmap).

Each writes the renamed GeoTIFF + metadata.json + AOI.gpkg.

input_path can be a FOLDER (every .tif under it) or a single .tif.
  - tier1/2/3: flood_date is inferred per file from the filename when processing
    a folder; pass flood_date=... for a single raster.
  - fema_ble: pass event (return period).
  - hwm: pass start_date and end_date.
Config defaults (source, sensor_code, ...) can be overridden as keyword args.
Run with pytest; comment out any test function you do not want to run.
"""

import fimbench

input_folder = "path/to/the/folder"
input_tif = "path/to/input/tif"
out_dir = "/Users/Supath/Downloads/Data/out"
event = "100"
start_date = "10160928"
end_date = "20161009"
flood_date = "20160928"
intermediate_folder = None  # None -> a temp dir is used and removed afterward

# Config overrides. None -> keep the module default.
source = "Supath Dhital"  # e.g. "Dr. X, ..." Creator name and email
nodata_val = None  # default -9999
block_size = None  # default 512 (GeoTIFF tile size)
simplify_tol = None  # default 0.0001 deg (~11 m) geometry simplify tolerance

# def test_processing_tier1_folder():
#     # Folder: flood_date inferred per file
#     fimbench.Tier1Processor(source=source, nodata_val=nodata_val, block_size=block_size, simplify_tol=simplify_tol).process(
#         input_folder, out_dir, intermediate_folder=intermediate_folder
#     )


def test_processing_tier1_single():
    # Single raster: pass the flood_date; override source if you want
    fimbench.Tier1Processor(
        source=source, nodata_val=nodata_val, block_size=block_size, simplify_tol=simplify_tol
    ).process(input_tif, out_dir, flood_date=flood_date, intermediate_folder=intermediate_folder)


# def test_processing_tier2_folder():
#     fimbench.Tier2Processor(source=source, nodata_val=nodata_val, block_size=block_size, simplify_tol=simplify_tol).process(
#         input_folder, out_dir, intermediate_folder=intermediate_folder
#     )


# def test_processing_tier2_single():
#     fimbench.Tier2Processor(source=source, nodata_val=nodata_val, block_size=block_size, simplify_tol=simplify_tol).process(
#         input_tif, out_dir, flood_date=flood_date, intermediate_folder=intermediate_folder
#     )


# def test_processing_tier3_folder():
#     fimbench.Tier3Processor(source=source, nodata_val=nodata_val, block_size=block_size, simplify_tol=simplify_tol).process(
#         input_folder, out_dir, intermediate_folder=intermediate_folder
#     )


def test_processing_tier3_single():
    fimbench.Tier3Processor(
        source=source, nodata_val=nodata_val, block_size=block_size, simplify_tol=simplify_tol
    ).process(input_tif, out_dir, flood_date=flood_date, intermediate_folder=intermediate_folder)


def test_processing_fema_ble():
    fimbench.FemaBleProcessor(
        source=source, nodata_val=nodata_val, block_size=block_size, simplify_tol=simplify_tol
    ).process(input_folder, out_dir, event, intermediate_folder=intermediate_folder)


# def test_processing_hwm():
#     fimbench.HwmProcessor(source=source, nodata_val=nodata_val, block_size=block_size, simplify_tol=simplify_tol).process(
#         input_tif, out_dir, start_date, end_date, intermediate_folder=intermediate_folder
#     )
