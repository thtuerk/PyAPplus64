import pathlib
import sys

sys.path.append('../src/')

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PyAPplus64'
copyright = '2023, Thomas Tuerk'
author = 'Thomas Tuerk'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',    
    'sphinx.ext.autosummary',
]

templates_path = ['_templates']
exclude_patterns = [] # type: ignore

language = 'de'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'nature'
# html_static_path = ['_static']

source_suffix = {
    '.rst': 'restructuredtext',
}

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    'papersize': 'a4paper',

    # The font size ('10pt', '11pt' or '12pt').
    # 'pointsize': '11pt',

    # Additional stuff for the LaTeX preamble.
    # 'preamble': PREAMBLE
}

autodoc_type_aliases = {
    'SqlValue': 'SqlValue'
}