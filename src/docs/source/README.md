Generating the Sphinx HTML Page

1. Install all packages from requirements.txt (have to install pandoc package executable via conda or manually)
2. From the top level package folder run the command `sphinx-build -v -b html src/docs/source/ public`
3. The file will be located in the public folder. The file is named index.html
