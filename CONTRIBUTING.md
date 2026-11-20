# Contributing to nisyscfg-python

Contributions to **nisyscfg-python** are welcome from all!

**nisyscfg-python** is managed via [git](https://git-scm.com), with the canonical upstream
repository hosted on [GitHub](https://github.com/ni/nisyscfg-python/).

**nisyscfg-python** follows a pull-request model for development.  If you wish to
contribute, you will need to create a GitHub account, fork this project, push a
branch with your changes to your project, and then submit a pull request.

See [GitHub's official documentation](https://help.github.com/articles/using-pull-requests/) for more details.

# Getting Started

## Install the NI System Configuration driver

The package uses the NI System Configuration Runtime, which is installed with the
NI System Configuration driver. Download and install the driver for your
platform from the [NI downloads page](https://www.ni.com/downloads/).

The unit tests use mocks, so the driver isn't required to run them, but you
need it to check changes against real hardware.

## Set up Poetry

Install [Poetry](https://python-poetry.org/docs/#installation) (version 2.1 or
later) and Python 3.11 or later. From the repository root, select the Python
interpreter to use and install the project and its development dependencies:

```shell
poetry env use 3.11
poetry install
```

Run project commands in the Poetry environment with `poetry run`, for example:

```shell
poetry run python -c "import nisyscfg"
```

## Update the lock file

Dependencies are periodically updated by [Mend Renovate](https://www.mend.io/renovate/) PRs. Sometimes you need to update them sooner or add a new dependency.

When you change dependency declarations in `pyproject.toml`, regenerate
`poetry.lock` from the repository root and include the updated lock file in your
change:

```shell
poetry lock
poetry check --lock
```

If you intend to update dependencies to the latest versions allowed by the
existing constraints, use the [`poetry update` command](https://python-poetry.org/docs/cli/#update).

## Build the package

Build the source distribution and wheel from the repository root:

```shell
poetry build
```

The build artifacts are written to `dist/`.

# Testing

Pull requests run CI checks before they can be merged. These include workflow
validation, project analysis (style and type checks), Bandit security checks,
documentation generation, unit tests on Windows and Linux across the supported
Python versions, and a package build. Many of these checks can be run locally,
before you create your PR.

Run the unit tests and coverage report locally with:

```shell
poetry run pytest
```

Run the project style and type checks and the Bandit scan with:

```shell
poetry run ni-python-styleguide lint
poetry run mypy
poetry run pyright
poetry run bandit -c pyproject.toml -r src/
```

To check the Poetry configuration and lock file, run:

```shell
poetry check --lock
```

To build the documentation locally, install the optional docs dependencies and
run Sphinx with warnings treated as errors:

```shell
poetry install --with docs
poetry run sphinx-build docs docs/_build -b html -W
```

The generated HTML documentation is in `docs/_build/`.

# Contributing

After you've verified that you can successfully build and run unit tests for
**nisyscfg-python**, you may fork the repository and
begin contributing to to the project.

1. Write a failing test for the new feature / bugfix.
2. Make your change.
3. Verify all tests, including the new ones, pass.
4. Update CHANGELOG.md if applicable.
5. On GitHub, send a New pull request to the main repository's main branch. GitHub
   pull requests are the expected method of code collaboration on this project.

# Release Process

1. Make sure your worktree is clean and up to date with `main`. Decide the next
   semantic version and bump the package version in `pyproject.toml` before
   creating the release. For example, increment the patch version with:

   ```shell
   poetry version patch
   ```

   Use `poetry version minor` or `poetry version major` for those increments, or
   provide an explicit version with `poetry version <version>`. Check the
   resulting version with `poetry version`, then commit.

   Create a PR and merge the change to `main`.

2. Before release, confirm CI passes, including the unit-test matrix across
   supported Python versions and operating systems. Spot check the "latest"
   documentation at https://nisyscfg.readthedocs.io/en/latest/.

3. Create a GitHub Release from the commit on `main` that contains the version
   bump. Set the tag to the version with a `v` prefix (for example, version
   `1.2.3` uses tag `v1.2.3`), use the version as the release title, and use
   the corresponding `CHANGELOG.md` entries as the release description. Publish
   the release; creating or pushing a tag without publishing a GitHub Release
   does not trigger the publishing workflow.

4. Publishing the release runs the `Publish to PyPI` workflow, which validates
   the tag against `pyproject.toml`, runs the analysis and docs checks, builds
   the package, and, after an authorized reviewer approves the `pypi`
   deployment, publishes to PyPI using
   [Trusted Publishing](https://docs.pypi.org/trusted-publishers/).

5. Confirm the workflow completes successfully. It also opens a PR that bumps
   `main` to the next dev version (for example, `0.2.2.dev0`); review and merge it.

# Developer Certificate of Origin (DCO)

   Developer's Certificate of Origin 1.1

   By making a contribution to this project, I certify that:

   (a) The contribution was created in whole or in part by me and I
       have the right to submit it under the open source license
       indicated in the file; or

   (b) The contribution is based upon previous work that, to the best
       of my knowledge, is covered under an appropriate open source
       license and I have the right under that license to submit that
       work with modifications, whether created in whole or in part
       by me, under the same open source license (unless I am
       permitted to submit under a different license), as indicated
       in the file; or

   (c) The contribution was provided directly to me by some other
       person who certified (a), (b) or (c) and I have not modified
       it.

   (d) I understand and agree that this project and the contribution
       are public and that a record of the contribution (including all
       personal information I submit with it, including my sign-off) is
       maintained indefinitely and may be redistributed consistent with
       this project or the open source license(s) involved.

(taken from [developercertificate.org](https://developercertificate.org/))

See [LICENSE](https://github.com/ni/nisyscfg-python/blob/main/LICENSE)
for details about how **nisyscfg-python** is licensed.
