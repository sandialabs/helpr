from PyInstaller.utils.hooks import collect_data_files

# Collect all data files from jaraco.text
datas = collect_data_files('jaraco.text')

# Add any specific file that might be missing
datas += [
    # ('path/to/lorem/ipsum.txt', 'jaraco/text')
]
