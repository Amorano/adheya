# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'Adheya'
year = datetime.now().year
copyright = u"%d Alex Morano " % year
author = 'amorano'
release = '0.4'

# -- General configuration ---------------------------------------------------
extensions = [
	'sphinx.ext.autodoc',
	'sphinx.ext.autosummary',
	'sphinx.ext.napoleon',
	'sphinx.ext.autosectionlabel',
	'sphinx.ext.todo',
	'sphinx.ext.viewcode',
	'sphinx.ext.extlinks',
	'sphinx.ext.intersphinx',
	'sphinx_rtd_theme',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
source_suffix = ".rst"
master_doc = "index"

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension Settings ------------------------------------------------------

autosummary_generate = False

extlinks = {
	'dearpygui': ('https://github.com/hoffstadt/DearPyGui/wiki/%s', 'dearpygui'),
}

intersphinx_mapping = {
	'python': ('https://docs.python.org/3.8', None),
	'curio': ('https://curio.readthedocs.io/en/latest', None),
}

autodoc_default_options = {
	'member-order': 'bysource',
	'show-inheritance': True,
}

autodoc_type_aliases = {
}

autodoc_mock_imports = ['dearpygui']

napoleon_numpy_docstring = False

html_context = {
	"display_github": True,
	"github_user": "amorano",
	"github_repo": "adheya",
	"github_version": "master",
	"conf_py_path": "/docs/",
}
