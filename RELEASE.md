# Release Process

## Prerequisites
- Push access to the repository
- Docker Hub credentials (`DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` in GitHub Secrets)
- PyPI API token (`PYPI_TOKEN` in GitHub Secrets) — for `publish-to-pypi` workflow

## Steps

1. **Update version** in `setup.py`, `debian/changelog`, and `Makefile`:
   ```bash
   # setup.py — set version = 'X.Y.Z'
   # Makefile — set VERSION=X.Y.Z
   # debian/changelog — add X.Y.Z-1 entry (dpkg-buildpackage uses this to version the .deb)
   ```

2. **Update `CHANGELOG.md`** — add the new version heading with release notes.

3. **Commit the version bump, deb changelog and changelog**:
   ```bash
   git add setup.py Makefile debian/changelog CHANGELOG.md
   git commit -m "Bump version to X.Y.Z"
   ```

4. **Tag the release**:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   ```

5. **Push**:
   ```bash
   git push origin master
   git push origin vX.Y.Z
   ```

   Pushing the tag triggers the GitHub Actions workflow (`.github/workflows/deploy-image.yml`) which:
   - Runs tests
   - Builds and pushes multi-arch Docker images (`linux/amd64`, `linux/arm64`) to Docker Hub
   - Tags images with semver (`X.Y.Z`, `X.Y`, `X`, `sha-...`)

6. **Build and upload to PyPI** (if applicable):
   ```bash
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```

7. **Build deb package** (if applicable):
   ```bash
   python setup.py --command-packages=stdeb.command bdist_deb
   ```

   Note: When the tag is pushed, GitHub Actions automatically creates a GitHub Release with release notes extracted from `CHANGELOG.md`.

## Versioning

Follows [SemVer](https://semver.org/):
- **Patch** (X.Y.Z+1): bug fixes, minor docs
- **Minor** (X.Y+1.0): new features, non-breaking changes
- **Major** (X+1.0.0): breaking changes
