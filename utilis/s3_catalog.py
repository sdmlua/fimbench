from __future__ import annotations
import json, re, datetime as dt
from typing import Dict, List, Any, Tuple
import boto3
from botocore import UNSIGNED
from botocore.config import Config
import streamlit as st

# CACHED RESOURCES
@st.cache_resource
def _s3_client():
    return boto3.client("s3", config=Config(signature_version=UNSIGNED))

# HELPERS
def _extract_ymd(s: Any) -> str | None:
    """
    Return an 8-digit YYYYMMDD found anywhere in s.
    Accepts str/bytes/int/float/list/dict; coerces to text safely.
    """
    if s is None:
        return None
    if isinstance(s, bytes):
        try:
            s = s.decode("utf-8", "replace")
        except Exception:
            s = str(s)
    elif not isinstance(s, str):
        try:
            s = json.dumps(s, ensure_ascii=False)
        except Exception:
            s = str(s)
    m = re.search(r"(?<!\d)(\d{8})(?!\d)", s)
    return m.group(1) if m else None

def _list_metadata_objects(bucket: str, root_prefix: str) -> List[str]:
    s3 = _s3_client()
    keys: List[str] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=root_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith("_metadata.json"):
                keys.append(key)
    return keys

# Lenient JSON fixer
_HUC_KEY_RE = re.compile(r'"(HUC\d{1,3})"\s*:\s*(0\d+)(\s*[,\}\]])')
_TRAILING_COMMA_RE = re.compile(r',(\s*[}\]])')
def _lenient_json_parse(raw: str) -> Dict[str, Any]:
    """
    Repair a couple of common JSON issues:
      1) HUC* with leading zero written as a bare number -> quote it.
      2) Trailing commas before } or ].
    If it still fails, raise JSONDecodeError.
    """
    text = raw
    text = _HUC_KEY_RE.sub(r'"\1": "\2"\3', text)
    text = _TRAILING_COMMA_RE.sub(r'\1', text)

    return json.loads(text)

def _fetch_json(bucket: str, key: str) -> Dict[str, Any]:
    """
    Fetch JSON from S3 and parse it.
    - Try strict JSON first.
    - If that fails, attempt a lenient repair (HUC* fix + trailing commas).
    - If still failing, raise ValueError with file context for display.
    """
    s3 = _s3_client()
    resp = s3.get_object(Bucket=bucket, Key=key)
    raw = resp["Body"].read().decode("utf-8", errors="replace")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            return _lenient_json_parse(raw)
        except json.JSONDecodeError as e2:
            lines = raw.splitlines()
            start = max(0, e2.lineno - 3)
            end   = min(len(lines), e2.lineno + 2)
            context = "\n".join(f"{i+1:>5}: {lines[i]}" for i in range(start, end))
            raise ValueError(
                f"Bad JSON at s3://{bucket}/{key} — {e2.msg} (line {e2.lineno}, col {e2.colno})\n"
                f"Context:\n{context}"
            ) from e2

# PUBLIC: build_catalog
@st.cache_data(show_spinner=False)
def build_catalog(bucket: str, root_prefix: str) -> Dict[str, Any]:
    """
    Cached: lists all *_metadata.json under root_prefix (across Tier_*/*),
    fetches and normalizes fields. Cache invalidates when (bucket, root_prefix) change
    or you manually clear it from the app.

    Returns:
        {
          "records": [ ...normalized dicts... ],
          "errors":  [ (key, message), ... ]   # any malformed JSON files that were skipped
        }
    """
    keys = _list_metadata_objects(bucket, root_prefix)
    records: List[Dict[str, Any]] = []
    errors: List[Tuple[str, str]] = []

    for key in keys:
        parts = key.split("/")
        tier = next((p for p in parts if p.lower().startswith("tier_")), None) or "Unknown_Tier"
        site = parts[-2] if len(parts) >= 2 else "Unknown_Site"

        try:
            meta = _fetch_json(bucket, key)
        except ValueError as ve:
            errors.append((key, str(ve)))
            continue 

        # Normalize fields
        file_name = meta.get("File_Name") or meta.get("File Name")
        res_m    = meta.get("Resolution in meter")
        dtype    = meta.get("Datatype") or meta.get("Data type")
        state    = meta.get("State")
        desc     = meta.get("Description")
        basin    = meta.get("River Basin Name") or meta.get("River Basin")
        source   = meta.get("Source")
        quality  = meta.get("Quality") or tier

        date_raw = meta.get("Date of Flood /Synthetic Flooding Event (return period (years))") or ""
        ymd_compact = _extract_ymd(date_raw) or _extract_ymd(file_name or "")
        date_iso = None
        if ymd_compact:
            try:
                date_iso = dt.datetime.strptime(ymd_compact, "%Y%m%d").date().isoformat()
            except Exception:
                date_iso = None

        lon = lat = None
        centroid = meta.get("Location of the centroid of the flood map") or []
        if isinstance(centroid, list) and len(centroid) >= 2:
            try:
                lon, lat = float(centroid[0]), float(centroid[1])
            except Exception:
                lon = lat = None
        if lon is None or lat is None:
            ex = meta.get("Extent") or {}
            xmin, ymin, xmax, ymax = ex.get("xmin"), ex.get("ymin"), ex.get("xmax"), ex.get("ymax")
            try:
                if all(v is not None for v in (xmin, ymin, xmax, ymax)):
                    lon = (float(xmin) + float(xmax)) / 2.0
                    lat = (float(ymin) + float(ymax)) / 2.0
            except Exception:
                lon = lat = None
        if lon is None or lat is None:
            lon, lat = 0.0, 0.0

        refs = meta.get("References") or []
        if isinstance(refs, str):
            refs = [refs]
        elif isinstance(refs, list):
            refs = [str(x) for x in refs]
        else:
            refs = [str(refs)]
        huc = {}
        for k in ("HUC2","HUC4","HUC6","HUC8","HUC10","HUC12"):
            if k in meta and meta[k] is not None:
                huc[k.lower()] = str(meta[k])

        records.append({
            "tier": tier,
            "site": site,
            "s3_key": key,
            "file_name": file_name,
            "resolution_m": res_m,
            "dtype": dtype,
            "state": state,
            "description": desc,
            "river_basin": basin,
            "source": source,
            "date_raw": date_raw,
            "date_ymd": date_iso,
            "quality": quality,
            "references": refs,
            "centroid_lon": lon,
            "centroid_lat": lat,
            "geometry": meta.get("FIM_Geometry"),
            "extent": meta.get("Extent"),
            **huc,
        })

    return {"records": records, "errors": errors}
