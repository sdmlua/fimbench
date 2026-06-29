# fimbench.query

Query benchmark flood inundation maps (FIMs) from the FIMbench database and,
optionally, download the matched assets (GeoTIFF + AOI GeoPackage). This is the
read side of the package: it reads the unified catalog core published by
[`fimbench.publish`](../publish/README.md) and returns plain Python dicts, so it doesnot
needs any **AWS credentials** to access data, the catalog and assets are served as public,
anonymous S3 reads.

## Connecting to an evaluation framework

`benchFIMquery` is built to drop into any FIM evaluation pipeline:

- **Plain-dict output.** Every call returns a regular `dict` (`status`,
  `message`, `matches`, `printable`). No custom classes to import, so it
  serializes straight to JSON and is trivial to assert on in tests.
- **AOI-driven matching.** Hand it the same predicted-FIM raster (or AOI
  boundary) your model produced via `raster_path` / `boundary_path`; it returns
  the benchmark records that cover that area — the natural "ground truth" pair
  for a contingency / CSI / POD-FAR style metric.
- **Local paths on demand.** With `download=True`, each match carries the
  local file paths of the downloaded benchmark raster and GeoPackage, so the
  evaluator can read them directly with rasterio / GDAL / geopandas.
- **No credentials, no state.** Because reads are anonymous, the same call works
  in CI, notebooks, and batch jobs; loop over events/HUC8s/tiers to build an
  evaluation matrix.

A typical loop: predict → `benchFIMquery(raster_path=..., download=True)` →
read the returned benchmark path → compute your metric against the prediction.

Based on the tier, area overlap, event dates, or any other preference, a user
can select exactly which benchmark FIMs to pull and feed downstream.

### Works seamlessly with FIMeval

`fimbench.query` powers benchmark access in
[**FIMeval**](https://github.com/sdmlua/fimeval), SDML's flood-map evaluation
framework. FIMeval uses `benchFIMquery` to discover and download the right
benchmark FIM for an area/event, then evaluates a predicted flood map against
it. Because the query returns plain dicts and local file paths, the same call
works standalone here or as the data-access layer inside FIMeval — query a
benchmark, access the assets, and evaluate, with no glue code.

## Use

All parameters are optional and keyword-only; combine them to narrow the search.

```python
from fimbench.query import benchFIMquery

# Scenario 1 — just query (no download): discover what benchmarks exist.
response = benchFIMquery(
    start_date="2016-04-01",
    end_date="2026-01-01",
    # huc8="03020201", tier="tier4",   # optionally narrow by basin / tier
)
print(response)                         # pretty summary
records = [m["record"] for m in response["matches"]]

# Scenario 2 — AOI search against your predicted FIM, with overlap stats.
response = benchFIMquery(
    raster_path="path/to/your_predicted_fim.tif",
    area=True,                          # adds overlap % and km² per match
)

# Scenario 3 — match an AOI for an event and download the benchmark assets.
response = benchFIMquery(
    boundary_path="path/to/aoi.gpkg",
    event_date="2017-08-30",
    download=True,
    out_dir="../downloads/",            # falls back to the AOI's folder if omitted
)
for m in response["matches"]:
    print(m["downloads"])               # local tif / gpkg paths to feed your evaluator

# Scenario 4 — direct download by exact filename.
response = benchFIMquery(
    file_name="HWM_10_0m_20160928_20161009_780051W352232N_BM.tif",
    download=True,
    out_dir="../downloads/",
)
```

## Filter combinations

| Filters                                  | Result                                  |
| ---------------------------------------- | --------------------------------------- |
| `file_name`                              | Direct lookup / download by filename    |
| `raster_path` or `boundary_path` (AOI)   | Spatial search; `area=True` adds overlap |
| AOI + `event_date`                       | Match on an exact event date            |
| AOI + `start_date` / `end_date`          | Match within a date range               |
| `start_date` / `end_date` only           | All records in the range (no AOI)       |
| `huc8`, `tier`                           | Narrow by basin / benchmark tier        |

`tier` is flexible (`'HWM'`, `'tier_1'`, `'Tier 2'`, `'tier3'`, ...). Set
`download=True` (with `out_dir`, or a `raster_path`/`boundary_path` whose folder
is reused) to fetch matched rasters and GeoPackages.

## Files

- `access_benchfim.py` — `benchFIMquery`, the high-level access/query service.
- `utilis.py` — catalog loading, anonymous S3 listing/download, date & tier helpers.

**For more usage notes refer to the [tests](../../../tests/) or [docs](../../../docs/) for the fimbench python package**
