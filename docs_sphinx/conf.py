import os, sys
sys.path.insert(0, os.path.abspath('..'))

project = 'SmartBudget'
author = 'Косілов В.О.'
release = '1.0'
language = 'uk'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

html_theme = 'sphinx_rtd_theme'
autodoc_member_order = 'bysource'
