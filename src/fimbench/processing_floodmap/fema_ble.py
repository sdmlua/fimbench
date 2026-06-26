"""
Authors: Supath Dhital (sdhital@ua.edu), Dipsikha Devi (ddevi@ua.edu)
Updated: June 2026

FEMA Base Level Engineering (BLE) flood map processing.

Standardizes FEMA BLE synthetic (return-period) flood rasters into the FIM
database format: renamed GeoTIFF, metadata.json, and AOI.gpkg per flood map.
"""

import json
import shutil
import tempfile
from pathlib import Path
import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.validation import make_valid
import geopandas as gpd

from .._log import log as _log
from .utils import get_intersected_huc8, list_input_tifs


class FemaBleProcessor:
    """Standardize FEMA Base Level Engineering flood maps for the FIM database."""

    SENSOR_CODE = "BLE"
    Full_Form = "Base Level Engineering"
    SOURCE = "NOAA/NWS Office of Water Prediction (OWP)"

    NODATA_VAL = -9999
    BLOCK_SIZE = 512
    SIMPLIFY_TOL = 0.0001  # ~11 m at the equator

    def __init__(self, *, sensor_code=None, full_form=None, source=None,
                 nodata_val=None, block_size=None, simplify_tol=None):
        # Class attributes are the defaults.
        if sensor_code is not None:
            self.SENSOR_CODE = sensor_code
        if full_form is not None:
            self.Full_Form = full_form
        if source is not None:
            self.SOURCE = source
        if nodata_val is not None:
            self.NODATA_VAL = nodata_val
        if block_size is not None:
            self.BLOCK_SIZE = block_size
        if simplify_tol is not None:
            self.SIMPLIFY_TOL = simplify_tol

        # Folder for intermediate rasters; set per run in process().
        self._work_dir = None

    def log(self, msg):
        _log(msg)

    def _work_path(self, name):
        # Place an intermediate file in the work dir (else next to the input).
        if self._work_dir is not None:
            return Path(self._work_dir) / name
        return Path(name)

    # Assign nodata, datatype and tile size
    def process_tif(self, input_tif, nodata_val=None, block_size=None):
        nodata_val = self.NODATA_VAL if nodata_val is None else nodata_val
        block_size = self.BLOCK_SIZE if block_size is None else block_size
        input_tif = Path(input_tif)
        output_tif = self._work_path(input_tif.stem + "_nodata.tif")
        output_tif.parent.mkdir(parents=True, exist_ok=True)

        with rasterio.open(input_tif) as src:
            m = src.read(masked=True)
            src_dtype = np.dtype(src.dtypes[0])
            if np.issubdtype(src_dtype, np.floating):
                out_dtype = "float32"
            else:
                out_dtype = "int32"

            out = np.full(m.shape, nodata_val, dtype=out_dtype)
            valid = ~m.mask
            out[valid] = m.data[valid].astype(out_dtype, copy=False)

            profile = src.profile.copy()
            profile.update(
                dtype=out_dtype,
                nodata=nodata_val,
                tiled=True,
                blockxsize=block_size,
                blockysize=block_size,
                compress="lzw"
            )

            with rasterio.open(output_tif, "w", **profile) as dst:
                dst.write(out)
                try:
                    dst.update_tags(**src.tags())
                except Exception:
                    pass

        return output_tif

    # Reproject to the target coordinate system (default EPSG:5070)
    def reproject_raster(self, input_file, target_epsg):
        input_file = Path(input_file)
        output_file = self._work_path(input_file.stem + f"_reprojected_{target_epsg}.tif")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with rasterio.open(input_file) as src:
            transform, width, height = calculate_default_transform(
                src.crs, f"EPSG:{target_epsg}", src.width, src.height, *src.bounds)

            metadata = src.meta.copy()
            metadata.update({
                "crs": f"EPSG:{target_epsg}",
                "transform": transform,
                "width": width,
                "height": height,
                "compress": "lzw"
            })

            with rasterio.open(output_file, "w", **metadata) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=f"EPSG:{target_epsg}",
                        resampling=Resampling.nearest
                    )
        return output_file

    # Extract the resolution from the projected file
    def get_resolution_string(self, geo_tif_5070):
        with rasterio.open(geo_tif_5070) as src:
            res_x, res_y = src.res
            avg_res = (res_x + res_y) / 2.0
            rounded_res = round(avg_res, 1)
            res_str = f"{str(rounded_res).replace('.', '_')}m"   # e.g., 10.0 -> "10_0m"
            res_txt = f"{rounded_res:.2f} m"
        return rounded_res, res_str, res_txt

    def get_raster_centroid(self, out_4326):
        with rasterio.open(out_4326) as src:
            b = src.bounds
            centroid_x = (b.left + b.right) / 2
            centroid_y = (b.top + b.bottom) / 2
            crs = src.crs

        return centroid_x, centroid_y, crs, b

    # Decimal degrees to DMS, e.g. 95 31'44" W and 31 04'36" N -> 953144W310436N
    def decimal_to_dms_str(self, dec, is_lat=True):
        direction = ''
        if is_lat:
            direction = 'N' if dec >= 0 else 'S'
        else:
            direction = 'E' if dec >= 0 else 'W'

        dec = abs(dec)
        degrees = int(dec)
        minutes = int((dec - degrees) * 60)
        seconds = int(((dec - degrees) * 60 - minutes) * 60)

        return f"{degrees:02d}{minutes:02d}{seconds:02d}{direction}"

    def build_metadata_dict(
        self, src_4326, src_5070, new_filename, res_m_float, res_txt, dms_code, x, y, state_list, huc8_list, name_list, EVENT
    ):
        with rasterio.open(src_4326) as src:
            meta = {
                "File_Name": new_filename,
                "Full form of the sensor code": self.Full_Form,
                "HUC8": huc8_list,
                "Format": src.driver,
                "Nodata_Value": src.nodata,
                "Resolution in meter": res_m_float,
                "Datatype": src.dtypes[0],
                "Compression Type": src.tags(ns="IMAGE_STRUCTURE"),
                "Extent": {
                    "xmin": src.bounds.left,
                    "ymin": src.bounds.bottom,
                    "xmax": src.bounds.right,
                    "ymax": src.bounds.top
                },
                "DMS_Code_centroid": dms_code,
                "Projection": src.crs.to_string() if src.crs else "Unknown",
                "Bands": src.count,
                "Rows": src.height,
                "Columns": src.width,
                "State": f"{state_list}, USA" if state_list else "USA",
                "Description": f"",
                "River Basin Name": name_list,
                "Source": self.SOURCE,
                "Location of the centroid of the flood map": (x, y),
                "Synthetic Flooding Event (return period (years))": EVENT,
                "Keywords": ["flood", "hazard", "GIS"],
                "Access_Rights": "Public",
                "References": [
                    "1. Cohen, S., Baruah, A., Nikrou, P., Tian, D., & Liu, H. (2025). Toward robust evaluations of flood inundation predictions using remote sensing derived benchmark maps. Water Resources Research, 61(8), e2024WR039574.",
                    "2. Munasinghe, D., Cohen, S., Tian, D., Liu, H., Baruah, A., and Devi, D. (2025). A Database of Flood Maps using high-resolution Airborne Imagery and Machine Learning Models. In: CIROH Developers' Conference, May 28-30, 2025.",
                    "3. Devi, D., Dhital, S., Munasinghe, D., Cohen, S., Baruah, A., Chen, Y., ... & Pruitt, C. (2025). A Framework for the Evaluation of Flood Inundation Predictions Over Extensive Benchmark Databases.",
                    "4. Tian.D, Liu.H,  Wang.L, Cohen.S, Thapa.P (2024).Enhancing satellite image-derived flood maps with hydrologically guided region growing method and high-resolution DEMs.Chapman Conference on Remote Sensing of the Water Cycle"
                ]
            }

        with rasterio.open(src_5070) as src_geom:
            arr = src_geom.read(1, masked=True)
            geom_crs = src_geom.crs
            mask = arr > 0  # 1 is flood, 0 is dry

            results = (
                {'properties': {'raster_val': v}, 'geometry': s}
                for i, (s, v) in enumerate(
                    shapes(arr, mask=mask, transform=src_geom.transform)
                )
            )

        geoms = list(results)
        if not geoms:
            self.log("No flooded areas found in 5070 raster.")
            return meta, None

        gdf1 = gpd.GeoDataFrame.from_features(geoms)
        gdf1.set_crs(geom_crs, inplace=True)

        if self.SIMPLIFY_TOL:
            gdf1['geometry'] = gdf1.simplify(self.SIMPLIFY_TOL, preserve_topology=True)
            gdf1['geometry'] = gdf1.make_valid()

        unified_geom = unary_union(gdf1.geometry)

        return meta, unified_geom

    def raster_to_polygon(self, in_raster, gpkg_path, metadata_row, valid_classes=(0, 1, 2), nodata=None, connectivity=8):
        nodata = self.NODATA_VAL if nodata is None else nodata
        in_raster = Path(in_raster)
        with rasterio.open(in_raster) as src:
            arr = src.read(1)
            tfm = src.transform
            crs = src.crs
            mask = arr != nodata
            polygons = []
            for geom, val in shapes(arr, mask=mask, transform=tfm, connectivity=connectivity):
                if val in valid_classes:
                    poly = shape(geom)
                    if not poly.is_valid:
                        poly = poly.buffer(0)
                    if not poly.is_empty:
                        polygons.append(poly)

        if not polygons:
            raise ValueError("No polygons found to build AOI.")

        unified = unary_union(polygons)
        gdf = gpd.GeoDataFrame([metadata_row], geometry=[unified], crs=crs)
        gdf.to_file(gpkg_path, layer="AOI", driver="GPKG")

    def raster_data_bbox(self, in_raster, gpkg_path, metadata_row, nodata=None):
        nodata = self.NODATA_VAL if nodata is None else nodata
        with rasterio.open(in_raster) as src:
            arr = src.read(1)
            crs = src.crs
            valid = arr != nodata
            if np.issubdtype(arr.dtype, np.floating):
                valid &= ~np.isnan(arr)
            valid_mask = valid.astype(np.uint8)
            geoms = [
                shape(geom)
                for geom, _ in shapes(valid_mask, mask=valid_mask, transform=src.transform)
            ]

        if not geoms:
            raise ValueError("No valid data found to build AOI.")

        unified = unary_union(geoms)
        if self.SIMPLIFY_TOL:
            unified = unified.simplify(self.SIMPLIFY_TOL, preserve_topology=True)
            unified = make_valid(unified)

        gdf = gpd.GeoDataFrame([metadata_row], geometry=[unified], crs=crs)
        gdf.to_file(gpkg_path, layer="AOI", driver="GPKG")

    def process(self, input_path, base_dest, event, intermediate_folder=None):
        """
        Process a folder of rasters or a single .tif.

        event: the synthetic return-period event (e.g. "100"), applied to all files.
        intermediate_folder: where temporary rasters are written; defaults to a
        fresh temp dir. Removed (best-effort) when processing finishes.
        """
        BASE_DEST = Path(base_dest)
        EVENT = event

        tif_list = list_input_tifs(input_path)
        if not tif_list:
            self.log(f"No .tif files found under {input_path}")
            return

        self.log(f"Found {len(tif_list)} .tif file(s) under {input_path}")

        # Set up the intermediate work dir (temp if not provided).
        if intermediate_folder is None:
            self._work_dir = Path(tempfile.mkdtemp(prefix="fimbench_"))
        else:
            self._work_dir = Path(intermediate_folder)
        self._work_dir.mkdir(parents=True, exist_ok=True)

        try:
            for tif in tif_list:
                try:
                    self.log(f"Processing: {tif}")

                    # Pre-processing steps
                    nodata_tif = self.process_tif(tif)
                    out_5070 = self.reproject_raster(nodata_tif, 5070)
                    out_4326 = self.reproject_raster(nodata_tif, 4326)
                    res_m_float, res_str, res_txt = self.get_resolution_string(out_5070)

                    # Centroid (4326) + DMS
                    x, y, raster_crs, b = self.get_raster_centroid(out_4326)
                    lon_str = self.decimal_to_dms_str(x, is_lat=False)
                    lat_str = self.decimal_to_dms_str(y, is_lat=True)
                    dms_code = lon_str + lat_str

                    # Metadata and geometry generation (return period comes from EVENT)
                    temp_filename = f"{self.SENSOR_CODE}_{res_str}_{EVENT}_{dms_code}_BM.tif"

                    meta_dict, unified_geom = self.build_metadata_dict(
                        out_4326, out_5070, temp_filename, res_m_float, res_txt, dms_code,
                        x, y, "", [], [], EVENT
                    )

                    # HUC overlay via the ArcGIS REST service (unified_geom is in EPSG:5070)
                    huc8_list, name_list, state_list = get_intersected_huc8(unified_geom, 5070)

                    # Update the metadata dictionary with the actual HUC results
                    meta_dict["HUC8"] = huc8_list
                    meta_dict["River Basin Name"] = name_list
                    meta_dict["State"] = f"{state_list}, USA" if state_list else "USA"
                    meta_dict["Description"] = (
                       f"The Flood Inundation Map (FIM) corresponds to FEMA Base Level Engineering "
                        f"for the {EVENT} flood with a spatial resolution of {res_txt}. "
                        f"The corresponding HUC IDs are {huc8_list}"
                    )

                    # File management
                    folder_name = f"{self.SENSOR_CODE}_{EVENT}_{dms_code}"
                    destination_folder = BASE_DEST / folder_name
                    destination_folder.mkdir(parents=True, exist_ok=True)

                    new_filename = f"{self.SENSOR_CODE}_{res_str}_{EVENT}_{dms_code}_BM.tif"
                    new_path = destination_folder / new_filename

                    shutil.copy2(out_4326, new_path)
                    self.log(f"Saved GeoTIFF: {new_path.name}")

                    # Save JSON
                    metadata_filename = new_path.name.replace("BM.tif", "metadata.json")
                    metadata_path = new_path.parent / metadata_filename
                    with open(metadata_path, "w") as jf:
                        json.dump(meta_dict, jf, indent=4)
                    self.log(f"Wrote metadata: {metadata_path.name}")

                    # AOI.gpkg
                    gpkg_path = new_path.parent / new_path.name.replace("BM.tif", "AOI.gpkg")
                    self.raster_data_bbox(out_4326, gpkg_path, meta_dict, nodata=self.NODATA_VAL)
                    self.log(f"Wrote AOI: {gpkg_path.name}")

                except Exception as e:
                    self.log(f"Skipped {tif.name} due to error: {e}")
                    import traceback
                    traceback.print_exc()

            self.log("Done.")
        finally:
            # Remove the intermediate work dir so the input folder stays clean
            # (best-effort; ignore if it cannot be removed).
            shutil.rmtree(self._work_dir, ignore_errors=True)
            self._work_dir = None


def process(input_path, base_dest, event, intermediate_folder=None, **overrides):
    """
    Convenience wrapper: run FemaBleProcessor over a folder or a single .tif.

    event: synthetic return-period event (e.g. "100").
    intermediate_folder: temp raster dir (defaults to a temp dir, removed after).
    Config overrides (e.g. source=...) are passed to the processor.
    """
    FemaBleProcessor(**overrides).process(
        input_path, base_dest, event, intermediate_folder=intermediate_folder
    )
