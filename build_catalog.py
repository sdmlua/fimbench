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
CORE_KEY       = "FIM_Database/catalog_core.json"
GPQ_KEY        = "FIM_Database/extents.parquet"
SIMPLIFY_M     = 100.0  # meters
MAX_STR_LEN    = 2000   # safeguard against accidental huge fields

# Regexes for lenient JSON parsing
_ymd_re = re.compile(r"(?<!\d)(\d{8})(?!\d)")
_TRAILING_COMMA_RE = re.compile(r',(\s*[}\]])')            # ", }" or ", ]"
_LINE_COMMENT_RE   = re.compile(r'(^|[,{]\s*)//.*$', re.MULTILINE)
_BLOCK_COMMENT_RE  = re.compile(r'/\*.*?\*/', re.DOTALL)
_HUC_LEADING0_RE   = re.compile(r'"(HUC\d{1,2})"\s*:\s*(0\d+)(\s*[,\}\]])')
_SMART_QUOTES = {u"\u201c": '"', u"\u201d": '"', u"\u2018": "'", u"\u2019": "'"}

#Utils
def s3_http_url(bucket: str, key: str) -> str:
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def _unsmart(s: str) -> str:
    for k,v in _SMART_QUOTES.items():
        s = s.replace(k, v)
    return s

def lenient_json_load(raw: str) -> dict:
    """Repair common JSON issues: BOM, comments, trailing commas, smart quotes, HUC leading zeros, NaN/Infinity."""
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
    if isinstance(x, list): return [str(v)[:MAX_STR_LEN] for v in x]
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

# Project lon/lat → WebMercator (m), simplify, back to lon/lat
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

def normalize_record(bucket: str, meta_key: str, meta: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict]]:
    parts = meta_key.split("/")
    tier = norm_tier(next((p for p in parts if p.lower().startswith("tier")), "Unknown_Tier"))
    site = parts[-2] if len(parts) >= 2 else "Unknown_Site"
    folder = "/".join(parts[:-1])

    file_name = safe_get(meta, "File_Name", "File Name", "File name")
    tif_url = s3_http_url(bucket, f"{folder}/{file_name}") if file_name else None
    json_url = s3_http_url(bucket, meta_key)

    date_field = safe_get(
        meta,
        "Date of Flood /Synthetic Flooding Event (return period (years))",
        "Date of Flood",
        "Date",
    )
    date_ymd = extract_ymd_iso(date_field) if tier != "Tier_4" else None
    return_period = extract_return_period(date_field) if tier == "Tier_4" else None

    lon, lat = centroid_from_meta(meta)
    refs = coerce_list(meta.get("References"))

    huc: Dict[str, str] = {}
    for k in ("HUC2","HUC4","HUC6","HUC8","HUC10","HUC12"):
        if k in meta and meta[k] is not None:
            huc[k.lower()] = str(meta[k])

    rec_id = stable_id(tier, site, file_name or meta_key)

    core = {
        "id": rec_id,
        "tier": tier,
        "site": site,
        "centroid_lon": lon,
        "centroid_lat": lat,
        "date_ymd": date_ymd,
        "date_raw": date_field,
        "return_period": return_period,          
        "file_name": file_name,
        "resolution_m": safe_get(meta, "Resolution in meter", "Resolution (m)", "resolution_m"),
        "state": safe_get(meta, "State"),
        "description": safe_get(meta, "Description"),
        "river_basin": safe_get(meta, "River Basin Name", "River Basin"),
        "source": safe_get(meta, "Source"),
        "quality": safe_get(meta, "Quality") or tier,
        "references": refs,
        "tif_url": tif_url,
        "json_url": json_url,
        **huc,
        "s3_key": meta_key,
    }

    geom = meta.get("FIM_Geometry")
    return core, geom

# MAIN 
def main():
    ap = argparse.ArgumentParser(description="Build catalog_core.json + extents.parquet (robust)")
    ap.add_argument("--bucket", default=DEFAULT_BUCKET)
    ap.add_argument("--prefix", default=DEFAULT_PREFIX)
    ap.add_argument("--core-key", default=CORE_KEY)
    ap.add_argument("--gpq-key", default=GPQ_KEY)
    ap.add_argument("--simplify-m", type=float, default=SIMPLIFY_M)
    ap.add_argument("--skip-geometry", action="store_true", help="Do not write extents.parquet")
    ap.add_argument("--profile", default=None, help="AWS profile (optional)")
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--out-core", default="catalog_core.json")
    ap.add_argument("--out-gpq", default="extents.parquet")
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

            # Ensure unique id
            rid = core["id"]
            if rid in seen_ids:
                seen_ids[rid] += 1
                core["id"] = f"{rid}__{seen_ids[rid]}"
            else:
                seen_ids[rid] = 1

            core_rows.append(core)

            if not args.skip_geometry and geom:
                simp = simplify_geojson_lonlat(geom, args.simplify_m)
                if simp:
                    ext_rows.append({"id": core["id"], "tier": core["tier"], "site": core["site"], "geometry": simp})
        except Exception as e:
            errors.append((key, repr(e)))

    # CORE JSON
    catalog_core = {
        "schema_version": "1.1",
        "updated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "records": core_rows,
        "errors": errors,
    }
    with open(args.out_core, "w", encoding="utf-8") as f:
        json.dump(catalog_core, f, ensure_ascii=False, indent=2)
    print(f"[write] {args.out_core} ({len(core_rows)} records, {len(errors)} error(s))")

    # GeoParquet
    if not args.skip_geometry and ext_rows:
        gdf = gpd.GeoDataFrame(
            pd.DataFrame([{"id": r["id"], "tier": r["tier"], "site": r["site"]} for r in ext_rows]),
            geometry=[shape(r["geometry"]) for r in ext_rows],
            crs="EPSG:4326",
        )
        
        gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()]
        gdf.to_parquet(args.out_gpq, index=False)
        print(f"[write] {args.out_gpq} ({len(gdf)} features)")
    elif args.skip_geometry:
        print("[info] --skip-geometry set; no GeoParquet will be written")
    else:
        print("[warn] no geometries found; extents.parquet will not be written")

    if not args.no_upload:
        # Upload core
        core_bytes = json.dumps(catalog_core, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        s3.put_object(
            Bucket=args.bucket, Key=args.core_key, Body=core_bytes,
            ContentType="application/json",
            CacheControl="public, max-age=86400, stale-while-revalidate=86400",
        )
        print(f"[upload] s3://{args.bucket}/{args.core_key} ({len(core_bytes)} bytes)")

        # Upload GeoParquet
        if (not args.skip_geometry) and os.path.exists(args.out_gpq):
            with open(args.out_gpq, "rb") as f:
                s3.put_object(
                    Bucket=args.bucket, Key=args.gpq_key, Body=f.read(),
                    ContentType="application/octet-stream",
                    CacheControl="public, max-age=86400, stale-while-revalidate=86400",
                )
            print(f"[upload] s3://{args.bucket}/{args.gpq_key}")

        print("[done] Upload finished")

if __name__ == "__main__":
    try:
        main()
    except ClientError as e:
        print(f"[aws error] {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)
        
#Run Locally
#python build_catalog.py --bucket sdmlab --prefix FIM_Database/
