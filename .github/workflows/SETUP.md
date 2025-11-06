# GitHub Actions Environment Setup Guide

This document explains the configuration required for GitHub Actions workflows to function properly.

## Required Environment Variables and Secrets

### Automatically Available Secrets

The following secrets are automatically provided by GitHub and **require no additional setup**:

- ✅ `GITHUB_TOKEN` - Used for branch creation, commits, PR creation, and GitHub Release creation (automatically provided)

### Required Secrets for PyPI Deployment

The following Secrets **must be configured** to use the `pypi-release.yml` workflow:

| Secret Name          | Description                              | Required   | Setup Location               |
| -------------------- | ---------------------------------------- | ---------- | ---------------------------- |
| `PYPI_API_TOKEN`     | PyPI API token (for production PyPI)     | ✅ Required | Settings → Secrets → Actions |
| `TESTPYPI_API_TOKEN` | TestPyPI API token (for test deployment) | ✅ Required | Settings → Secrets → Actions |

**Setup Instructions:**
1. Go to GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Click "New repository secret"
3. Enter `PYPI_API_TOKEN` or `TESTPYPI_API_TOKEN` in the Name field
4. Enter the corresponding API token in the Value field (full string starting with `pypi-`)
5. Click "Add secret"

**Token Creation:**
- **PyPI Token**: https://pypi.org/manage/account/token/
- **TestPyPI Token**: https://test.pypi.org/manage/account/token/
- Scope: Select "Entire account"

### Optional Secrets (Notification Integration, etc.)

For extending workflows with additional features:

### Slack/Discord Notifications (Optional)

To receive notifications when deployment completes:

| Secret Name           | Description                |
| --------------------- | -------------------------- |
| `SLACK_WEBHOOK_URL`   | Slack Incoming Webhook URL |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL        |

## Workflow Permissions

The following permissions are required for workflows to function:

- ✅ `contents: read` - Read code (included in `pypi-release.yml`)
- ✅ `contents: write` - Create GitHub Release (included in `pypi-release.yml`)

## Workflow Testing

To test if workflows are functioning correctly:

1. **Manual Execution Test (PyPI Release):**
   - Go to GitHub repository → Actions tab
   - Select "PyPI Release"
   - Click "Run workflow"
   - Select release type (patch/minor/major) or enter version directly
   - Execute

2. **Automatic Trigger Test (Semantic Version Change):**
   ```bash
   # Change to Semantic Version in pyproject.toml
   # Example: 0.1.0 → 0.1.1
   git add pyproject.toml
   git commit -m "chore: Bump version to 0.1.1"
   git push origin main
   
   # Workflow automatically runs and deploys to PyPI
   ```

## Troubleshooting

### Workflow Not Running

1. **GitHub Actions Enabled**
   - Settings → Actions → General
   - Select "Allow all actions and reusable workflows"

2. **Workflow File Location**
   - Verify `.github/workflows/pypi-release.yml` path is correct

3. **Branch Protection Rules**
   - Settings → Branches
   - Check if there are any rules restricting workflow execution on `main` branch

### Permission Errors

- Check the `permissions` section in the workflow
- Verify repository Settings → Actions → General → "Workflow permissions"

### Deployment Failure

- Verify Semantic Version format (X.Y.Z)
- Verify `PYPI_API_TOKEN`, `TESTPYPI_API_TOKEN` Secrets are correctly configured
- Check GitHub Actions logs (click on execution result in Actions tab)
- Verify all tests pass

## Reference Materials

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Secrets Management](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)
