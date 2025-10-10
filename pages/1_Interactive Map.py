from __future__ import annotations
import hashlib
import datetime as dt
from io import BytesIO
from typing import Dict, Any, Iterable, List, Tuple, Optional

import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import mapping

import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.features import GeoJson
from folium.plugins import MarkerCluster
from branca.element import Element, MacroElement
from jinja2 import Template
import json

from utilis.ui import inject_globalfont
inject_globalfont(font_size_px=18, sidebar_font_size_px=20)

# CONFIG
BUCKET    = "sdmlab"
CORE_KEY  = "FIM_Database/FIM_Viz/catalog_core.json"
TILES_KEY = "FIM_Database/FIM_Viz/tiles"

# Max features to draw at once
BASE_FEATURE_CAP = 10

TIER_COLORS = {
    "Tier_1": "#1b9e77",
    "Tier_2": "#d95f02",
    "Tier_3": "#7570b3",
    "Tier_4": "#e7298a",
    "Tier_5": "#66a61e",
}
DEFAULT_TIER_COLOR = "#2c7fb8"

BASEMAPS = {
    "OpenStreetMap": dict(tiles="OpenStreetMap", attr="© OpenStreetMap"),
    "CartoDB Positron": dict(tiles="CartoDB positron", attr="© OpenStreetMap contributors, © CARTO"),
    "Esri WorldTopoMap": dict(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri — Sources: Esri, HERE, Garmin, FAO, NOAA, and others"
    ),
    "Esri WorldImagery": dict(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri, Maxar, Earthstar Geographics, GIS User Community"
    ),
}

# HELPERS
def http_url(key: str) -> str:
    from urllib.parse import quote
    return f"https://{BUCKET}.s3.amazonaws.com/{quote(key, safe='/')}"

@st.cache_data(show_spinner=False, ttl=86400)
def fetch_json(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False)
def fingerprint_ids(ids: Iterable[str]) -> str:
    arr = sorted([str(x) for x in ids])
    return hashlib.sha1(("\n".join(arr)).encode("utf-8")).hexdigest()

# Custom vector grid layer for folium
class VectorGridProtobuf(MacroElement):
    _template = Template("""
        {% macro script(this, kwargs) %}
        (function ensureVectorGrid(cb){
          if (window.L && L.vectorGrid) { cb(); return; }
          var s = document.createElement('script');
          s.src = "https://unpkg.com/leaflet.vectorgrid/dist/Leaflet.VectorGrid.bundled.js";
          s.onload = cb; document.head.appendChild(s);
        })(function(){
          var map       = {{ this._parent.get_name() }};
          var urlTpl    = {{ this.tiles_url|tojson }};
          var lyrId     = {{ this.layer_name|tojson }};
          var colorMap  = {{ this.tier_colors|safe }};
          var defaultC  = {{ this.default_color|tojson }};
          var maxNative = {{ this.max_native }};

          // filters coming from Python
          var TIER_SET  = new Set({{ this.allowed_tiers|safe }});
          var DATE_MIN  = {{ this.date_min }};
          var DATE_MAX  = {{ this.date_max }};

          function matches(props){
            // 1) Tier
            if (TIER_SET.size > 0) {
              if (!TIER_SET.has(String(props.tier || ""))) return false;
            }
            // 2) Date range (YYYYMMDD int) — missing dates are allowed
            var ets = Number(props.event_ts);
            if (Number.isFinite(ets)) {
              if (ets < DATE_MIN || ets > DATE_MAX) return false;
            }
            return true;
          }

          var style = {};
          style[lyrId] = function(props){
            if (!matches(props)) {
                return { stroke:false, fill:false, opacity:0, fillOpacity:0, weight:0 };
            }
            var c = (props && props.tier && colorMap[props.tier]) ? colorMap[props.tier] : defaultC;
            return {
                stroke:true,       // no borders
                weight:0.5,
                color:c,
                opacity:1,          // border invisible
                fill:true,
                fillColor:c,
                fillOpacity:0.5,   // fill visible
                lineCap:'round',
                lineJoin:'round',
                smoothFactor:10.0    // smooth geometry edges
            };

          };

          var grid = L.vectorGrid.protobuf(urlTpl, {
            vectorTileLayerStyles: style,
            interactive: true,
            maxNativeZoom: maxNative,
            maxZoom: 22,
            rendererFactory: L.svg.tile
          })
          .on('click', function(e){
            var p = (e.layer && e.layer.properties) || {};
            var html = "<div style='font:13px system-ui'><b>"+(p.tier||"")+
                       "</b> — "+(p.site_id||"")+
                       "<br/>ID: "+(p.feature_id||"")+
                       (p.event_date ? "<br/>Date: "+p.event_date : "") +
                       "</div>";
            L.popup().setLatLng(e.latlng).setContent(html).openOn(map);
          })
          .addTo(map);

          window.__fimGrid = grid;
        });
        {% endmacro %}
    """)
    def __init__(
        self,
        tiles_url: str,
        layer_name: str = "fim_extents",
        tier_colors: Optional[Dict[str,str]] = None,
        max_native: int = 14,
        allowed_tiers: Optional[List[str]] = None,
        date_min: int = 0,
        date_max: int = 99999999
    ):
        super().__init__()
        if tier_colors is None:
            tier_colors = TIER_COLORS
        self.tiles_url      = tiles_url
        self.layer_name     = layer_name
        self.tier_colors    = json.dumps(tier_colors)
        self.default_color  = DEFAULT_TIER_COLOR
        self.max_native     = max_native
        self.allowed_tiers  = json.dumps([str(x) for x in (allowed_tiers or [])])
        self.date_min       = int(date_min)
        self.date_max       = int(date_max)
        
# Streamlit page boot
st.set_page_config(page_title="Interactive FIM Vizualizer", page_icon="🌊", layout="wide")
st.title("Benchmark FIMs")

# Session defaults
ss = st.session_state
if "saved_center" not in ss:
    ss.saved_center = [39.8283, -98.5795]
if "saved_zoom" not in ss:
    ss.saved_zoom = 5.0
if "fim_show" not in ss:
    ss.fim_show = False
if "filters_changed" not in ss:
    ss.filters_changed = True 
if "map_built_once" not in ss:
    ss.map_built_once = False

# Sidebar cache control
with st.sidebar:
    st.header("Data")
    if st.button("Reload Data", use_container_width=True):
        fetch_json.clear()
        for k in ("catalog_records", "core_errors"):
            ss.pop(k, None)
        ss.filters_changed = True
        st.success("Cache cleared. Data will reload now.")

# Load catalog
if "catalog_records" not in ss:
    core = fetch_json(http_url(CORE_KEY))
    ss.catalog_records = core.get("records", [])
    ss.core_errors     = core.get("errors", [])

records: List[Dict[str, Any]] = ss.catalog_records
load_errors = ss.get("core_errors", [])

if load_errors:
    with st.expander(f"{len(load_errors)} metadata issue(s) — click for details", expanded=False):
        for key, msg in load_errors[:50]:
            st.markdown(f"- **{key}**")
            st.code(msg, language="text")
        if len(load_errors) > 50:
            st.caption(f"...and {len(load_errors)-50} more")

if not records:
    st.warning("No records found in catalog_core.json.")
    st.stop()

# Filters
all_tiers = sorted({r.get("tier", "Unknown_Tier") for r in records})
dates_all = sorted([r["date_ymd"] for r in records if (r.get("tier") != "Tier_4") and r.get("date_ymd")])
min_date = dt.date.fromisoformat(dates_all[0]) if dates_all else dt.date(2000, 1, 1)
max_date = dt.date.fromisoformat(dates_all[-1]) if dates_all else dt.date.today()
rp_all   = sorted({r.get("return_period") for r in records if r.get("tier") == "Tier_4" and r.get("return_period") is not None})

with st.sidebar:
    st.header("Filters")
    with st.form("filters_form", clear_on_submit=False):
        sel_tiers = st.multiselect("Select FIM Tiers from Database", options=all_tiers, default=all_tiers)

        show_date_filter = any(t != "Tier_4" for t in sel_tiers)
        if show_date_filter:
            dr = st.date_input(
                "Date range (non-synthetic)",
                value=(min_date, max_date), min_value=min_date, max_value=max_date, format="YYYY-MM-DD"
            )
        else:
            dr = None

        show_rp_filter = ("Tier_4" in sel_tiers) and bool(rp_all)
        if show_rp_filter:
            sel_rps = st.multiselect("Return periods (For synthetic benchark Tier_4, years)", options=rp_all, default=rp_all)
        else:
            sel_rps = None

        show_polys = st.checkbox("Show Flood Inundation Mapping Extent", value=ss.get("fim_show", False))

        apply_filters = st.form_submit_button("Apply Filters", use_container_width=True)

    st.header("Basemap")
    basemap_choice = st.selectbox("Select basemap", list(BASEMAPS.keys()), index=2)

# persist flood extent toggle
ss.fim_show = show_polys

# Date range unpack
if isinstance(dr, tuple) and len(dr) == 2:
    start_date, end_date = dr
else:
    start_date, end_date = min_date, max_date

def in_date_range(r) -> bool:
    iso = r.get("date_ymd")
    if not iso:
        return False
    try:
        d = dt.date.fromisoformat(iso)
    except Exception:
        return False
    return (start_date <= d <= end_date)

def pass_filters(r) -> bool:
    rtier = r.get("tier")
    if rtier not in sel_tiers:
        return False
    if rtier == "Tier_4":
        if sel_rps is None:
            return True
        rp = r.get("return_period")
        return (rp in sel_rps) if (rp is not None) else False
    else:
        if dr is None:
            return True
        return in_date_range(r)

if apply_filters:
    ss.filters_changed = True

filtered = [r for r in records if pass_filters(r)]
filtered_ids = [str(r["id"]) for r in filtered]
ids_key = fingerprint_ids(filtered_ids)

# Map helpers
def feature_cap_by_zoom(zoom: float) -> int:
    if zoom >= 10:
        return 200
    if zoom >= 8:
        return 120
    if zoom >= 6:
        return 60
    if zoom >= 5:
        return 30
    return BASE_FEATURE_CAP

@st.fragment
def render_map():
    # Base map
    m = folium.Map(
        location=ss.saved_center,
        zoom_start=ss.saved_zoom,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )
    bm = BASEMAPS[basemap_choice]
    folium.TileLayer(tiles=bm["tiles"], name=basemap_choice, control=False, attr=bm["attr"], show=True).add_to(m)

    current_cap = feature_cap_by_zoom(float(ss.saved_zoom))

    # Markers
    def popup_html(r: dict) -> str:
        tif_url = r.get("tif_url"); json_url = r.get("json_url")
        fields = [
            ("File Name", r.get("file_name")),
            ("Resolution (m)", r.get("resolution_m")),
            ("State", r.get("state")),
            ("Description", r.get("description")),
            ("River Basin Name", r.get("river_basin")),
            ("Source", r.get("source")),
            ("Date", r.get("date_ymd") or r.get("date_raw")),
            ("Return Period (years)", r.get("return_period") if r.get("tier") == "Tier_4" else None),
            ("Quality", r.get("quality")),
        ]
        rows = "".join(
            f"<tr><th style='text-align:left;vertical-align:top;padding-right:8px'>{k}</th>"
            f"<td style='text-align:left'>{'' if v is None else v}</td></tr>"
            for k, v in fields
        )
        refs = r.get("references") or []
        refs_html = ""
        if refs:
            refs_html = "<div style='margin-top:6px'><b>References</b><div style='margin:4px 0;padding-left:12px'>"
            for ref in refs:
                refs_html += f"<div style='margin-bottom:6px'>{ref}</div>"
            refs_html += "</div></div>"

        buttons_html = ""
        if tif_url:
            buttons_html += f"""
            <a href="{tif_url}" target="_blank" rel="noopener"
               style="text-decoration:none;display:inline-block;background:#2563eb;color:#fff;
                      padding:8px 10px;border-radius:6px;font-weight:600;margin-right:8px;">
              ⬇ Download Benchmark FIM (.tif)
            </a>"""
        if json_url:
            buttons_html += f"""
            <a href="{json_url}" target="_blank" rel="noopener"
               style="text-decoration:none;display:inline-block;background:#059669;color:#fff;
                      padding:8px 10px;border-radius:6px;font-weight:600;">
              ⬇ Download Metadata (.json)
            </a>"""

        return f"""
        <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif; font-size:13px; max-width:420px">
            <table>{rows}</table>
            {'<hr style="margin:6px 0" />' if refs_html or buttons_html else ''}
            {refs_html}
            {buttons_html}
        </div>
        """

    markers_fg = MarkerCluster(
        name="Benchmark FIM Sites",
        show=True,
        disableClusteringAtZoom=10
    )
    count = 0
    for r in filtered:
        if count >= current_cap:
            break
        lat = float(r.get("centroid_lat", 0))
        lon = float(r.get("centroid_lon", 0))
        color = TIER_COLORS.get(r.get("tier"), DEFAULT_TIER_COLOR)
        folium.CircleMarker(
            location=[lat, lon],
            radius=8, color="black", weight=1.5, fill=True, fill_color=color, fill_opacity=0.9,
            tooltip=f"{r.get('tier')} — {r.get('site')}",
            popup=folium.Popup(popup_html(r), max_width=500),
        ).add_to(markers_fg)
        count += 1
    markers_fg.add_to(m)

    # Vector tiles hosting from s3
    if ss.fim_show:
        allowed_tiers = list(set(sel_tiers))
        date_min = int((start_date or dt.date(1900,1,1)).strftime("%Y%m%d"))
        date_max = int((end_date   or dt.date(2100,1,1)).strftime("%Y%m%d"))

        # Put the vector grid into a FeatureGroup so it appears in LayerControl
        vg_group = folium.FeatureGroup(name="Benchmark FIM Extents", show=True)
        vg = VectorGridProtobuf(
            tiles_url= "https://sdmlab.s3.amazonaws.com/FIM_Database/FIM_Viz/tiles/{z}/{x}/{y}.pbf",
            layer_name="fim_extents",
            max_native=14,
            allowed_tiers=allowed_tiers,
            date_min=date_min,
            date_max=date_max
        )
        vg_group.add_child(vg)
        vg_group.add_to(m)

    # Legend
    legend_items = "".join(
        f"<div style='display:flex;align-items:center;margin-bottom:6px'>"
        f"<span style='display:inline-block;width:16px;height:16px;background:{TIER_COLORS.get(t, DEFAULT_TIER_COLOR)};"
        f"border:1px solid #000;margin-right:8px'></span>"
        f"<span style='font-size:14px'>{t}</span></div>"
        for t in sorted(set(r.get("tier") for r in filtered))
    )

    legend_html = f"""
    <div style="position:fixed; z-index:9999; bottom:20px; right:20px; background:rgba(255,255,255,0.95);
                padding:12px 14px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.3);">
      <div style="font-weight:600; font-size:14px; margin-bottom:8px">FIM Tiers</div>
      {legend_items if legend_items else '<div style="font-size:13px;color:#666">No FIMs with this filter in any Tier</div>'}
    </div>
    """
    m.get_root().html.add_child(Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)

    # Render in Streamlit
    st_folium(
        m,
        width=None,
        height=720,
        key="fim_map",
        returned_objects=[]
    )

    if ss.filters_changed or not ss.map_built_once:
        ss.map_built_once = True
        ss.filters_changed = False
        
render_map()

#Render the table
PLATFORM_BY_TIER = {
    "Tier_1": "Hand Labeled Aerial Imagery",
    "Tier_2": "Planet Satellite Imagery",
    "Tier_3": "Sentinel-1 Imagery",
    "Tier_4": "Synthetic HEC-RAS 1D",
}

def dash(x):
    """Return a dash for empty values, else the value itself."""
    if x is None:
        return "–"
    if isinstance(x, str) and x.strip() == "":
        return "–"
    return x

def to_date_key(r: dict) -> int:
    ets = r.get("event_ts")
    if isinstance(ets, (int, float)) and int(ets) > 0:
        return int(ets)
    for k in ("event_date", "date_ymd"):
        v = r.get(k)
        if isinstance(v, str) and v:
            try:
                d = dt.date.fromisoformat(v)
                return int(d.strftime("%Y%m%d"))
            except Exception:
                pass
    v = r.get("date_raw")
    if isinstance(v, (int, float)) and int(v) > 0:
        return int(v)
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return 0

def nice_date_and_year(r: dict) -> tuple[str, str]:
    for k in ("event_date", "date_ymd"):
        v = r.get(k)
        if isinstance(v, str) and v:
            try:
                y = str(dt.date.fromisoformat(v).year)
            except Exception:
                y = v[:4] if len(v) >= 4 else ""
            return v, y
    raw = r.get("date_raw") or ""
    if isinstance(raw, (int, float)):
        raw = str(int(raw))
    year = raw[:4] if isinstance(raw, str) and len(raw) >= 4 else ""
    if isinstance(raw, str) and len(raw) == 8 and raw.isdigit():
        disp = f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    else:
        disp = raw if raw else ""
    return disp, year

def row_from_record(r: dict) -> dict:
    date_disp, year = nice_date_and_year(r)
    basin = r.get("basin")
    if not basin:
        basin = r.get("river_basin")
    platform = PLATFORM_BY_TIER.get(r.get("tier"), "–")
    return {
        "River/Basin": dash(basin),
        "State": dash(r.get("state")),
        "Year": dash(year),
        "Date": dash(date_disp),
        "Resolution (m)": r.get("resolution_m") if isinstance(r.get("resolution_m"), (int, float)) else "–",
        "HUC8": dash(r.get("huc8")),
        "Quality": dash(r.get("quality") or r.get("tier")),
        "Platform": platform,
        "Download FIM (TIF)": dash(r.get("tif_url")),
        "Metadata (JSON)": dash(r.get("json_url") or r.get("metadata_url")),
        "_DateKey": to_date_key(r),  
    }
    
table_rows = [row_from_record(r) for r in filtered]
df_full = pd.DataFrame(table_rows)

if not df_full.empty:
    df_full = df_full.sort_values("_DateKey", ascending=False, kind="mergesort")
    df_display = df_full.drop(columns=["_DateKey"])
else:
    df_display = df_full

# Pagination
ROWS_PER_PAGE = 50
if "table_page" not in ss:
    ss.table_page = 0

total_pages = max(1, (len(df_display) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
start_idx = ss.table_page * ROWS_PER_PAGE
end_idx = min(start_idx + ROWS_PER_PAGE, len(df_display))
df_page = df_display.iloc[start_idx:end_idx]

# Show current page
st.markdown("# Benchmark FIM Records on Tabular View")
st.write("")
st.markdown("<hr style='border:0.5px solid rgba(44,127,184,0.35); margin:1rem 0;' />", unsafe_allow_html=True)
st.write("")

# dataframe styling
st.markdown(
    """
    <style>
    /* Make absolutely every text node inside column headers bold + black */
    [data-testid="stDataFrame"] div[role="columnheader"] *,
    [data-testid="stDataFrame"] div[role="columnheader"]  {
        font-weight: 900 !important;
        color: #000 !important;
        text-shadow: none !important; /* in case theme applies subtle shading */
    }

    /* Optional: stronger header background + bottom border */
    [data-testid="stDataFrame"] div[role="columnheader"] {
        background-color: #f2f2f2 !important;
        border-bottom: 2px solid #ccc !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.dataframe(
    df_page,
    width='stretch',
    hide_index=True,
    column_config={
        "Download FIM (TIF)": st.column_config.LinkColumn("Download FIM (TIF)", display_text="Download"),
        "Metadata (JSON)": st.column_config.LinkColumn("Metadata (JSON)", display_text="Open"),
        "Resolution (m)": st.column_config.NumberColumn(format="%.2f"),
    }
)

# Pager
c1, _, c3 = st.columns([1, 2, 1])
with c1:
    if st.button("⬅ Previous", disabled=ss.table_page == 0):
        ss.table_page -= 1
        st.rerun()
with c3:
    if st.button("Next ➡", disabled=ss.table_page >= total_pages - 1):
        ss.table_page += 1
        st.rerun()

st.caption(f"Page {ss.table_page + 1} of {total_pages} — Showing {len(df_page):,} of {len(df_display):,} records")


# MAP ACTIONS
with st.sidebar:
    st.header("Map actions")
    colA, colB = st.columns(2)
    with colA:
        if st.button("Zoom −", use_container_width=True):
            ss.saved_zoom = max(2.0, float(ss.saved_zoom) - 1.0)
            ss.filters_changed = True
    with colB:
        if st.button("Zoom +", use_container_width=True):
            ss.saved_zoom = min(18.0, float(ss.saved_zoom) + 1.0)
            ss.filters_changed = True

    if st.button("Center on USA", use_container_width=True):
        ss.saved_center = [39.8283, -98.5795]
        ss.saved_zoom = 5.0
        ss.filters_changed = True


