# Contributing to HELPR
This document describes the Hydrogen Extremely Low Probability of Rupture ("HELPR") application development.
The application comprises a frontend GUI a backend module both written in Python.
Step-by-step instructions will be added at a later date for setting up the enviroment to develop both the GUI and the backend.

# Changelog
For any significant changes made to the source code, it is expected that the change will be summarized in the [CHANGELOG](./CHANGELOG.md) document. Guidance and suggestions for how to best enter these changes in the changelog are [here](https://keepachangelog.com/en/1.0.0/). New changes should be added to the `[Unreleased]` section at the top of the file; these will be removed to a release section during the next public release.

&nbsp;
# Table of Contents
[A. Repository Layout](#repo-layout)

[B. GUI Development](#gui)

&nbsp;&nbsp; [B.1. Development Environment Setup](#gui-dev)

&nbsp;&nbsp; [B.2. Building the HELPR Application for Distribution](#gui-distr)
            
[C. Python HELPR Module Development](#py-dev)
        
[D. Python HELPR Usage](#py-usage)

<a name="repo-layout">&nbsp;</a>
# A. Repository Layout
Development of HELPR includes both the frontend Python GUI and the backend Python module.
Source code is organized as follows:

```
$
├───examples
├───gui
│    ├───HelprGui
│    │     ├───analyses
│    │     ├───assets
│    │     ├───parameters
│    │     ├───state
│    │     ├───tests
│    │     ├───ui_files
│    │     └───utils
│    └───installers
└───src
     ├───docs
     │     └───source
     ├───helpr
     │     ├───physics
     │     ├───tests
     │     │     ├───unit_tests
     │     │     └───verification_tests 
     │     └───utilities
     └───probabilistic
           ├───capabilities
           ├───examples
           └───tests
```

* `examples` - Demonstrations of HELPR capabilities through Jupyter notebooks
* `gui/HelprGui` - GUI for distributable HELPR application
* `gui/installers` - Installer scripts to build GUI distribution for Windows and macOS systems
* `src/docs` - Sphinx documentation generation
* `src/helpr` - Python source code for physics and utilities calculations and associated capability tests
* `src/probabilistic` - Python source code for probabilistic capabilities

<a name="gui">&nbsp;</a>
# B. Python GUI Development

This section describes how to set up a cross-platform development environment for the HELPR GUI.
It includes instructions for both developing and distributing the GUI application to users of Windows and macOS systems.

The GUI uses the Qt framework and PySide wrapper to implement the UI and to interface with the backend python HELPR library.
This document assumes familiarity with Python 3.8, the Qt framework, and basic JavaScript, which is used in Qt UI .qml files.

**NOTE: The Qt framework has a complex licensing situation.
The HELPR team must always verify that no incompatible modules are included in any release.**

### Nomenclature

The following terms and labels are used in this document:

    GUI         - The HELPR Graphical User Interface
    backend     - analysis code found in the HELPR module
    repo/       - path to the HELPR repository on your machine; e.g. P:/projects/helpr/repo
    installers/ - path to the GUI installers directory, (repo/gui/installers/)

<a name="gui-dev"></a>
## B.1. Development Environment Setup

### Step 1. Clone the Repository
The GUI and backend code reside within the HELPR repository.
Clone it via the gitlab instructions. Make sure to initialize the `probabilities` submodule as well.

### Step 2. Set Up a Python Development Environment
HELPR and the GUI require a standard Python 3.8 virtual environment.
See Python documentation for installing Python 3.8 and creating a new virtual environment.

For development, the following requirements file contains all required python modules.
Activate your virtualenv before installing these:

    python pip install -r repo/gui/requirements-dev.txt

**Warning**: the dev modules must NOT be bundled into a HELPR distribution.
Many of these modules have incompatible licenses for distribution and are used for development only.
For example, *jupyter* is used to verify the backend HELPR demos but should not be included in the distribution.
The bundling scripts include an import trap which halts the process if development modules are found.


### Step 3. Set Up a Separate Distribution Virtual Environment
A separate virtual environment must be created for building release-ready HELPR distributions.
This env contains only those modules necessary for the distribution and excludes development-only modules like *jupyter*.

    python pip install -r repo/gui/requirements.txt

### Step 4. Install Qt 6.5
*(Note: this step requires a free Qt account)*

Download the Qt online installer for Open Source Qt [here](https://www.qt.io/download-open-source).
Open the installer and select "Custom Installation". Modify the components as follows:

* Disable Qt Design studio
* Enable Qt 6.5.2
* Under Qt 6.5.2, enable only the following options:
    * (Windows) MSVC 64-bit
    * (Windows) MinGW 64-bit
    * Qt 5 compatibility module
    * Qt shader tools
* Under Qt 6.5.2 > Additional libraries, enable only the following:
    * Active Qt
    * Qt Image Formats
    * Qt PDF
    * Qt Positioning
    * Qt WebEngine
    * Qt WebView

Wait for the installer to finish.

*...an eternity later...*


### Step 5. Set Up Project in QtCreator
The QtCreator IDE is recommended for developing the UI .QML files and running the application during development.
After opening the `gui` directory in QtCreator, modify the project settings as follows:
1. Select the Projects tab (on the left) > Run
2. Add a new Python interpreter
3. In the interpreter settings, navigate to the python exe or symlink in your env.
4. Make sure the specified virtualenv is now selected for the project

**Careful**: QtCreator on macOS will try to follow the symlinked python when it is selected during the above steps.
If this occurs, the path will be set to `env/bin/python3.8` instead of to your virtualenv.
Revise this path to make sure the interpreter location points to the symlink file in the virtualenv, and NOT the systemwide parent bin/python.

It should be something like:

    /Users/cianan/projects/helpr/envs/py3.8-dev/bin/python3.8

And not:

    /Library/Frameworks/Python.Framework/Versions/3.8/Python

Once the project is set up, click the "Run" button to launch the Qt application.
Open the .qml files in `gui/ui_files` to edit the interface.

<a name="gui-distr"></a>
## B.2. Building the HELPR Application for Distribution

Building HELPR is a two-step process. First, the GUI components and python files are bundled via pyInstaller.
Next, the bundled files are incorporated into a platform-specific installer package.
These steps must be conducted on the platform for which a distribution is being created.
For example, the Intel-based macOS distribution must be built on an Intel-based macOS system.

Note that the .sh scripts used below include filters for excluding license-incompatible modules according to
the [Qt Docs](https://doc.qt.io/qt-6/qtmodules.html#gpl-licensed-addons).

<a name="distr-win"></a>
### HELPR for Windows

#### Requirements

The following tools are required to build HELPR on Windows:
* Inno Setup Compiler (https://jrsoftware.org/isdl.php)

#### Step 0. Update Version and Configuration
Update the HELPR versioning in the .spec file and within the application code.
Also check that the build configuration is set to `DEBUG=False` in the `gui_settings.py` file.

#### Step 1. Create the HELPR bundle
Update the version number in the .spec file before running pyinstaller.

    cd installers/
    pyinstaller .\helpr_win.spec --noconfirm

To test the bundle executable:

    cd installers/
    .\dist\HELPR\HELPR.exe

#### Step 2. Build the distribution setup file
1. Open Inno Setup compiler
2. Select helpr.iss script file
3. Click "compile"

This creates the HELPR installer .exe file (named "mysetup.exe") in the `installers/installer` directory.
This file can be renamed and distributed to end-users.


<a name="distr-mac"></a>
### HELPR for macOS
Mac-based distributions of HELPR follow the same basic build process;
however, there are some slight differences if building for Intel-based Mac vs. Apple-silicon Macs.
These differences are described below.

#### Requirements
Before attempting to build HELPR, verify that the following prerequisites are present:
* Xcode (https://developer.apple.com)
* Xcode command-lines tools (see below)
* An active Apple Developer account
* create an app-specific password for code-signing [here](https://www.qt.io/download-open-source)

It is important to **never accidentally include credentials in a git commit**.
Use this command to store your credentials on your machine:

    xcrun notarytool store-credentials "<keychain profile>"
                   --apple-id "AC_USERNAME"
                   --team-id <WWDRTeamID>
                   --password <secret_2FA_password>

Xcode command-line tools can be installed via the Terminal:

    xcode-select --install

#### Step 0. Update Version and Configuration
Update the HELPR version fields in the *.spec, distribution.xml, and *.sh files, and within the GUI.
Also check that the build configuration is set to `DEBUG=False` in the `gui_settings.py` file.

#### Step 1. Create the HELPR app bundle
Create the bundle via the .spec script in the `installers/dist` directory.

    cd installers/
    pyinstaller helpr_mac.spec --noconfirm

To verify the code-signed .app:

    codesign -v -vvv --deep --strict dist/HELPR.app

To test the bundle:

    cd installers/
    dist/HELPR/HELPR


#### Step 2. Build Mac package installer
Execute the script to build a .pkg installer from the HELPR.app file.
This script will also submit the pkg to Apple for notarization.

Note that this will copy the HELPR.app to a child dist/app/ directory.
This is done so that the bundle process can correctly identify it as a component.

Pass your codesign identity as the first argument and credential profile as the second.
Remember to surround entries with quotes "" if there are spaces.

    ./helpr_mac_create_pkg.sh "<Installer ID>" "<Profile>"

Notarization may take a long time to complete. To check on the status or poll for updates:

    xcrun notarytool info HELPR.app.zip --keychain-profile "<Profile>"
    xcrun notarytool wait HELPR.app.zip --keychain-profile "<Profile>"


### References

Qt QML Documentation <br>
https://doc.qt.io/qt-6/qmltypes.html

PyInstaller on signing macOS bundles<br>
https://pyinstaller.org/en/stable/feature-notes.html?highlight=identity#app-bundles

The Apple notarization process<br>
https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution
https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution/customizing_the_notarization_workflow

https://www.unix.com/man-page/osx/1/productbuild/

<a name="py-dev">&nbsp;</a>
# C. Python HELPR Module Development

<a name="py-usage">&nbsp;</a>
# D. Python HELPR Usage
