# Release Management for RetroChat v3

This document explains how the automated build and release process works.

## Automated Builds

Every push to the `main` branch triggers an automated build that:

1. **Builds Windows Executable**: Creates `rchat.exe` using PyInstaller
2. **Builds Python Package**: Creates `.whl` and `.tar.gz` files for pip installation
3. **Creates Development Release**: Publishes a development release with version `3.0.0.devXXX+{commit-hash}`

## Creating Official Releases

To create an official release:

1. **Tag a version**:
   ```bash
   git tag v3.0.0
   git push origin v3.0.0
   ```

2. **GitHub Actions will automatically**:
   - Build the executable and packages
   - Create a GitHub release with proper release notes
   - Upload all build artifacts
   - (Optional) Publish to PyPI if configured

## Version Numbering

- **Development builds**: `3.0.0.dev{commit-count}+{short-sha}` (e.g., `3.0.0.dev42+abc1234`)
- **Official releases**: `3.0.0` (follows semantic versioning)

## Installation Methods After Release

### For End Users
```bash
# Method 1: Download executable (Windows)
# Download rchat-3.0.0.exe from GitHub releases

# Method 2: Install via pip
pip install retrochat-cli

# Method 3: Install from GitHub
pip install git+https://github.com/DefamationStation/retrochat-v3.git@v3.0.0
```

### For Developers
```bash
# Install development version
pip install git+https://github.com/DefamationStation/retrochat-v3.git

# Or clone and install locally
git clone https://github.com/DefamationStation/retrochat-v3.git
cd retrochat-v3
pip install -e .
```

## Local Testing

Before pushing changes, you can test the build process locally:

### Windows
```powershell
.\build.ps1
```

### Cross-platform
```bash
python -m build
pip install pyinstaller
pyinstaller retrochat.spec
```

## GitHub Secrets Configuration

For PyPI publishing (optional), configure these secrets in your GitHub repository:

1. Go to Settings > Secrets and variables > Actions
2. Add `PYPI_TOKEN` with your PyPI API token

## File Structure

```
retrochat-v3/
├── .github/workflows/
│   └── build-and-release.yml    # GitHub Actions workflow
├── main.py                      # Entry point
├── setup.py                     # Python package configuration  
├── retrochat.spec              # PyInstaller configuration
├── build.ps1                   # Local build script (Windows)
├── test_build.py              # Build verification script
└── RELEASE.md                 # This file
```

## Troubleshooting

### Build Fails
- Check that all dependencies are listed in `requirements.txt`
- Verify PyInstaller can find all modules (check `hiddenimports` in `retrochat.spec`)
- Test locally first with `.\build.ps1`

### Package Install Fails
- Ensure `setup.py` has correct entry points
- Check that all source files are included in the package
- Test with `pip install -e .` locally

### Executable Doesn't Work
- Check that all data files are included in PyInstaller spec
- Test with various Windows versions
- Verify no absolute paths are hardcoded
