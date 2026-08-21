.PHONY: build clean

# Build wheel + sdist into a dist/ containing only the current version.
# Use this instead of a bare `uv build`, which leaves stale versions behind.
build:
	./scripts/build.sh

# Remove all build output and caches.
clean:
	rm -rf dist build src/*.egg-info
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
