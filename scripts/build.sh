#!/usr/bin/env bash
# Build FIMbench's wheel + sdist into a dist/ that holds ONLY the current version.
#
# Plain `uv build` *appends* to dist/, so artifacts from every past version pile
# up: dist/ grows without bound and `twine upload dist/*` would re-publish old
# releases. This wrapper wipes dist/ first, so it always holds exactly two
# files. It also deletes the `.gitignore` (contents: `*`) that uv drops into
# dist/, so the fresh artifacts show up in `git status`. They stay untracked on
# purpose -- releases go to PyPI, not into git history.
set -euo pipefail

cd "$(dirname "$0")/.."

version="$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)"
if [ -z "$version" ]; then
    echo "build.sh: could not read version from pyproject.toml" >&2
    exit 1
fi

rm -rf dist
uv build "$@"
rm -f dist/.gitignore

printf '\nfimbench %s -> dist/ (previous versions removed)\n' "$version"
ls -lh dist
