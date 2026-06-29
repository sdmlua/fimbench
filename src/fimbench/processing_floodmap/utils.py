"""
Authors: Supath Dhital (sdhital@ua.edu), Dipsikha Devi (ddevi@ua.edu)
Updated: June 2026

Resolve the HUC8 watersheds a flood map overlaps via the public ArcGIS REST
service, so no HUC8 shapefile has to be loaded. get_intersected_huc8(geom, crs)
returns (huc8_list, name_list, state_list) ready for the metadata, matching the
tiers' previous shapefile-intersection output.
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import requests
import geopandas as gpd
from shapely.ops import unary_union


def list_input_tifs(input_path):
    """
    Resolve input_path to a list of .tif files.

    Accepts a single .tif file or a folder (searched recursively). Raises
    FileNotFoundError if the path does not exist.
    """
    p = Path(input_path)
    if p.is_file():
        return [p]
    if p.is_dir():
        return sorted(f for f in p.rglob("*.tif") if f.is_file())
    raise FileNotFoundError(f"Input path not found: {p}")


# Public ArcGIS REST service for WBD HUC8 boundaries.
HUC8_REST_URL = (
    "https://services.arcgis.com/ts4gk3YgS68yLGFl/arcgis/rest/services/"
    "HUC8_Boundaries/FeatureServer/0"
)

def _rings(geometry):
    # ESRI JSON rings from a Polygon / MultiPolygon.
    if geometry.geom_type == "Polygon":
        return [list(geometry.exterior.coords)]
    if hasattr(geometry, "geoms"):
        return [list(p.exterior.coords) for p in geometry.geoms]
    return []


def query_huc8(geom, crs):
    """
    Query the REST service for HUC8 features intersecting ``geom``.

    geom: a shapely geometry. crs: its CRS (EPSG int or anything pyproj accepts).
    Returns a GeoDataFrame (EPSG:4326) with columns HUC8, NAME, STATES; empty if
    nothing intersects.
    """
    # Reproject the query geometry to WGS84 for the ESRI request.
    g = gpd.GeoSeries([geom], crs=crs).to_crs(4326)
    rings = _rings(unary_union(g.geometry))
    esri_geom = {"rings": rings, "spatialReference": {"wkid": 4326}}

    params = {
        "f": "geojson",
        "where": "1=1",
        "geometry": json.dumps(esri_geom),
        "geometryType": "esriGeometryPolygon",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": 4326,
        "outFields": "HUC8,name,states",
        "returnGeometry": "true",
        "outSR": 4326,
    }

    res = requests.post(f"{HUC8_REST_URL}/query", data=params, timeout=30)
    res.raise_for_status()
    gdf = gpd.read_file(BytesIO(res.content))
    if gdf.empty:
        return gdf

    # Match the column names the tiers expect.
    gdf = gdf.rename(columns={"name": "NAME", "states": "STATES"})
    return gdf


def get_intersected_huc8(geom, crs):
    """
    Return (huc8_list, name_list, state_list) for the HUC8s overlapping ``geom``.

    Reproduces the tiers' previous output: sorted unique HUC8 and NAME, and a
    comma-split/sorted/de-duplicated STATES string. Falls back to
    ([], [], "USA") when nothing intersects.
    """
    gdf = query_huc8(geom, crs)
    if gdf.empty:
        return [], [], "USA"

    # Keep only rows that truly intersect the geometry (REST query is bbox-ish).
    g = gpd.GeoSeries([geom], crs=crs).to_crs(4326).iloc[0]
    hit = gdf[gdf.intersects(g)].copy()
    if hit.empty:
        return [], [], "USA"

    huc8_list = sorted(hit["HUC8"].dropna().unique().tolist())
    name_list = sorted(hit["NAME"].dropna().unique().tolist())
    raw_states = hit["STATES"].dropna().unique().tolist()
    state_set = set()
    for s in raw_states:
        for part in str(s).split(','):
            state_set.add(part.strip())
    state_list = ", ".join(sorted(list(state_set)))
    return huc8_list, name_list, state_list
