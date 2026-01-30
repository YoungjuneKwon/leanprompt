# GitHub Actions for PyPI Deployment

This directory contains GitHub Actions workflows for automatically deploying the LeanPrompt package to PyPI.

## Workflows

### `deploy-to-pypi.yml`

Automatically deploys to PyPI when changes are made to the `leanprompt/` directory or related files on the main branch. Also supports manual triggering.

#### Triggers

1. **Automatic**: Push to `main` branch with changes in:
   - `leanprompt/**`
   - `setup.py`
   - `requirements.txt`
   - `README.md`
   - `LICENSE`

2. **Manual**: Can be triggered from GitHub Actions UI with optional reason

#### Setup Required

1. **Repository Secrets**:
   - `PYPI_TOKEN`: Your PyPI API token for package uploads

2. **GitHub Token Permissions**:
   - The workflow uses `GITHUB_TOKEN` to create releases
   - Ensure the repository settings allow GitHub Actions to create releases

#### Workflow Steps

1. **Version Detection**: Extracts version from `setup.py`
2. **Version Check**: Verifies if version already exists on PyPI
3. **Build**: Creates source and wheel distributions
4. **Deploy**: Uploads to PyPI if version is new
5. **Release**: Creates GitHub release tag

#### Usage

**Automatic Deployment**:
```bash
# Make changes to any of the tracked files
git add leanprompt/core.py
git commit -m "Update core functionality"
git push origin main
```

**Manual Deployment**:
1. Go to repository's Actions tab
2. Select "Deploy to PyPI" workflow
3. Click "Run workflow"
4. Optional: Add a reason for deployment

#### Version Management

- The workflow automatically checks if the version already exists on PyPI
- If version exists, deployment is skipped to avoid conflicts
- To deploy a new version, update the version in `setup.py`

#### Files

- `.github/workflows/deploy-to-pypi.yml`: Main workflow file
- `.github/scripts/get_version.py`: Helper script to extract version from setup.py

## Security Notes

- The PyPI token is stored as a repository secret and never exposed
- The workflow only runs on main branch to prevent unauthorized deployments
- Version checking prevents accidental overwrites