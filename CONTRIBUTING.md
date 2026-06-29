# Contributing to fimbench

Thanks for your interest in contributing! `fimbench` is developed by the
[Surface Dynamics Modeling Lab (SDML)](https://github.com/sdmlua) and provides
flood inundation map (FIM) preprocessing, S3 database interaction, and querying
utilities for the FIMbench project.

## Getting started

1. **Fork and clone** the repository.

   ```bash
   git clone https://github.com/<your-username>/fimbench.git
   cd fimbench
   ```

2. **Create an environment and install in editable mode** with the dev extras.

   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

   Add optional capabilities as you need them:

   ```bash
   pip install -e ".[tiling]"   # vector tiles (also needs `tippecanoe` on PATH)
   pip install -e ".[publish]"  # ArcGIS Online publishing
   ```

3. **Create a branch** off `dev`.

   ```bash
   git checkout dev
   git checkout -b feature/short-description
   ```

## Where code goes

The package is organised into four groups, one per stage of the FIM data
lifecycle. Put new code in the group that matches its responsibility:

| Group                  | Responsibility                                                |
| ---------------------- | ------------------------------------------------------------- |
| `processing_floodmap/` | Raw flood map → standardized, DB-compatible artifact          |
| `webcontent_utils/`    | Create web content: build catalog, make/serve tiles, smooth   |
| `query/`               | Query availability of data in the database, download assets   |
| `publish/`             | Push catalog/tiles to S3 and extents to ArcGIS Online         |

`webcontent_utils` **creates** content; `publish` **pushes** it out — new
destinations are new `upload_*` modules under `publish`. S3 interaction lives in
`publish/s3/`; anything that talks to S3 should go through `fimbench.publish.s3`
rather than constructing its own `boto3` client.

## Code style

- **Formatting:** [`black`](https://black.readthedocs.io/) (line length 100).
- **Linting:** [`ruff`](https://docs.astral.sh/ruff/) (line length 100).
- Add type hints and a module/function docstring to new code.

```bash
black src tests
ruff check src tests
```

## Tests

Tests live in `tests/`, mirroring the subpackage they cover
(e.g. `tests/test_processing_metadata.py`). Run them with:

```bash
pytest
```

Please add or update tests for any behavior you change.

## Commit messages and pull requests

- Write clear, imperative commit messages (e.g. "add GeoPackage writer").
- Open pull requests against the `dev` branch.
- In the PR description, explain *what* changed and *why*, and link any related
  issue.
- Make sure `black`, `ruff`, and `pytest` pass before requesting review.

## Reporting issues

Open an issue describing:

- what you expected to happen,
- what actually happened (with the traceback if any),
- a minimal way to reproduce it,
- your OS and Python version.

## License

This project is dual-licensed (see [LICENSE](LICENSE)): the software / source
code under **CC BY 4.0**, and the FIMbench dataset under **CC BY-NC 4.0**
(non-commercial). By contributing code, you agree that your contributions will
be licensed under the project's CC BY 4.0 license.

## Questions

Reach out to Supath Dhital — sdhital@ua.edu.
