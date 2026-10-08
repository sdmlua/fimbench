# Flood map metadata

Every flood map in the FIMbench database has a `metadata.json` file stored
next to its raster. The file describes the raster itself, where it is, which
flood it shows, where it came from, and how severe the event was. This page
explains every metadata field, how its value is produced, and how it differs
between FIM categories. It also covers the files built from the metadata: the
AOI GeoPackage, the extent GeoJSON, and the web catalog.

The metadata is written by the processors in
[`fimbench.processing_floodmap`](../src/fimbench/processing_floodmap/), one per
category.

---

## Contents

1. [What each flood map consists of](#1-what-each-flood-map-consists-of)
2. [FIM categories at a glance](#2-fim-categories-at-a-glance)
3. [Which fields each category has](#3-which-fields-each-category-has)
4. [Field reference](#4-field-reference)
5. [Example metadata.json files](#5-example-metadatajson-files)
6. [Companion files: AOI.gpkg and extent GeoJSON](#6-companion-files-aoigpkg-and-extent-geojson)
7. [From metadata to the web catalog](#7-from-metadata-to-the-web-catalog)
8. [Notes and caveats](#8-notes-and-caveats)

---

## 1. What each flood map consists of

Processing one raw flood raster produces a folder containing three files, plus
an optional extent GeoJSON written elsewhere:

```
{folder}/
├── {name}_BM.tif           # the benchmark flood map (GeoTIFF, EPSG:4326)
├── {name}_metadata.json    # the metadata described on this page
└── {name}_AOI.gpkg         # area of interest: valid-data footprint + metadata
{geojson_dest}/
└── {name}_extent.geojson   # flooded area + key metadata (optional)
```

### Naming convention

| Category | Folder | File stem `{name}` |
|---|---|---|
| Tier 1, 2, 3 | `{SENSOR}_{date}_{DMS}` | `{SENSOR}_{res}_{date}_{DMS}` |
| HWM | `HWM_{start}_{end}_{DMS}` | `HWM_{res}_{start}_{end}_{DMS}` |
| FEMA BLE | `BLE_{return period}_{DMS}` | `BLE_{res}_{return period}_{DMS}` |

- `{SENSOR}` is the sensor code: `AI`, `PSS`, `S1A`, `HWM` or `BLE`.
- `{res}` is the resolution with `_` in place of the decimal point, for example `0_3m` or `10_0m`. See [Resolution in meter](#resolution-in-meter).
- `{date}` is the flood date as given, either `YYYYMMDD` or `YYYYMMDDTHHMMSS`.
- `{start}` and `{end}` are the HWM flood window, each as `YYYYMMDD`.
- `{DMS}` is the centroid code, for example `953036W293058N`. See [DMS_Code_centroid](#dms_code_centroid).

Examples:

```
Tier_1/AI_20170903_953036W293058N/AI_0_3m_20170903_953036W293058N_metadata.json
Tier_2/PSS_20240623T163213_951204W425252N/PSS_3_0m_20240623T163213_951204W425252N_metadata.json
HWM/HWM_20170916_20170930_660421W182426N/HWM_10_1m_20170916_20170930_660421W182426N_metadata.json
FEMA_BLE/BLE_500_932457W352955N/BLE_10_0m_500_932457W352955N_metadata.json
```

In S3, these folders sit under `FIM_Database/{Tier_1 | Tier_2 | Tier_3 | HWM | FEMA_BLE}/`.

---

## 2. FIM categories at a glance

| Category | Processor | Sensor code | `Full form of the sensor code` | `Quality` | Event timing |
|---|---|---|---|---|---|
| **Tier 1**: Aerial imagery | `Tier1Processor` | `AI` | Aerial Imagery | `Tier 1` | Flood date |
| **Tier 2**: PlanetScope | `Tier2Processor` | `PSS` | Planet Scope Scene | `Tier 2` | Date + UTC acquisition time |
| **Tier 3**: Sentinel-1 | `Tier3Processor` | `S1A` | Sentinel-1A | `Tier 3` | Date + UTC acquisition time |
| **HWM**: High Water Marks | `HwmProcessor` | `HWM` | High Water Mark | none | Flood window (start–end) |
| **FEMA BLE**: Base Level Engineering | `FemaBleProcessor` | `BLE` | Base Level Engineering | none | Return period (synthetic) |

Default `Source` per category (it can be overridden with `source=` when
creating the processor, except for Tier 2; see [Section 8](#8-notes-and-caveats)):

| Category | `Source` |
|---|---|
| Tier 1, HWM | Dr. Dinuke Munasinghe, The University of Alabama (dsmunasinghe@ua.edu) |
| Tier 2, Tier 3 | Dr. Dan Tian, The University of Alabama (dtian1@ua.edu) |
| FEMA BLE | NOAA/NWS Office of Water Prediction (OWP) |

---

## 3. Which fields each category has

✓ = present, — = not present.

| Field | Tier 1 | Tier 2 | Tier 3 | HWM | FEMA BLE |
|---|:-:|:-:|:-:|:-:|:-:|
| **Identification** | | | | | |
| `File_Name` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `Full form of the sensor code` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `Description` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `Source` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `Quality` | ✓ | ✓ | ✓ | — | — |
| `Keywords` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `Access_Rights` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `References` | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Raster properties** | | | | | |
| `Format`, `Nodata_Value`, `Datatype`, `Compression Type` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `Resolution in meter` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `Projection`, `Bands`, `Rows`, `Columns` | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Location** | | | | | |
| `Extent` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `Location of the centroid of the flood map` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `DMS_Code_centroid` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `HUC8` | ✓ | ✓ | ✓ | ✓ | ✓ (dominant only) |
| `River Basin Name` | ✓ | ✓ | ✓ | ✓ | ✓ (dominant only) |
| `State` | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Event** | | | | | |
| `Flooding Event` | ✓ | ✓ | ✓ | — | — |
| `Date of the flooding` | ✓ | ✓ | ✓ | — | — |
| `Acquisition Time in UTC` | — | ✓ | ✓ | — | — |
| `Start Date of the Flood`, `End Date of the Flood` | — | — | — | ✓ | — |
| `Synthetic Flooding Event (return period (years))` | — | — | — | — | ✓ |
| **Event severity** | | | | | |
| `Event Recurrence Interval (USGS)` | ✓ | ✓ | ✓ | ✓ | — |
| `Event Discharge (USGS) [cms]` | ✓ | ✓ | ✓ | ✓ | — |
| `USGS Gauge ID` | ✓ | ✓ | ✓ | ✓ | — |
| `Event Recurrence Interval (NWM)` | ✓ | ✓ | ✓ | ✓ | — |
| `Event Discharge (NWM) [cms]` | ✓ | ✓ | ✓ | ✓ | — |

---

## 4. Field reference

Fields appear in `metadata.json` in the order below (event fields sit between
`Location of the centroid of the flood map` and `Keywords`).

### 4.1 Identification

#### File_Name
The file name of the benchmark raster, for example
`AI_0_3m_20170903_953036W293058N_BM.tif`. It follows the
[naming convention](#naming-convention) and is the key used to find the
matching metadata, AOI and extent files.

#### Full form of the sensor code
The data source written out in full, for example `"Aerial Imagery"` or
`"Planet Scope Scene"`. See the table in [Section 2](#2-fim-categories-at-a-glance).

#### Description
One sentence describing the map. It is filled in after the HUC8 lookup and
follows a fixed template per category:

| Category | Template |
|---|---|
| Tier 1 | The Flood Inundation Map (FIM) was generated using NOAA Emergency Response Imagery acquired for the `{date}` flood with a spatial resolution of `{res}`. The corresponding HUC IDs are `{HUC8}` |
| Tier 2 | … generated using Planet Scope Scene imagery combined with a gap-filled algorithm for the `{date}` flood … |
| Tier 3 | … generated using Sentinel-1 Imagery combined with a gap-filled algorithm for the `{date}` flood … |
| HWM | … generated using USGS High Water Marks acquired for the `{start}-{end}` flood … |
| FEMA BLE | The Flood Inundation Map (FIM) corresponds to FEMA Base Level Engineering for the `{return period}` flood … |

`{res}` is written with two decimals and a unit, for example `0.30 m`.

#### Source
Who produced the flood map, with an institution and contact email. See the
defaults in [Section 2](#2-fim-categories-at-a-glance).

#### Quality
The data tier: `"Tier 1"`, `"Tier 2"` or `"Tier 3"`. HWM and FEMA BLE
metadata have no `Quality` field. In the web catalog they are labelled
`"High Water FIM"` and `"FEMA Base Level Engineering"` instead (see
[Section 7](#7-from-metadata-to-the-web-catalog)).

#### Keywords
Always `["flood", "hazard", "GIS"]`.

#### Access_Rights
Always `"Public"`.

#### References
A list of four citations for the FIMbench database and its methods. It is
the same for every map.

### 4.2 Raster properties

All raster properties describe the final `_BM.tif`, which is in EPSG:4326.

| Field | Meaning | Typical value |
|---|---|---|
| `Format` | GDAL driver of the raster | `"GTiff"` |
| `Nodata_Value` | Value used for pixels with no data | `-9999.0` |
| `Datatype` | Pixel data type. Integer sources are stored as `int32`, floating-point sources as `float32` | `"int32"` |
| `Compression Type` | GeoTIFF compression and interleaving | `{"COMPRESSION": "LZW", "INTERLEAVE": "BAND"}` |
| `Projection` | Coordinate reference system | `"EPSG:4326"` |
| `Bands` | Number of bands | `1` |
| `Rows`, `Columns` | Raster height and width in pixels | `117396`, `129344` |

#### Resolution in meter
The pixel size in metres. The raster is reprojected to EPSG:5070 (CONUS Albers,
metres), the x and y pixel sizes are averaged, and the result is rounded to
0.1 m.

Because it is measured after reprojection, it can differ slightly from the
source's nominal resolution. For example, a 10 m HWM raster may be recorded as
`9.4` or `10.1`. The same value, with `_` for the decimal point, appears in the
file name (`10_1m`).

### 4.3 Location

#### Extent
The bounding box of the `_BM.tif`, in decimal degrees (EPSG:4326):

```json
"Extent": {"xmin": -95.684, "ymin": 29.358, "xmax": -95.336, "ymax": 29.674}
```

This box covers the whole raster, including any nodata margin. It is not the
box around the flooded pixels.

#### Location of the centroid of the flood map
`[longitude, latitude]` of the centre of the `Extent` box, in decimal degrees.
It is the centre of the raster's bounding box, not the centre of the flooded
area.

#### DMS_Code_centroid
The centroid written as degrees-minutes-seconds without separators: longitude
first, then latitude, each with its hemisphere letter. For example, `953036W293058N`
means 95°30′36″ W, 29°30′58″ N. Values are truncated, not rounded, to whole
seconds. Longitudes of 100° or more give a longer code, for example
`1091442W451109N`.

The code identifies the map's location in its folder and file names.

#### HUC8
A list of the 8-digit USGS Watershed Boundary Dataset (WBD) HUC codes for the
watersheds the flooded area falls in, for example `["12040205", "12070104"]`.

They are found by querying the public ArcGIS REST service for WBD HUC8
boundaries with the flood polygon (every pixel with value > 0, from the
EPSG:5070 raster):

- **Tier 1, 2, 3 and HWM:** every HUC8 the flooded area intersects, sorted.
- **FEMA BLE:** only the single HUC8 that holds most of the flooded area,
  because BLE maps are produced per watershed. If no HUC8 holds at least 70 %
  of the area, the largest one is still used, and the shares are logged.

When nothing intersects (for example, outside the WBD coverage), the list is empty.

#### River Basin Name
The names of the HUC8 watersheds in `HUC8`, sorted, for example
`["Austin-Oyster", "Lower Brazos"]`.

#### State
The two-letter codes of the states the HUC8 watersheds cover, sorted and
followed by `", USA"`, for example `"IA, MN, USA"`. It is `"USA"` when no HUC8
was found.

These are the states of the watersheds, so a map can list a state it doesn't
itself reach. Territories appear by their code, for example `"PR, USA"`.

### 4.4 Event timing

The event fields depend on the category.

#### Tier 1, 2, 3: Flooding Event, Date of the flooding, Acquisition Time in UTC

| Field | Tier 1 | Tier 2, Tier 3 |
|---|---|---|
| `Flooding Event` | The flood date as given, usually `YYYYMMDD` | Date and acquisition time, `YYYYMMDDTHHMMSS`, for example `"20240623T163213"` |
| `Date of the flooding` | Same as `Flooding Event` | Date part only, `YYYYMMDD` |
| `Acquisition Time in UTC` | not present | Time part as `HH:MM:SS` (or `HH:MM` for a 4-digit time); `null` when no time was given |

The flood date is passed to the processor, or read from the file name
(`YYYYMMDD`, `YYYY-MM-DD` or `DD-MM-YYYY`, optionally followed by
`T<time>`). Times are in UTC.

#### HWM: Start Date of the Flood, End Date of the Flood
The flood window, each as `YYYYMMDD`, for example `"20170916"` and
`"20170930"`. High water marks record the highest water reached during an
event, so a window is used instead of a single date. The dates are read from
the file name (`…_YYYYMMDD_YYYYMMDD_…`), or passed explicitly to the processor.

#### FEMA BLE: Synthetic Flooding Event (return period (years))
The return period of the design flood in years, as a string, for example
`"100"` or `"500"`. BLE maps model a hypothetical flood of that size, not an
observed event, so they have no date.

### 4.5 Event severity (recurrence interval)

Observed-flood maps (Tier 1, 2, 3 and HWM) carry two independent estimates of
how rare the flood was. One uses observed USGS streamflow, the other the
National Water Model (NWM). The full procedure, including every scenario and
failure label, is in
**[recurrence-interval_documentation.md](recurrence-interval_documentation.md)**.

| Field | Type | Values |
|---|---|---|
| `Event Recurrence Interval (USGS)` | string or null | A return period (`"2 yr"` … `"100 yr"`, `"< 2 yr"`, `"> 100 yr"`); `"No USGS Gauge"`; `"No usable USGS Gauge"`; `null` if the lookup couldn't be attempted |
| `Event Discharge (USGS) [cms]` | number or null | Observed discharge at the gage in m³/s, 2 decimals; `null` unless a return period was assigned |
| `USGS Gauge ID` | string or null | USGS site number of the gage used, for example `"06605850"` |
| `Event Recurrence Interval (NWM)` | string | A return period, or a short reason why none could be assigned, for example `"No outlet reach found"` |
| `Event Discharge (NWM) [cms]` | number or null | Modeled discharge at the flood's outlet reach in m³/s, 2 decimals |

The discharge behind each estimate depends on the category:

| Category | Discharge used |
|---|---|
| Tier 1 (date only) | Daily maximum of hourly discharge on the flood date |
| Tier 2, Tier 3 (date + time) | Discharge nearest the acquisition time |
| HWM | Maximum discharge over the flood window |

FEMA BLE maps have no recurrence-interval fields, because the return period is
already part of their definition.

---

## 5. Example metadata.json files

### Tier 3 (Sentinel-1)

`Tier_3/S1A_20180213T233042_840231W364457N/S1A_8_5m_20180213T233042_840231W364457N_metadata.json`

```json
{
    "File_Name": "S1A_8_5m_20180213T233042_840231W364457N_BM.tif",
    "Full form of the sensor code": "Sentinel-1A",
    "HUC8": ["05130101"],
    "Format": "GTiff",
    "Nodata_Value": -9999.0,
    "Resolution in meter": 8.5,
    "Datatype": "float32",
    "Compression Type": {"COMPRESSION": "LZW", "INTERLEAVE": "BAND"},
    "Extent": {"xmin": -84.17817, "ymin": 36.69268, "xmax": -83.90604, "ymax": 36.80620},
    "DMS_Code_centroid": "840231W364457N",
    "Projection": "EPSG:4326",
    "Bands": 1,
    "Rows": 1226,
    "Columns": 2939,
    "State": "KY, TN, VA, USA",
    "Description": "The Flood Inundation Map (FIM) was generated using Sentinel-1 Imagery combined with a gap-filled algorithm for the 20180213T233042 flood with a spatial resolution of 8.50 m. The corresponding HUC IDs are ['05130101']",
    "River Basin Name": ["Upper Cumberland"],
    "Source": "Dr. Dan Tian,The University of Alabama, Email id: dtian1@ua.edu",
    "Location of the centroid of the flood map": [-84.04210, 36.74944],
    "Flooding Event": "20180213T233042",
    "Date of the flooding": "20180213",
    "Acquisition Time in UTC": "23:30:42",
    "Event Recurrence Interval (USGS)": "5 yr",
    "Event Discharge (USGS) [cms]": 954.28,
    "USGS Gauge ID": "03404000",
    "Event Recurrence Interval (NWM)": "5 yr",
    "Event Discharge (NWM) [cms]": 1115.08,
    "Keywords": ["flood", "hazard", "GIS"],
    "Access_Rights": "Public",
    "Quality": "Tier 3",
    "References": ["1. Cohen, S., Baruah, A., ...", "2. ...", "3. ...", "4. ..."]
}
```

(Coordinates are shortened and the references abbreviated here.)

### How the other categories differ

**Tier 1** has no `Acquisition Time in UTC`, and `Date of the flooding`
repeats `Flooding Event`:

```json
"Flooding Event": "20170903",
"Date of the flooding": "20170903",
"Event Recurrence Interval (USGS)": "No usable USGS Gauge",
"Event Discharge (USGS) [cms]": null,
"USGS Gauge ID": null,
"Event Recurrence Interval (NWM)": "2 yr",
"Event Discharge (NWM) [cms]": 2140.68,
"Quality": "Tier 1"
```

**Tier 2** has the same structure as Tier 3. Here the NWM estimate failed
because the operational archive no longer had the file:

```json
"Flooding Event": "20240623T163213",
"Date of the flooding": "20240623",
"Acquisition Time in UTC": "16:32:13",
"Event Recurrence Interval (USGS)": "> 100 yr",
"Event Discharge (USGS) [cms]": 1523.44,
"USGS Gauge ID": "06605850",
"Event Recurrence Interval (NWM)": "NWM discharge unavailable: no short-range file for valid time 2024-06-23 17:00:00+00:00 at COMID 14621904 (archive expired?)",
"Event Discharge (NWM) [cms]": null,
"Quality": "Tier 2"
```

**HWM** replaces the event date with a window and has no `Quality`:

```json
"Start Date of the Flood": "20170916",
"End Date of the Flood": "20170930",
"Event Recurrence Interval (USGS)": "No usable USGS Gauge",
"Event Recurrence Interval (NWM)": "No outlet reach found",
...
```

**FEMA BLE** replaces all event and severity fields with the return period,
and has no `Quality`:

```json
"Source": "NOAA/NWS Office of Water Prediction (OWP)",
"Synthetic Flooding Event (return period (years))": "500",
"Keywords": ["flood", "hazard", "GIS"],
...
```

---

## 6. Companion files: AOI.gpkg and extent GeoJSON

### `{name}_AOI.gpkg`
The area of interest for the map: the footprint of the raster's valid data.

- **Layer:** `AOI`, one feature.
- **Geometry:** the area where the raster has data (not nodata or NaN),
  whether flooded or dry, in EPSG:4326. It is simplified with a tolerance of
  0.0001° (about 11 m).
  - For Tier 1 aerial maps (0.2–0.5 m pixels), the footprint is built on a
    coarse grid of about 5 m and read in chunks. This keeps very large rasters
    fast and the file small. Nodata gaps and specks smaller than the tolerance
    are dropped.
- **Attributes:** all fields of `metadata.json`.

It is used to check whether a model's prediction overlaps a benchmark map, for
example by the `query` module.

### `{name}_extent.geojson` (optional)
The flooded area with a selection of metadata. It is written only when
`geojson_dest` is passed to `process()`, into that separate folder.

- **Geometry:** every flooded pixel (value > 0) of the EPSG:5070 raster,
  merged into one MultiPolygon. It is simplified by 10 m, which also drops
  patches smaller than that, then converted to EPSG:4326 with coordinates
  rounded to 6 decimals (about 0.1 m).
- **Properties:** a subset of the metadata fields:

| Category | Properties |
|---|---|
| Tier 1 | `File_Name`, `Full form of the sensor code`, `HUC8`, `Resolution in meter`, `Extent`, `State`, `River Basin Name`, `Flooding Event`, the five event-severity fields, `Quality` |
| Tier 2 | As Tier 1, plus `Source` |
| Tier 3 | As Tier 1 |
| HWM | As Tier 1, but `Start Date of the Flood` and `End Date of the Flood` instead of `Flooding Event`, and no `Quality` |
| FEMA BLE | `File_Name`, `Full form of the sensor code`, `HUC8`, `Resolution in meter`, `Extent`, `State`, `River Basin Name`, `Synthetic Flooding Event (return period (years))` |

The extent GeoJSONs of all maps are merged and smoothed to build the web
map's `FIM_extents.geojson` and vector tiles (see the next section).

---

## 7. From metadata to the web catalog

`FIMCatalogBuilder` ([`webcontent_utils/build_catalog.py`](../src/fimbench/webcontent_utils/build_catalog.py))
reads every `*_metadata.json` under `FIM_Database/` in S3 and turns each one
into a record in `catalog_core.json`. The web map, the vector tiles and the
`query` module all use these records, not the metadata files directly.

| Catalog field | Comes from |
|---|---|
| `id` | `{tier}/{folder}/{File_Name without .tif}` |
| `site_id` | The map's folder name |
| `tier` | The S3 prefix: `Tier_1`, `Tier_2`, `Tier_3`, `HWM` or `FEMA_BLE` |
| `date_ymd` | `Flooding Event` as `YYYY-MM-DD` (Tier 1, 2, 3) |
| `event_ts` | The date and time from `Flooding Event` as written, for example `20240623T163213` (Tier 1, 2, 3 only) |
| `start_date_ymd`, `end_date_ymd` | `Start/End Date of the Flood` as `YYYY-MM-DD` (HWM) |
| `return_period` | `Synthetic Flooding Event (return period (years))` (FEMA BLE) |
| `json_url`, `tif_url`, `gpkg_url` | S3 URLs of the metadata, raster and AOI |
| `s3_prefix` | The map's folder in S3 |
| `centroid` | `Location of the centroid of the flood map` |
| `bbox` | `Extent` as `[xmin, ymin, xmax, ymax]` |
| `resolution_m` | `Resolution in meter` |
| `huc8` | `HUC8` |
| `state`, `basin` | `State`, `River Basin Name` |
| `source`, `access_rights`, `description`, `references` | `Source`, `Access_Rights`, `Description`, `References` |
| `file_name` | `File_Name` |
| `quality` | `Quality` for Tier 1, 2, 3; `"High Water FIM"` for HWM; `"FEMA Base Level Engineering"` for FEMA BLE |

The event-severity fields are not copied into the catalog. They stay in each
map's `metadata.json`, which the catalog links to through `json_url`.

`CatalogandTileManager` ([`webcontent_utils/tiling.py`](../src/fimbench/webcontent_utils/tiling.py))
then joins these catalog fields onto the merged extents to build
`FIM_extents.geojson` and the vector tiles in `FIM_Database/FIM_Viz/`.

---

## 8. Notes and caveats

- **Tier 2 `Source` can't be overridden.** The metadata builder sets `Source`
  twice, and the second, hard-coded value
  (`"Dr. Dan Tian ,The University of Alabama, …"`) wins. A `source=` passed to
  `Tier2Processor` has no effect.
- **The Tier 2 quality-control ratio isn't stored.** `Tier2Processor` computes
  the ratio of class-1 to class-2 pixels (described in the module as a
  quality-control threshold), but the value is not written to the metadata.
- **`Extent` and the centroid describe the whole raster**, including nodata
  margins, not just the flooded area.
- **`Resolution in meter` is measured after reprojection** to EPSG:5070, so it
  can differ by a few tenths of a metre from the source's nominal resolution.
- **`State` comes from the HUC8 watersheds**, so it can include a state the
  flooded area doesn't reach.
- **Dates and times** are strings in `YYYYMMDD` or `YYYYMMDDTHHMMSS` form, and
  times are UTC. The catalog converts them to `YYYY-MM-DD`.
