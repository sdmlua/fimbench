"""
Authors: Supath Dhital (sdhital@ua.edu), Dipsikha Devi (ddevi@ua.edu)
Updated: June 2026

Resolve the HUC8 watersheds a flood map overlaps via the public ArcGIS REST
service, so no HUC8 shapefile has to be loaded. get_intersected_huc8(geom, crs)
returns (huc8_list, name_list, state_list) ready for the metadata, matching the
tiers' previous shapefile-intersection output. get_dominant_huc8 returns the
same triple but with only the HUC8 that covers most of the flood extent, which
is what the per-watershed FEMA BLE maps need.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests
import geopandas as gpd
import pandas as pd
from shapely.prepared import prep


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

# One response can only carry so many features, so results are paged.
_PAGE_SIZE = 1000


def _bounds_4326(geom, crs):
    """Return the (minx, miny, maxx, maxy) of ``geom`` in EPSG:4326."""
    minx, miny, maxx, maxy = gpd.GeoSeries([geom], crs=crs).to_crs(4326).total_bounds
    return float(minx), float(miny), float(maxx), float(maxy)


def query_huc8(geom, crs):
    """
    Query the REST service for HUC8 features intersecting ``geom``.

    geom: a shapely geometry. crs: its CRS (EPSG int or anything pyproj accepts).
    Returns a GeoDataFrame (EPSG:4326) with columns HUC8, NAME, STATES; empty if
    nothing intersects.

    Only the bounding box of ``geom`` is sent, so the request stays the same
    small size no matter how many vertices the flood polygons have (a fine
    resolution raster easily vectorizes into hundreds of thousands of vertices,
    which the service rejects with HTTP 413). The bbox over-selects, and
    get_intersected_huc8 narrows the result down locally against the real
    geometry.
    """
    empty = gpd.GeoDataFrame({"HUC8": [], "NAME": [], "STATES": []}, geometry=[], crs=4326)
    if geom is None or geom.is_empty:
        return empty

    minx, miny, maxx, maxy = _bounds_4326(geom, crs)
    if not all(v == v for v in (minx, miny, maxx, maxy)):  # NaN bounds
        return empty

    params = {
        "f": "geojson",
        "where": "1=1",
        "geometry": f"{minx},{miny},{maxx},{maxy}",
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": 4326,
        "outFields": "HUC8,name,states",
        "returnGeometry": "true",
        "outSR": 4326,
        "resultRecordCount": _PAGE_SIZE,
    }

    # Page until the service stops reporting more features, so an arbitrarily
    # large extent still returns every HUC8 it touches.
    frames = []
    offset = 0
    while True:
        res = requests.post(
            f"{HUC8_REST_URL}/query", data={**params, "resultOffset": offset}, timeout=60
        )
        res.raise_for_status()
        payload = json.loads(res.content)
        features = payload.get("features") or []
        if features:
            frames.append(gpd.GeoDataFrame.from_features(features, crs=4326))
        if not features or not payload.get("exceededTransferLimit"):
            break
        offset += len(features)

    if not frames:
        return empty

    gdf = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), geometry="geometry", crs=4326)

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

    # The REST query used the bounding box, so narrow it down here against the
    # real geometry. prep() keeps this cheap for very detailed flood polygons.
    g = gpd.GeoSeries([geom], crs=crs).to_crs(4326).iloc[0]
    hit = gdf[gdf.geometry.apply(prep(g).intersects)].copy()
    if hit.empty:
        # Sliver geometries can miss on exact predicates; retry with a ~0.1 m
        # tolerance before giving up.
        hit = gdf[gdf.geometry.apply(prep(g.buffer(1e-6)).intersects)].copy()
    if hit.empty:
        return [], [], "USA"

    return _format_huc8_lists(hit)


def _format_huc8_lists(hit):
    """Build the (huc8_list, name_list, state_list) triple the tiers write out."""
    huc8_list = sorted(hit["HUC8"].dropna().unique().tolist())
    name_list = sorted(hit["NAME"].dropna().unique().tolist())
    raw_states = hit["STATES"].dropna().unique().tolist()
    state_set = set()
    for s in raw_states:
        for part in str(s).split(","):
            state_set.add(part.strip())
    state_list = ", ".join(sorted(list(state_set)))
    return huc8_list, name_list, state_list


# FEMA BLE maps are produced per watershed, so a single HUC8 should own almost
# all of the flood extent; anything else is edge overlap from neighbours.
DOMINANT_HUC8_FRACTION = 0.70

# Equal-area CRS (CONUS Albers) so the area shares are not latitude-distorted.
_AREA_CRS = 5070


def get_dominant_huc8(geom, crs, min_fraction=DOMINANT_HUC8_FRACTION, log=None):
    """
    Return (huc8_list, name_list, state_list) for the single HUC8 that holds
    most of ``geom``'s area.

    Same output shape as get_intersected_huc8 -- huc8_list and name_list are
    lists (of one entry), state_list a comma-joined string -- so metadata keys
    and value formats stay identical. The HUC8 covering at least ``min_fraction``
    of the flood area wins; if none reaches that share the largest one is used
    and the shares are logged. Falls back to ([], [], "USA") when nothing
    intersects.
    """
    gdf = query_huc8(geom, crs)
    if gdf.empty:
        return [], [], "USA"

    # Measure the overlap in an equal-area projection.
    g = gpd.GeoSeries([geom], crs=crs).to_crs(_AREA_CRS).iloc[0]
    total = g.area
    if total <= 0:
        return [], [], "USA"

    areas = gdf.to_crs(_AREA_CRS).geometry.apply(
        lambda h: g.intersection(h).area if g.intersects(h) else 0.0
    )
    shares = areas / total
    if shares.max() <= 0:
        return [], [], "USA"

    top = shares.idxmax()
    if log is not None and shares[top] < min_fraction:
        ranked = ", ".join(
            f"{gdf.loc[i, 'HUC8']}={shares[i]:.0%}"
            for i in shares.sort_values(ascending=False).index[:4]
            if shares[i] > 0
        )
        log(
            f"No HUC8 covers {min_fraction:.0%} of the flood extent "
            f"({ranked}); using the largest, {gdf.loc[top, 'HUC8']}."
        )

    return _format_huc8_lists(gdf.loc[[top]])
