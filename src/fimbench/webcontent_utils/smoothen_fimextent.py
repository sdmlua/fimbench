# Smoothen the FIM extents for vizualization
import json
import geopandas as gpd
import numpy as np
import os
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely import simplify, set_precision

from .._log import log as _log


def chaikin_smooth(coords, iterations=3):
    pts = np.array(coords)
    for _ in range(iterations):
        L = pts[:-1]
        R = pts[1:]
        new_pts = np.empty((2 * len(L), 2))
        new_pts[0::2] = 0.75 * L + 0.25 * R
        new_pts[1::2] = 0.25 * L + 0.75 * R
        pts = np.vstack([new_pts, new_pts[0]])
    return pts.tolist()


def smooth_polygon(geom, iterations=3):
    if geom is None or geom.is_empty:
        return geom
    if geom.geom_type == "Polygon":
        exterior = chaikin_smooth(list(geom.exterior.coords), iterations)
        interiors = [chaikin_smooth(list(ring.coords), iterations) for ring in geom.interiors]
        return Polygon(exterior, interiors)
    elif geom.geom_type == "MultiPolygon":
        return MultiPolygon([smooth_polygon(p, iterations) for p in geom.geoms])
    return geom


def round_coords(geom, precision=5):
    if geom is None or geom.is_empty:
        return geom
    if geom.geom_type == "Polygon":
        exterior = [(round(x, precision), round(y, precision)) for x, y in geom.exterior.coords]
        interiors = [
            [(round(x, precision), round(y, precision)) for x, y in ring.coords]
            for ring in geom.interiors
        ]
        return Polygon(exterior, interiors)
    elif geom.geom_type == "MultiPolygon":
        return MultiPolygon([round_coords(p, precision) for p in geom.geoms])
    return geom


def process_flood_extents(
    input_path,
    output_path,
    pre_tolerance=30,
    post_tolerance=10,
    smooth_iterations=4,
    coord_precision=5,
):
    _log(f"Loading: {os.path.basename(input_path)}...")

    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Preserve all original attributes exactly as-is, indexed by row position
    attr_lookup = [feat["properties"] for feat in raw["features"]]
    _log(f"Loaded {len(attr_lookup)} features.")

    gdf = gpd.read_file(input_path, engine="pyogrio")
    gdf.columns = gdf.columns.str.strip()
    _log(f"Rows: {len(gdf)}")

    utm_crs = gdf.estimate_utm_crs()
    gdf = gdf.to_crs(utm_crs)
    _log(f"Projected to UTM: {utm_crs.to_epsg()}")

    gdf["geometry"] = simplify(
        gdf.geometry.values, tolerance=pre_tolerance, preserve_topology=False
    )
    gdf["geometry"] = set_precision(gdf.geometry.values, grid_size=1.0)

    _log(f"Smoothing (iterations={smooth_iterations})...")
    gdf["geometry"] = gdf["geometry"].apply(
        lambda g: smooth_polygon(g, iterations=smooth_iterations)
    )

    if post_tolerance > 0:
        gdf["geometry"] = simplify(
            gdf.geometry.values, tolerance=post_tolerance, preserve_topology=True
        )

    gdf = gdf.to_crs("EPSG:4326")
    gdf["geometry"] = gdf["geometry"].apply(lambda g: round_coords(g, coord_precision))

    _log("Assembling output GeoJSON...")
    features = []
    for i, row in gdf.iterrows():
        features.append(
            {"type": "Feature", "properties": attr_lookup[i], "geometry": mapping(row.geometry)}
        )

    output_geojson = {"type": "FeatureCollection", "features": features}

    _log(f"Exporting to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_geojson, f, ensure_ascii=False, separators=(",", ":"))

    in_mb = os.path.getsize(input_path) / 1e6
    out_mb = os.path.getsize(output_path) / 1e6
    _log("Process complete!")
    _log(f"  Features : {len(features)}")
    _log(
        f"  File size: {in_mb:.1f} MB -> {out_mb:.1f} MB ({(1 - out_mb/in_mb)*100:.0f}% reduction)"
    )


if __name__ == "__main__":
    process_flood_extents(
        input_path="/Users/Supath/Downloads/SDML/FIMeval/geojson_FIMextents/merged_output1.geojson",
        output_path="/Users/Supath/Downloads/SDML/FIMeval/fim_viz/FIM_extents.geojson",
        pre_tolerance=30,
        post_tolerance=5,
        smooth_iterations=5,
    )
