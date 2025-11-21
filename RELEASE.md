# Release Process

This document describes how to create and publish a new release of `acc-fwu`.

## Overview

The release process is largely automated via GitHub Actions. When you create a new GitHub Release, the CI/CD pipeline will:

1. Run all tests and linting
2. Perform security scans (Bandit, Snyk)
3. Build distribution packages
4. Sign the release with build attestation
5. Publish to PyPI automatically

## Prerequisites

Before creating a release, ensure:

- [ ] All tests pass locally (`pytest`)
- [ ] All linting passes (`flake8 .`)
- [ ] The code has been reviewed and merged to `main`
- [ ] You have maintainer access to the repository
- [ ] The PyPI environment is configured in GitHub (see [PyPI Setup](#pypi-setup))

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** (x.0.0): Incompatible API changes
- **MINOR** (0.x.0): New features, backwards compatible
- **PATCH** (0.0.x): Bug fixes, backwards compatible

The version is automatically determined from git tags using `setuptools_scm`.

## Creating a Release

### Step 1: Update Documentation

1. Update `README.md` with the new version's changes in the "Summary of Changes" section
2. Commit and push these changes to `main`

```bash
git add README.md
git commit -m "docs: update changelog for v0.x.x release"
git push origin main
```

### Step 2: Create a Git Tag

Create an annotated tag following semantic versioning:

```bash
# For a patch release (bug fixes)
git tag -a v0.1.5 -m "Release v0.1.5"

# For a minor release (new features)
git tag -a v0.2.0 -m "Release v0.2.0"

# For a major release (breaking changes)
git tag -a v1.0.0 -m "Release v1.0.0"
```

Push the tag to GitHub:

```bash
git push origin v0.x.x
```

### Step 3: Create GitHub Release

1. Go to the [Releases page](https://github.com/johnybradshaw/acc-firewall_updater/releases)
2. Click **"Draft a new release"**
3. Select the tag you just created
4. Set the release title (e.g., `v0.1.5`)
5. Write release notes describing:
   - New features
   - Bug fixes
   - Breaking changes (if any)
   - Security fixes (if any)
6. Click **"Publish release"**

### Step 4: Verify the Release

After publishing:

1. Check the [Actions tab](https://github.com/johnybradshaw/acc-firewall_updater/actions) to ensure the workflow completes successfully
2. Verify the package is available on [PyPI](https://pypi.org/project/acc-fwu/)
3. Test the installation:

```bash
pip install --upgrade acc-fwu
acc-fwu --version
```

## Release Notes Template

```markdown
## What's Changed

### New Features
- Feature 1 description
- Feature 2 description

### Bug Fixes
- Fix 1 description
- Fix 2 description

### Security
- Security fix description (if any)

### Breaking Changes
- Breaking change description (if any)

### Dependencies
- Updated dependency X to version Y

**Full Changelog**: https://github.com/johnybradshaw/acc-firewall_updater/compare/v0.1.4...v0.1.5
```

## PyPI Setup

The project uses [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) for secure PyPI uploads without storing API tokens.

### Initial Setup (One-time)

1. Create an account on [PyPI](https://pypi.org/)
2. Create the project on PyPI (first upload must be manual)
3. Go to your project's settings on PyPI
4. Add a new "trusted publisher":
   - Repository: `johnybradshaw/acc-firewall_updater`
   - Workflow: `python-app.yml`
   - Environment: `pypi`
5. In GitHub repository settings, create an environment named `pypi` with the PyPI URL

### GitHub Environment Configuration

The `pypi` environment should be configured in GitHub:

1. Go to **Settings** > **Environments**
2. Create/edit the `pypi` environment
3. Set environment URL to `https://pypi.org/p/acc-fwu`
4. Optionally add protection rules (e.g., required reviewers)

## Manual Release (Emergency Only)

If the automated release fails, you can manually upload to PyPI:

```bash
# Build the package
python -m pip install build twine
python -m build

# Upload to PyPI (requires API token)
python -m twine upload dist/*
```

**Note**: Manual uploads bypass build attestation and are not recommended.

## Troubleshooting

### Release Workflow Fails

1. Check the [Actions tab](https://github.com/johnybradshaw/acc-firewall_updater/actions) for error details
2. Common issues:
   - Tests failing: Fix tests and create a new tag
   - Security scan failures: Address vulnerabilities first
   - PyPI authentication: Verify trusted publisher setup

### Package Not Appearing on PyPI

- Wait a few minutes; PyPI indexing can take time
- Check the workflow logs for upload errors
- Verify the `pypi` environment is correctly configured

### Version Mismatch

If the version on PyPI doesn't match the tag:

1. `setuptools_scm` derives version from git tags
2. Ensure you're building from the tagged commit
3. The tag must follow the format `v0.x.x`

## Security Considerations

- **Never** commit API tokens or secrets to the repository
- Use GitHub's trusted publishing for PyPI uploads
- All releases are signed with build attestation
- Security scans (Bandit, Snyk) run before every release

## Rollback

If a release has critical issues:

1. **Do not delete** the PyPI release (versions cannot be reused)
2. Create a new patch release with the fix
3. If necessary, [yank](https://pypi.org/help/#yanked) the problematic version on PyPI

```bash
# Create hotfix
git checkout -b hotfix/v0.1.6
# ... make fixes ...
git commit -m "fix: critical issue"
git checkout main
git merge hotfix/v0.1.6
git tag -a v0.1.6 -m "Hotfix release v0.1.6"
git push origin main v0.1.6
```

Then create a new GitHub release for v0.1.6.
