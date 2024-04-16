# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))


# -- Project information -----------------------------------------------------

project = 'helpr'
copyright = '2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).' +  \
            'Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains' + \
            'certain rights in this software'
author = 'Benjamin B. Schroeder, Cianan Sims, Benjamin R. Liu, Bailey Lucero, and Michael Devin'

# The full version, including alpha/beta/rc tags
release = '1.1.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx_design',
    'sphinx.ext.napoleon',
    'nbsphinx',
    'sphinx.ext.doctest',
    'nbsphinx_link',
]
autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
html_theme_path = ["_themes\sphinx_rtd_theme", ]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_logo = "_static/HELPR_app_icon.jpg"
html_theme_options = {'logo_only': True}

# Show text as python format
highlight_language = 'python3'
rst_prolog = """
.. role:: python(code)
   :language: python
"""

# Ensure function default definitions preserved as specified
autodoc_preserve_defaults = True