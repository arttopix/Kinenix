# Releasing to PyPI

`kinenix`, `kinenix-hub`, and `kinenix-worker` are released together with one version number. Users install them with:

```bash
pip install kinenix              # core engine and the kinenix CLI
pip install "kinenix[worker]"    # adds kinenix-worker
pip install "kinenix[hub]"       # adds kinenix-hub (the `kinenix hub` command)
```

`kinenix-studio` is not published yet.

Publishing runs in GitHub Actions ([`.github/workflows/release.yml`](../.github/workflows/release.yml)) with **PyPI Trusted Publishing**: PyPI trusts this repository's workflow directly, so no API token is stored anywhere.

---

## 1. One-time setup

### 1.1 Trusted publishers on PyPI

Sign in to https://pypi.org with the account that owns `kinenix`.

| Project | Where | Action |
| :--- | :--- | :--- |
| `kinenix` (exists) | Your projects, then `kinenix`, then **Manage**, then **Publishing** | Add a GitHub publisher |
| `kinenix-hub` (new) | Account menu, then **Publishing** (https://pypi.org/manage/account/publishing/) | Add a **pending** publisher with project name `kinenix-hub` |
| `kinenix-worker` (new) | Same page | Add a **pending** publisher with project name `kinenix-worker` |

Use these values:

| Field | Value |
| :--- | :--- |
| Owner | `arttopix` |
| Repository name | `Kinenix` |
| Workflow name | `release.yml` |
| Environment name | `pypi` for `kinenix` and `kinenix-hub`; **`pypi-worker`** for `kinenix-worker` |

A pending publisher turns into the project on the first successful upload.

`kinenix-worker` has its own environment because PyPI refuses a pending publisher whose owner, repository, workflow, and environment all match another pending publisher ("A pending trusted publisher matching this configuration has already been registered for a different project name"). The release workflow publishes it in a separate job (`pypi-worker`) that runs after `kinenix` and `kinenix-hub` are uploaded.

### 1.2 Trusted publishers on TestPyPI

Repeat 1.1 on https://test.pypi.org (a separate site with its own account), with environment name **`testpypi`** for `kinenix` and `kinenix-hub`, and **`testpypi-worker`** for `kinenix-worker`. Use it to try every release before the real one.

### 1.3 GitHub environments (recommended)

The workflow creates the `pypi`, `pypi-worker`, `testpypi`, and `testpypi-worker` environments on first use. To require approval before anything is published, open the repository **Settings**, then **Environments**, then **pypi** and **pypi-worker**, and add yourself under **Required reviewers**.

---

## 2. Making a release

Released version numbers can never be reused on PyPI or TestPyPI. If something is wrong after an upload, fix it and release the next version (for example `0.2.0b2`).

1. **Bump the version** in a pull request into `dev`. Change all of these to the same value; a test fails if they differ:
   - `__version__` in `kinenix-core/kinenix/__init__.py`, `kinenix-hub/kinenix_hub/__init__.py`, and `kinenix-worker/kinenix_worker/__init__.py`
   - `kinenix-hub>=` and `kinenix-worker>=` in the extras of `kinenix-core/pyproject.toml`
   - `kinenix>=` in the dependencies of `kinenix-hub/pyproject.toml` and `kinenix-worker/pyproject.toml`
2. **Merge `dev` into `main`** through the usual release pull request. CI builds the packages, checks their metadata, and installs them in a clean environment.
3. **Try it on TestPyPI:** in GitHub, open **Actions**, then **Release**, then **Run workflow** on `main`. When it finishes, check in a new virtual environment:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "kinenix[hub,worker]==0.2.0b1"
   kinenix --version
   kinenix-worker --version
   ```
4. **Publish to PyPI** by tagging `main`:
   ```bash
   git switch main && git pull
   git tag v0.2.0b1
   git push origin v0.2.0b1
   ```
   The workflow builds again, checks that the tag matches the package version, and publishes all three packages.
5. Check https://pypi.org/project/kinenix/, `kinenix-hub`, and `kinenix-worker`, then install from PyPI in a clean environment.

---

## 3. Upgrading an installation

```bash
pip install --upgrade "kinenix[hub]"      # or "kinenix[worker]"
```

On Windows, stop any running `kinenix hub` or `kinenix-worker` from that environment first. Windows locks the running `kinenix.exe`, so pip can remove the old version but fail to install the new one, leaving `kinenix` uninstalled. If that happens, stop the process and run the same command again. A folder named like `~inenix-...dist-info` left in `site-packages` by the failed attempt can be deleted.

On a Raspberry Pi running the systemd service: `sudo systemctl stop kinenix-worker`, upgrade, then `sudo systemctl start kinenix-worker`.

---

## 4. What the checks cover

| Check | Where |
| :--- | :--- |
| All packages build as wheel and sdist | CI `packages` job, release workflow |
| PyPI metadata and README render (`twine check --strict`) | CI `packages` job, release workflow |
| One shared version; tag equals `v` + version | `.github/scripts/check_release.py` |
| Siblings require the same version | `kinenix-core/tests/test_repository_rules.py` |
| `kinenix[hub,worker]` installs from the built files in a clean environment, and `kinenix`, `kinenix hub`, `kinenix-worker`, and the dashboard files work | CI `packages` job |
