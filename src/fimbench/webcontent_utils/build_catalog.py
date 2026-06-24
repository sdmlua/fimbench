"""
Author: Supath Dhital
Date Created: January 2026

FIMCatalogBuilder: A professional class-based utility to crawl S3,
normalize metadata, and build catalog_core.json.

Requirements:
  - Python: pandas, boto3
"""

from __future__ import annotations
import os
import sys
import json
import re
import codecs
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import boto3
from botocore.exceptions import ClientError
import pandas as pd


class FIMCatalogBuilder:
    def __init__(
        self,
        bucket: str = "sdmlab",
        prefix: str = "FIM_Database/",
        profile: Optional[str] = None,
        max_str_len: int = 2000,
        out_dir: Optional[str | Path] = None
    ):
        self.bucket = bucket
        self.prefix = prefix
        self.max_str_len = max_str_len

        self.out_dir = Path(out_dir) if out_dir else None
        if self.out_dir:
            self.out_dir.mkdir(parents=True, exist_ok=True)

        self.session = boto3.session.Session(profile_name=profile) if profile else boto3.session.Session()
        self.s3 = self.session.client("s3")

        self._KNOWN_RP_VALUES = {2, 5, 10, 25, 50, 100, 200, 500, 1000}
        self._ymd_re = re.compile(r"(?<!\d)(\d{8})(?!\d)")
        self._TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
        self._LINE_COMMENT_RE = re.compile(r"(^|[,{]\s*)//.*$", re.MULTILINE)
        self._BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
        self._HUC_LEADING0_RE = re.compile(r'"(HUC\d{1,2})"\s*:\s*(0\d+)(\s*[,\}\]])')
        self._SMART_QUOTES = {"\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'"}
        self._GPKG_SUFFIX_RE = re.compile(r"_(BM|FIM|MASK)$", re.IGNORECASE)

        self.core_rows = []
        self.errors = []
        self.seen_ids = {}

    # Formatting the JSON helpers
    def _unsmart(self, s: str) -> str:
        for k, v in self._SMART_QUOTES.items():
            s = s.replace(k, v)
        return s

    def _lenient_json_load(self, raw: str) -> dict:
        txt = raw.lstrip(codecs.BOM_UTF8.decode("utf-8"))
        txt = self._BLOCK_COMMENT_RE.sub("", txt)
        txt = self._LINE_COMMENT_RE.sub(r"\1", txt)
        txt = self._TRAILING_COMMA_RE.sub(r"\1", txt)
        txt = self._unsmart(txt)
        txt = self._HUC_LEADING0_RE.sub(r'"\1": "\2"\3', txt)
        txt = re.sub(r"(?<![A-Za-z0-9_])NaN(?![A-Za-z0-9_])", "null", txt)
        txt = re.sub(r"(?<![A-Za-z0-9_])-?Infinity(?![A-Za-z0-9_])", "null", txt)
        return json.loads(txt)

    def coerce_list(self, x) -> List[str]:
        """
        Coerce reference-like values into a list[str].
        - Accepts string, list[str], list[dict], dict, etc.
        - Preserves key/value refs by json-dumping dicts (still list[str]).
        """
        if x is None:
            return []
        items = x if isinstance(x, list) else [x]
        out: List[str] = []
        for v in items:
            if isinstance(v, dict):
                out.append(json.dumps(v, ensure_ascii=False)[:self.max_str_len])
            else:
                out.append(str(v)[:self.max_str_len])
        return out

    def _load_with_context(self, raw: str, where: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            try:
                return self._lenient_json_load(raw)
            except json.JSONDecodeError as e:
                lines = raw.splitlines()
                i, j = max(0, e.lineno - 3), min(len(lines), e.lineno + 2)
                ctx = "\n".join(f"{k+1:>5}: {lines[k]}" for k in range(i, j))
                raise ValueError(f"Bad JSON at {where}: {e.msg} (line {e.lineno})\n{ctx}")

    # Extraction Helpers
    def _safe_get(self, d: Dict[str, Any], *names: str):
        for n in names:
            if n in d and d[n] is not None:
                v = d[n]
                return v if not isinstance(v, str) else v[:self.max_str_len]
        return None

    def _extract_ymd_iso(self, text: Any) -> Optional[str]:
        if text is None:
            return None
        s = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
        m = self._ymd_re.search(s)
        if not m:
            return None
        try:
            return dt.datetime.strptime(m.group(1), "%Y%m%d").date().isoformat()
        except:
            return None
        
    def _extract_event_ts(self, text: Any) -> Optional[str]:
        if text is None:
            return None
        s = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
        m = re.search(r"(?<!\d)(\d{8}T\d+)(?!\d)", s)
        if m:
            return m.group(1)

        # Fallback
        m = self._ymd_re.search(s)
        if m:
            return m.group(1)

        return None

    def _extract_return_period(self, text: Any) -> Optional[int]:
        if text is None:
            return None
        if isinstance(text, (int, float)):
            return int(text)
        s = str(text)
        if self._ymd_re.search(s):
            return None
        m = re.search(r"(?<!\d)(\d{2,4})(?!\d)", s)
        if not m:
            return None
        try:
            return int(m.group(1))
        except:
            return None

    def _centroid_from_meta(self, meta: Dict[str, Any]) -> Tuple[float, float]:
        c = meta.get("Location of the centroid of the flood map")
        if isinstance(c, list) and len(c) >= 2:
            try:
                return float(c[0]), float(c[1])
            except:
                pass
        ex = meta.get("Extent") or {}
        try:
            lon = (float(ex.get("xmin")) + float(ex.get("xmax"))) / 2.0
            lat = (float(ex.get("ymin")) + float(ex.get("ymax"))) / 2.0
            return lon, lat
        except:
            return 0.0, 0.0

    def _bbox_from_extent(self, meta: Dict[str, Any]) -> Optional[List[float]]:
        ex = meta.get("Extent") or {}
        try:
            return [
                float(ex["xmin"]),
                float(ex["ymin"]),
                float(ex["xmax"]),
                float(ex["ymax"]),
            ]
        except:
            return None

    # Normalization 
    def normalize_record(self, meta_key: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        parts = meta_key.split("/")

        tier_str = next(
            (p for p in parts if p.lower().startswith("tier") or p.lower() == "hwm"),
            "Unknown_Tier"
        )
        if tier_str.lower() == "hwm":
            tier = "HWM"
        else:
            m_tier = re.match(r"(?i)\s*tier[_\s-]*(\d)\b", tier_str.strip())
            tier = f"Tier_{m_tier.group(1)}" if m_tier else tier_str

        site = parts[-2] if len(parts) >= 2 else "Unknown_Site"
        folder = "/".join(parts[:-1])

        file_name = self._safe_get(meta, "File_Name", "File Name", "File name")
        tif_url = f"https://{self.bucket}.s3.amazonaws.com/{folder}/{file_name}" if file_name else None

        base_no_ext, _ = os.path.splitext(file_name or "")
        base_aoi = (
            self._GPKG_SUFFIX_RE.sub("_AOI", base_no_ext)
            if self._GPKG_SUFFIX_RE.search(base_no_ext)
            else f"{base_no_ext}_AOI"
        )
        gpkg_url = f"https://{self.bucket}.s3.amazonaws.com/{folder}/{base_aoi}.gpkg" if file_name else None

        # Dates different for different tiers
        start_date_ymd = None
        end_date_ymd = None
        date_ymd = None
        event_ts = None
        return_period = None

        if tier == "HWM":
            start_date_ymd = self._extract_ymd_iso(
                self._safe_get(meta, "Start Date of the Flood")
            )
            end_date_ymd = self._extract_ymd_iso(
                self._safe_get(meta, "End Date of the Flood")
            )
            # event_ts anchored to start date for sorting
            if start_date_ymd:
                event_ts = int(start_date_ymd.replace("-", ""))

        elif tier == "Tier_4":
            rp_field = self._safe_get(
                meta,
                "Synthetic Flooding Event (return period (years))",
                "Return Period",
                "RP",
            )
            return_period = self._extract_return_period(rp_field)
            if return_period is None and file_name:
                for tok in re.split(r"[_\-]", os.path.splitext(file_name)[0]):
                    if tok.isdigit() and int(tok) in self._KNOWN_RP_VALUES:
                        return_period = int(tok)
                        break

        else:  # Tier 1, 2, 3
            flooding_event = self._safe_get(meta, "Flooding Event")
            date_ymd = self._extract_ymd_iso(flooding_event)
            event_ts = self._extract_event_ts(flooding_event)

        lon, lat = self._centroid_from_meta(meta)

        core = {
                "id": f"{tier}/{site}/{os.path.splitext(os.path.basename(file_name or meta_key))[0]}",
                "site_id": site,
                "tier": tier,
                "date_ymd": date_ymd,                    # Tier 1/2/3 flood date
                "start_date_ymd": start_date_ymd,        # HWM only
                "end_date_ymd": end_date_ymd,            # HWM only
                "return_period": return_period,           # Tier 4 only
                **({"event_ts": event_ts} if tier in {"Tier_1", "Tier_2", "Tier_3"} else {}),
                "json_url": f"https://{self.bucket}.s3.amazonaws.com/{meta_key}",
                "s3_prefix": folder,
                "tif_url": tif_url,
                "gpkg_url": gpkg_url,
                "centroid": [lon, lat],
                "bbox": self._bbox_from_extent(meta),
                "resolution_m": self._safe_get(meta, "Resolution in meter", "Resolution (m)"),
                "state": self._safe_get(meta, "State"),
                "basin": self._safe_get(meta, "River Basin Name"),
                "source": self._safe_get(meta, "Source"),
                "access_rights": self._safe_get(meta, "Access_Rights"),
                "file_name": file_name,
                "s3_key": meta_key,
                "quality": self._safe_get(meta, "Quality") or tier,
                "description": self._safe_get(meta, "Description"),
                "references": meta.get("References"),
            }

        for k in ("HUC2", "HUC4", "HUC6", "HUC8", "HUC10", "HUC12"):
            if k in meta:
                core[k.lower()] = (
                    [str(v) for v in meta[k]]
                    if isinstance(meta[k], list)
                    else str(meta[k])
                )

        return core

    # Building the catalog_core.json
    def build_catalog(self, out_core: str = "catalog_core.json"):
        core_path = self.out_dir / out_core if self.out_dir else Path(out_core)

        paginator = self.s3.get_paginator("list_objects_v2")
        meta_keys = [
            obj["Key"]
            for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix)
            for obj in page.get("Contents", [])
            if obj["Key"].lower().endswith("_metadata.json")
        ]

        total_files = len(meta_keys)
        print(f"\n[INFO] Found {total_files} keys. Processing...", flush=True)

        for i, key in enumerate(meta_keys, 1):
            file_name_only = os.path.basename(key)
            print(f"[{i}/{total_files}] Working on: {file_name_only}                    ", end="\r", flush=True)

            try:
                raw = (
                    self.s3.get_object(Bucket=self.bucket, Key=key)["Body"]
                    .read()
                    .decode("utf-8", errors="replace")
                )
                meta = self._load_with_context(raw, f"s3://{self.bucket}/{key}")
                core = self.normalize_record(key, meta)

                rid = core["id"]
                self.seen_ids[rid] = self.seen_ids.get(rid, 0) + 1
                if self.seen_ids[rid] > 1:
                    core["id"] = f"{rid}__{self.seen_ids[rid]}"

                self.core_rows.append(core)

            except Exception as e:
                print(f"\n[ERROR] Failed at {key}: {e}", flush=True)
                self.errors.append((key, repr(e)))

        print(f"\n[INFO] Processing complete for {len(self.core_rows)} records.", flush=True)

        with open(core_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "updated_at": dt.datetime.utcnow().isoformat() + "Z",
                    "records": self.core_rows,
                    "errors": self.errors,
                },
                f,
                indent=2,
            )
        print(f"[INFO] Catalog core written to {core_path}", flush=True)