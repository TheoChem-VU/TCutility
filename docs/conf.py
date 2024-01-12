import git
import pathlib as pl
import sys

sys.path.insert(0, str(pl.Path(__file__).parent.parent / "src" / "tcutility"))
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "TCutility"
copyright = "2024, TheoCheM VU Amsterdam"
author = "TheoCheM VU Amsterdam"

# get release information
repo = git.Repo("..")

tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
if len(tags) == 0:
    latest_tag = None
    release = "vUnknown"
else:
    latest_tag = tags[-1]
    release = latest_tag.name

print("Git data:")
print("\tRepository:    ", repo)
print("\tHeads:         ", repo.heads)
print("\tTags:          ", tags)
print("\tLatest Tag:    ", repr(latest_tag))
print("\tLatest Version:", release)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    # 'sphinx.ext.autosummary',
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


autodoc_default_options = {
    "autosummary": False,
}

modindex_common_prefix = ["tcutility."]

html_theme_options = {
    # "show_nav_level": 2,
    # "navigation_depth": 2,
    "navbar_end": ["star"],
    "navbar_center": [],
    "navbar_start": ["logo"],
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_favicon = "https://avatars.githubusercontent.com/u/119413491"
html_theme = "pydata_sphinx_theme"  # pip install pydata-sphinx-theme
html_static_path = ["_static"]
add_module_names = False

# custom variables
rst_epilog = f"""
.. |ProjectVersion| replace:: {release}
.. |cm-1| replace:: :math:`\\text{{cm}}^{-1}`
.. |kcal/mol| replace:: :math:`\\text{{kcal mol}}^{-1}`
.. |km/mol| replace:: :math:`\\text{{km mol}}^{-1}`
"""
