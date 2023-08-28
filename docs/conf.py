# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys


current_dir = os.path.dirname(__file__)

target_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, target_dir)

target_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, target_dir)


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'TCutility'
copyright = '2023, TheoCheM VU Amsterdam'
author = 'TheoCheM VU Amsterdam'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    "sphinx.ext.autodoc",
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    # 'sphinx.ext.autosummary',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


autodoc_default_options = {
    'autosummary': False,
}

modindex_common_prefix = ['TCutility.']

html_theme_options = {
  "show_nav_level": 2,
  "navigation_depth": 2,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'  # pip install pydata-sphinx-theme
html_static_path = ['_static']


# custom variables
rst_epilog = f"""
.. |ProjectVersion| replace:: v{release}
"""
