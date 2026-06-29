# fimbench.processing_floodmap

This standalone module helps to standardize a raw benchmark flood map into the FIMbench database format. It is now structured as one class per flooding map source;
each writes the renamed GeoTIFF, metadata.json, and AOI.gpkg into a per-map
folder under the destination. Logic is kept faithful to the source notebooks,
so the output matches.

Intersected HUC8 watersheds informations for metadata within US are resolved on the fly from the ArcGIS REST service
(`utils.get_intersected_huc8`)

## Classes

- `Tier1Processor` — Aerial Imagery (AI)
- `Tier2Processor` — Planet Scope Scene (PSS)
- `Tier3Processor` — Sentinel 1A (S1A)
- `FemaBleProcessor` — FEMA Base Level Engineering (BLE), uses a return-period event
- `HwmProcessor` — High Water Mark (HWM), single TIF + start/end date

Defaults (`SENSOR_CODE`, `SOURCE`, `NODATA_VAL`, `SIMPLIFY_TOL`, ...) are class
attributes and can be overridden via keyword args.

## Use

```python
from fimbench.processing_floodmap import Tier1Processor

Tier1Processor().process("in/rasters", "out/")
# override a default:
Tier1Processor(source="My source").process("in/rasters", "out/")
```

Each module also exposes a `process(...)` shortcut:

```python
from fimbench.processing_floodmap import tier1, fema_ble, hwm

tier1.process("in/", "out/")
fema_ble.process("in/", "out/", event="100")
hwm.process("map.tif", "out/", start_date="160928", end_date="161009")
```
**For more usage notes refer to the [tests](../../../tests/) or [docs](../../../docs/) for the fimbench python package**