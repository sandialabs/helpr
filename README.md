# Hydrogen Extremely Low Probability of Rupture (HELPR)
Hydrogen Extremely Low Probability of Rupture (HELPR) is a probabilistic tool
suite for safety assessment of natural gas assets containing hydrogen environments.

&nbsp;
## Copyright and License
The copyright language is available in the [COPYRIGHT.txt](./COPYRIGHT.txt) file.
The license, as well as terms and conditions, are available in the
[LICENSE.md](./LICENSE.md) file.

&nbsp;
## Contributing
The application comprises a frontend GUI and a backend module both written in Python.
Anyone who wants to contribute to the development of the open-source HELPR project
should refer to the details in the [CONTRIBUTING](./CONTRIBUTING.md) document.

&nbsp;
## Documentation
Documentation of the technical approach underlying HELPR as well as a user guide
for the GUI are under development.
Sphinx documentation of the Python backend module is available at <https://sandialabs.github.io/helpr/>.

&nbsp;
## Repository Layout
The HELPR repository includes both the Python frontend GUI and the backend module.
Application code is organized in directories in the git repository in the following way:

```
$
├───examples
├───gui
│    ├───src
│    │    └───helprgui
│    │         ├───assets
│    │         ├───forms
│    │         ├───hygu (submodule)
│    │         ├───models
│    │         ├───tests
│    │         └───ui
│    └───build
└───src
     ├───docs
     │     └───source
     ├───helpr
     │     ├───data
     │     ├───physics
     │     ├───tests
     │     │     ├───integration_tests
     │     │     ├───unit_tests
     │     │     └───verification_tests 
     │     └───utilities
     └───probabilistic
           ├───capabilities
           ├───examples
           └───tests
```

* `examples` - Demonstrations of HELPR capabilities through Jupyter notebooks
* `gui/src` - GUI module for distributable HELPR application
* `gui/src/helprgui/hygu` - submodule library containing generic GUI components (e.g. generic parameter classes)
* `gui/build` - Installer scripts to build GUI distribution for Windows and macOS systems
* `src/docs` - Sphinx documentation generation
* `src/helpr` - Python source code for physics and utilities calculations and associated capability tests
* `src/probabilistic` - Python source code for probabilistic capabilities
