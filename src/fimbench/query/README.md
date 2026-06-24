# fimbench.query

Query benchmark flood inundation maps (FIMs) from the database and download
matched assets.

## Use

```python
from fimbench.query import benchFIMquery

response = benchFIMquery(
    file_name="HWM_10_0m_20160928_20161009_780051W352232N_BM.tif",
    download=True,
    out_dir="../downloads/",
)
print(response)
```

## Filter combinations

| Filters                                  | Result                                  |
| ---------------------------------------- | --------------------------------------- |
| `file_name`                              | Direct lookup / download by filename    |
| `raster_path` or `boundary_path` (AOI)   | Spatial search; `area=True` adds overlap |
| AOI + `event_date`                       | Match on an exact event date            |
| AOI + `start_date` / `end_date`          | Match within a date range               |
| `huc8`, `tier`                           | Narrow by basin / benchmark tier        |

Set `download=True` (with `out_dir`) to fetch matched rasters and GeoPackages.

## Files

- `access_benchfim.py` — `benchFIMquery`, the high-level access/query service.
- `utilis.py` — catalog loading, S3 listing/download, date & tier helpers.
