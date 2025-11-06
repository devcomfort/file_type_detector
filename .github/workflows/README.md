# GitHub Actions Workflows

This directory contains CI/CD workflows for the project.

## Workflow Overview

| Workflow              | Purpose                   | Trigger                         | Required Secrets                       |
| --------------------- | ------------------------- | ------------------------------- | -------------------------------------- |
| `pypi-release.yml`    | Automatic PyPI deployment | Semantic Version change (X.Y.Z) | `PYPI_API_TOKEN`, `TESTPYPI_API_TOKEN` |
| `create-release.yml`  | Manual GitHub Release     | workflow_dispatch (manual)      | None (uses GITHUB_TOKEN)               |

---

## pypi-release.yml

Automatically deploys to PyPI when Semantic Version (X.Y.Z format) is updated.

### Trigger Conditions

1. **Automatic Trigger**: 
   - Runs automatically when `version` field in `pyproject.toml` changes to Semantic Version format on `main` branch
   - Format: `X.Y.Z` (e.g., `0.1.0`, `1.2.3`)
   - Pre-release versions like `0.1.0-dev` are ignored

2. **Manual Trigger**: 
   - Execute via `workflow_dispatch`
   - Select release type: `patch`, `minor`, `major`
   - Or specify a version number directly

### Workflow Process

1. **Version Validation**: Verify Semantic Version format (X.Y.Z)
2. **Test Execution**: Ensure all tests pass
3. **Package Build**: Create distribution packages using `python -m build`
4. **Package Validation**: Validate packages with `twine check`
5. **TestPyPI Deployment**: Deploy to TestPyPI first for verification
6. **PyPI Deployment**: Deploy to actual PyPI after TestPyPI success
7. **GitHub Release Creation**: Automatically create GitHub Release tag and release notes

### Deployment Process

```
Version change detected
    ↓
Test execution (abort if failed)
    ↓
Package build and validation
    ↓
TestPyPI deployment
    ↓
PyPI deployment
    ↓
GitHub Release creation
```

### Required Secrets

⚠️ **Must be configured:**

| Secret Name          | Description        | Creation Location                           |
| -------------------- | ------------------ | ------------------------------------------- |
| `PYPI_API_TOKEN`     | PyPI API token     | https://pypi.org/manage/account/token/      |
| `TESTPYPI_API_TOKEN` | TestPyPI API token | https://test.pypi.org/manage/account/token/ |

**Setup Instructions:** See `.github/workflows/SETUP.md`

### Required Permissions

- `contents: read` - Read code
- `contents: write` - Create GitHub Release
- TestPyPI/PyPI deployment permissions (managed via API Token)

### Semantic Version Check

The workflow only auto-deploys the following formats:

- ✅ `0.1.0`
- ✅ `1.2.3`
- ✅ `10.0.0`
- ❌ `0.1.0-dev` (pre-release, not auto-deployed)
- ❌ `0.1.0a1` (pre-release)
- ❌ `0.1` (format error)

### Usage Examples

#### Automatic Deployment (Semantic Version Change)

```bash
# Change version in pyproject.toml
version = "0.1.1"  # Semantic Version format

git add pyproject.toml
git commit -m "chore: Bump version to 0.1.1"
git push origin main

# Workflow automatically runs and deploys to PyPI
```

#### Manual Deployment

1. Go to GitHub Actions tab
2. Select "PyPI Release"
3. Click "Run workflow"
4. Select release type:
   - `patch`: 0.1.0 → 0.1.1
   - `minor`: 0.1.0 → 0.2.0
   - `major`: 0.1.0 → 1.0.0
5. Or enter a specific version: `0.2.5`

### Environment Protection Rules (Recommended)

You can set up pre-deployment approval using GitHub Environments:

1. Settings → Environments
2. Create `testpypi`, `pypi` environments
3. Set required reviewers (optional)

This allows you to require approval before deployment.

### Troubleshooting

#### Deployment Not Running

- Verify Semantic Version format (X.Y.Z)
- Verify `PYPI_API_TOKEN`, `TESTPYPI_API_TOKEN` Secrets are configured
- Check GitHub Actions logs for error messages

#### Deployment Aborted Due to Test Failure

- Run tests locally: `rye run pytest tests/ -v`
- Ensure all tests pass

---

## create-release.yml

Manually create a GitHub Release without deploying to PyPI.

### Trigger

**Manual Trigger Only**:
- Execute via `workflow_dispatch` from GitHub Actions UI
- Requires version input (e.g., `0.2.0`)

### Usage

1. Go to GitHub repository → **Actions** tab
2. Select "Create GitHub Release"
3. Click "Run workflow"
4. Enter version number (e.g., `0.2.0`)
5. Optionally enter custom title and release notes
6. Execute

### Inputs

| Input     | Description                                    | Required | Default                             |
| --------- | ---------------------------------------------- | -------- | ----------------------------------- |
| `version` | Version to release (e.g., `0.2.0`)            | ✅ Yes   | -                                   |
| `title`   | Release title                                  | ❌ No    | `Release v{version}`                 |
| `notes`   | Release notes (markdown supported)             | ❌ No    | Auto-generated installation notes    |

### Example

```bash
# Manual workflow dispatch
# Version: 0.2.0
# Title: (default) "Release v0.2.0"
# Notes: (auto-generated)
```

### When to Use

- ✅ Create release after manual PyPI deployment
- ✅ Create release for pre-release versions
- ✅ Create release with custom notes
- ✅ Create release without deploying to PyPI

### Permissions

- `contents: write` - Required to create GitHub Release

---

## Lock File Management

Dependency lock files (`requirements.lock`, `requirements-dev.lock`) are updated manually by developers.

### How to Update Lock Files

```bash
# Sync dependencies and update lock files
rye sync
rye lock

# Review changes
git diff requirements*.lock

# Commit changes
git add requirements.lock requirements-dev.lock
git commit -m "chore: Update lock files"
```

### When to Update

- When dependency versions change in `pyproject.toml`
- When adding new dependencies
- When removing existing dependencies
- When lock files change after running `rye sync`

---

## General Considerations

### Advantages

- ✅ Prevents mistakes through automation
- ✅ Consistent deployment process
- ✅ Easy to track changes
- ✅ Manual lock file management allows clear visibility into dependency changes

### Warnings

- ⚠️ Only Semantic Versions are auto-deployed (pre-releases require manual deployment)
- ⚠️ Secrets must be configured (when using `pypi-release.yml`)
- ⚠️ Packages cannot be deleted from PyPI after deployment (version update required)
- ⚠️ Lock files must be updated manually, so care is needed when changing dependencies

### Potential Improvements

1. **Slack/Discord notification integration**
2. **Dependabot automatic updates**
3. **Security scanning integration** (`rye audit`)
4. **Multi-Python version testing**
