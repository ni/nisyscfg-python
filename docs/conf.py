"""Sphinx Configuration File."""

import datetime
import pathlib
import tomllib

import autoapi.extension

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "autoapi.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

root_path = pathlib.Path(__file__).parent.parent
pyproj_file = root_path / "pyproject.toml"
with pyproj_file.open("rb") as file:
    proj_config = tomllib.load(file)

project = proj_config["project"]["name"]
company = "National Instruments"
copyright = f"2026-%Y, {company}"
if datetime.datetime.now().year == 2026:
    copyright = f"%Y, {company}"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
release = proj_config["project"]["version"]
version = ".".join(release.split(".")[:2])
description = proj_config["project"]["description"]


htmlhelp_basename = f"{project}doc"


# tell autoapi to doc the public options
autoapi_options = list(autoapi.extension._DEFAULT_OPTIONS)
autoapi_options.remove("private-members")  # note: remove this to include "_" members in docs
autoapi_dirs = [root_path / "src" / "nisyscfg"]
autoapi_type = "python"
autodoc_typehints = "description"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}


# -- Options for HTML output ----------------------------------------------


# The theme to use for HTML and HTML Help pages. See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": -1,
}

# Napoleon settings
napoleon_numpy_docstring = False
