from PyInstaller.utils.hooks import collect_data_files

# Include the necessary data files for pkg_resources
datas = collect_data_files('pkg_resources')

# Add hiddenimports to ensure all necessary dependencies are included
hiddenimports = [
    'pkg_resources.py2_warn',
    'appdirs',
    'packaging',
    'packaging.version',
    'packaging.specifiers',
    'packaging.requirements',
    'packaging.markers',
    'setuptools.extern.six',
    'setuptools.extern.packaging',
]

