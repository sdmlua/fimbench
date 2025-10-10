from __future__ import annotations
import os, sys, json, re, argparse, datetime as dt
from typing import Any, Dict, List, Tuple, Optional

import boto3
from botocore.exceptions import ClientError

import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely.errors import GEOSException
from pyproj import Transformer
import codecs

# Config defaults
DEFAULT_BUCKET = "sdmlab"
DEFAULT_PREFIX = "FIM_Database/"
SIMPLIFY_M     = 20.0  # meters
MAX_STR_LEN    = 2000

# Regex / helpers for lenient JSON
_ymd_re = re.compile(r"(?<!\d)(\d{8})(?!\d)")
_TRAILING_COMMA_RE = re.compile(r',(\s*[}\]])')            # ", }" or ", ]"
_LINE_COMMENT_RE   = re.compile(r'(^|[,{]\s*)//.*$', re.MULTILINE)
_BLOCK_COMMENT_RE  = re.compile(r'/\*.*?\*/', re.DOTALL)
_HUC_LEADING0_RE   = re.compile(r'"(HUC\d{1,2})"\s*:\s*(0\d+)(\s*[,\}\]])')
_SMART_QUOTES = {u"\u201c": '"', u"\u201d": '"', u"\u2018": "'", u"\u2019": "'"}

def s3_http_url(bucket: str, key: str) -> str:
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def _unsmart(s: str) -> str:
    for k,v in _SMART_QUOTES.items():
        s = s.replace(k, v)
    return s

def lenient_json_load(raw: str) -> dict:
    txt = raw.lstrip(codecs.BOM_UTF8.decode("utf-8"))
    txt = _BLOCK_COMMENT_RE.sub("", txt)
    txt = _LINE_COMMENT_RE.sub(r"\1", txt)
    txt = _TRAILING_COMMA_RE.sub(r"\1", txt)
    txt = _unsmart(txt)
    txt = _HUC_LEADING0_RE.sub(r'"\1": "\2"\3', txt)
    txt = re.sub(r'(?<![A-Za-z0-9_])NaN(?![A-Za-z0-9_])', 'null', txt)
    txt = re.sub(r'(?<![A-Za-z0-9_])-?Infinity(?![A-Za-z0-9_])', 'null', txt)
    return json.loads(txt)

def load_with_context(raw: str, where: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            return lenient_json_load(raw)
        except json.JSONDecodeError as e:
            lines = raw.splitlines()
            i = max(0, e.lineno - 3); j = min(len(lines), e.lineno + 2)
            ctx = "\n".join(f"{k+1:>5}: {lines[k]}" for k in range(i, j))
            raise ValueError(f"Bad JSON at {where}: {e.msg} (line {e.lineno}, col {e.colno})\n{ctx}") from e

def extract_ymd_iso(text: Any) -> Optional[str]:
    if text is None: return None
    s = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    m = _ymd_re.search(s)
    if not m: return None
    try:
        return dt.datetime.strptime(m.group(1), "%Y%m%d").date().isoformat()
    except Exception:
        return None

def extract_return_period(text: Any) -> Optional[int]:
    if text is None: return None
    s = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    if _ymd_re.search(s):
        return None
    m = re.search(r"(?<!\d)(\d{2,4})(?!\d)", s)
    if not m: return None
    try:
        return int(m.group(1))
    except Exception:
        return None

def coerce_list(x) -> List[str]:
    if x is None: return []
    if isinstance(x, list):
        return [str(v)[:MAX_STR_LEN] for v in x]
    return [str(x)[:MAX_STR_LEN]]

def centroid_from_meta(meta: Dict[str, Any]) -> Tuple[float, float]:
    c = meta.get("Location of the centroid of the flood map")
    if isinstance(c, list) and len(c) >= 2:
        try:
            return float(c[0]), float(c[1])  # lon, lat
        except Exception:
            pass
    ex = meta.get("Extent") or {}
    try:
        xmin, ymin, xmax, ymax = ex.get("xmin"), ex.get("ymin"), ex.get("xmax"), ex.get("ymax")
        if all(v is not None for v in (xmin, ymin, xmax, ymax)):
            lon = (float(xmin) + float(xmax)) / 2.0
            lat = (float(ymin) + float(ymax)) / 2.0
            return lon, lat
    except Exception:
        pass
    return 0.0, 0.0

def safe_get(d: Dict[str, Any], *names: str, maxlen: int = MAX_STR_LEN):
    for n in names:
        if n in d and d[n] is not None:
            v = d[n]
            return v if not isinstance(v, str) else v[:maxlen]
    return None

def norm_tier(name: Optional[str]) -> str:
    if not name: return "Unknown_Tier"
    s = str(name).strip()
    m = re.match(r'(?i)\s*tier[_\s-]*(\d)\b', s)
    return f"Tier_{m.group(1)}" if m else s

def stable_id(tier: str, site: str, file_or_key: str) -> str:
    base = os.path.splitext(os.path.basename(file_or_key))[0]
    return f"{tier}/{site}/{base}"

def simplify_geojson_lonlat(geom_geojson: Dict, tol_m: float) -> Optional[Dict]:
    if geom_geojson is None:
        return None
    try:
        geom = shape(geom_geojson)
    except Exception:
        return None
    if geom.is_empty:
        return None
    try:
        to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
        to_4326 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform
        geom_3857 = transform(to_3857, geom)
        simp_3857 = geom_3857.simplify(tol_m, preserve_topology=True)
        simp_4326 = transform(to_4326, simp_3857)
        if simp_4326.is_empty:
            return None
        return mapping(simp_4326)
    except GEOSException:
        return None

def list_meta_keys(s3, bucket: str, prefix: str) -> List[str]:
    keys: List[str] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            k = obj["Key"]
            if k.lower().endswith("_metadata.json"):
                keys.append(k)
    return keys


# NORMALIZATION
def normalize_record(bucket: str, meta_key: str, meta: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict]]:
    parts = meta_key.split("/")
    tier = norm_tier(next((p for p in parts if p.lower().startswith("tier")), "Unknown_Tier"))
    site = parts[-2] if len(parts) >= 2 else "Unknown_Site"
    folder = "/".join(parts[:-1])

    file_name = safe_get(meta, "File_Name", "File Name", "File name")
    tif_url = s3_http_url(bucket, f"{folder}/{file_name}") if file_name else None
    json_url = s3_http_url(bucket, meta_key)

    date_field = safe_get(meta,
                          "Date of Flood /Synthetic Flooding Event (return period (years))",
                          "Date of Flood",
                          "Date")
    date_ymd = extract_ymd_iso(date_field) if tier != "Tier_4" else None
    event_ts = int(date_ymd.replace("-", "")) if date_ymd else None
    return_period = extract_return_period(date_field) if tier == "Tier_4" else None

    lon, lat = centroid_from_meta(meta)
    refs = coerce_list(meta.get("References"))

    huc: Dict[str, str] = {}
    for k in ("HUC2","HUC4","HUC6","HUC8","HUC10","HUC12"):
        if k in meta and meta[k] is not None:
            huc[k.lower()] = str(meta[k])

    rec_id = stable_id(tier, site, file_name or meta_key)

    core = {
        # stable identifiers
        "id": rec_id,
        "feature_id": rec_id,
        "site_id": site,
        "tier": tier,
        "site": site,   

        # dates
        "event_date": date_ymd,
        "event_ts": event_ts,       
        "date_raw": date_field,
        "return_period": return_period,

        # links / versioning
        "metadata_url": json_url,
        "s3_prefix": folder,
        "tif_url": tif_url,
        "geom_version": 1,

        # context (compact)
        "resolution_m": safe_get(meta, "Resolution in meter", "Resolution (m)", "resolution_m"),
        "state": safe_get(meta, "State"),
        "basin": safe_get(meta, "River Basin Name", "River Basin"),
        "source": safe_get(meta, "Source"),
        "access_rights": safe_get(meta, "Access_Rights"),
        "quality": safe_get(meta, "Quality") or tier,   
        **huc,  

        # centroid for quick fly-to
        "centroid": [lon, lat],

        # misc
        "file_name": file_name,
        "references": refs,
        "s3_key": meta_key,
    }

    geom = meta.get("FIM_Geometry")
    return core, geom

# MAIN
def main():
    ap = argparse.ArgumentParser(description="Build catalog_core.json + FIM_extents.geojson (lean, tile-ready)")
    ap.add_argument("--bucket", default=DEFAULT_BUCKET)
    ap.add_argument("--prefix", default=DEFAULT_PREFIX)
    ap.add_argument("--simplify-m", type=float, default=SIMPLIFY_M)
    ap.add_argument("--skip-geometry", action="store_true", help="Do not write FIM_extents.geojson")
    ap.add_argument("--profile", default=None, help="AWS profile (optional)")
    ap.add_argument("--out-core", default="catalog_core.json")
    ap.add_argument("--out-geojson", default="FIM_extents.geojson")
    args = ap.parse_args()

    session = boto3.session.Session(profile_name=args.profile) if args.profile else boto3.session.Session()
    s3 = session.client("s3")

    meta_keys = list_meta_keys(s3, args.bucket, args.prefix)
    print(f"[list] found {len(meta_keys)} metadata files under s3://{args.bucket}/{args.prefix}")

    core_rows: List[Dict[str, Any]] = []
    ext_rows: List[Dict[str, Any]] = []
    errors: List[Tuple[str, str]] = []
    seen_ids: Dict[str, int] = {}

    for i, key in enumerate(meta_keys, 1):
        if (i % 50 == 0) or (i == len(meta_keys)):
            print(f"[read] {i}/{len(meta_keys)}: {key}")
        try:
            raw = s3.get_object(Bucket=args.bucket, Key=key)["Body"].read().decode("utf-8", errors="replace")
            meta = load_with_context(raw, f"s3://{args.bucket}/{key}")

            core, geom = normalize_record(args.bucket, key, meta)

            rid = core["id"]
            if rid in seen_ids:
                seen_ids[rid] += 1
                core["id"] = f"{rid}__{seen_ids[rid]}"
                core["feature_id"] = core["id"]  
            else:
                seen_ids[rid] = 1

            core_rows.append(core)

            if not args.skip_geometry and geom:
                simp = simplify_geojson_lonlat(geom, args.simplify_m)
                if simp:
                    # compute bbox from simplified geom
                    try:
                        _g = shape(simp)
                        xmin, ymin, xmax, ymax = _g.bounds
                        bbox = [float(xmin), float(ymin), float(xmax), float(ymax)]
                    except Exception:
                        bbox = None

                    # tile-ready lean properties only
                    ext_rows.append({
                        "geometry": simp,
                        "properties": {
                            "feature_id": core["feature_id"],
                            "site_id": core["site_id"],
                            "tier": core["tier"],
                            "event_date": core["event_date"],
                            "event_ts": core["event_ts"],
                            "metadata_url": core["metadata_url"],
                            "s3_prefix": core["s3_prefix"],
                            "geom_version": core["geom_version"],
                            "resolution_m": core.get("resolution_m"),
                            "huc8": core.get("huc8"),
                            "state": core.get("state"),
                            "basin": core.get("basin"),
                            "source": core.get("source"),
                            "access_rights": core.get("access_rights"),
                            "centroid": core.get("centroid"),
                            "bbox": bbox,
                        }
                    })
        except Exception as e:
            errors.append((key, repr(e)))

    # write catalog_core.json
    catalog_core = {
        "schema_version": "1.1",
        "updated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "records": core_rows,
        "errors": errors,
    }
    with open(args.out_core, "w", encoding="utf-8") as f:
        json.dump(catalog_core, f, ensure_ascii=False, indent=2)
    print(f"[write] {args.out_core} ({len(core_rows)} records, {len(errors)} error(s))")

    # write FIM_extents.geojson
    if not args.skip_geometry and ext_rows:
        gdf = gpd.GeoDataFrame(
            pd.DataFrame([r["properties"] for r in ext_rows]),
            geometry=[shape(r["geometry"]) for r in ext_rows],
            crs="EPSG:4326",
        )
        # keep only clean geometries
        gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]

        # enforce a stable, lean schema/order 
        cols_order = [
            "feature_id","site_id","tier","event_date","event_ts",
            "metadata_url","s3_prefix","geom_version",
            "resolution_m","huc8","state","basin","source","access_rights",
            "centroid","bbox"
        ]
        cols_order = [c for c in cols_order if c in gdf.columns] + \
                     [c for c in gdf.columns if c not in cols_order and c != "geometry"]
        gdf = gdf[cols_order + ["geometry"]]

        gdf.to_file(args.out_geojson, driver="GeoJSON")
        print(f"[write] {args.out_geojson} ({len(gdf)} features)")
    elif args.skip_geometry:
        print("[info] --skip-geometry set; FIM_extents.geojson will not be written")
    else:
        print("[warn] no geometries found; FIM_extents.geojson will not be written")

if __name__ == "__main__":
    try:
        main()
    except ClientError as e:
        print(f"[aws error] {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)

# Run locally:
# python build_catalog.py --bucket sdmlab --prefix FIM_Database/
