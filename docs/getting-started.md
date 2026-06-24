# Getting started

## Requirements

- Python ≥ 3.10
- For tiling: [`tippecanoe`](https://github.com/felt/tippecanoe) on your `PATH`
  (`brew install tippecanoe`)

## Install

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# core package
pip install -e .

# with development tools
pip install -e ".[dev]"

# optional capabilities
pip install -e ".[tiling]"         # vector-tile generation
pip install -e ".[publish]"        # ArcGIS Online publishing
```

## Importing

```python
import fimbench as fb

# groups, one per lifecycle stage
from fimbench import processing_floodmap, webcontent_utils, query, publish

# the shared S3 layer lives under publish
from fimbench.publish import s3
```

## Configuration

S3 access is centralized in `fimbench.publish.s3`. Default bucket/prefix for the
FIM database live in `fimbench.publish.s3.s3_client`:

```python
DEFAULT_BUCKET = "sdmlab"
DEFAULT_PREFIX = "FIM_Database/"
```

Use standard AWS credential resolution (environment variables, shared profile,
or anonymous/unsigned access for public reads).

> The functional modules are being populated incrementally — see
> [architecture.md](architecture.md) for the intended responsibilities of each
> subpackage.
