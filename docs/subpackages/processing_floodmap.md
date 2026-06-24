# `fimbench.processing_floodmap`

Transform a *raw* flood inundation map into a standardized, database-compatible
artifact — the entry stage of the pipeline.

Given a heterogeneous input (raster extent or vector polygons, arbitrary CRS,
inconsistent fields) it produces a normalized GeoPackage plus a standardized
metadata document, so that everything downstream (`webcontent_utils`, `query`,
`publish`) can assume a single, consistent schema.

## Output

```
raw flood map  ->  standardized.gpkg  +  metadata.json
```

## Status

This package is **intentionally empty for now** — it holds only `__init__.py`.
Modules for flood-map normalization, metadata building, and GeoPackage writing
will be added here as the standardization workflow is implemented.
