# -*- mode: python ; coding: utf-8 -*-

"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""

import os
import shutil
import sys
from pathlib import Path

# Ensure dev environment is not active, as it contains many modules that must not be included in build.
try:
    import jupyter
    print("ERROR - successful Jupyter import indicates development environment is active. Halting build.")
    sys.exit(0)
except ImportError as err:
    pass

"""
Creates code bundle for Windows distribution.

$ cd installers/
$ pyinstaller .\helpr_win.spec --noconfirm

To test:
$ .\dist\HELPR\HELPR.exe

This script also excludes license-incompatible modules according to:
https://doc.qt.io/qt-6/qtmodules.html#gpl-licensed-addons

"""

# Specify included Qt directories and files to ensure incompatible (GPL) modules are excluded.
# Note (Cianan): can also delete the excluded modules from the PySide source directory, but the whitelist approach is more reliable.
do_filtering = True

pyside_dir_blacklist = [
    'QtCharts',
    'QtCoAP',
    'DataVisualization',
    'Lottie',
    'MQTT',
    'NetworkAuthorization',
    'QtQuick3D',
    'Timeline',
    'VirtualKeyboard',
    'Wayland',
    'Scene3D',
]

pyside_qml_subdir_whitelist = [
    'Qt',
    'Qt5Compat',
    'QtCore',
    'QtQml',
    'QtQuick',
    'QtTest',
]

qt_file_whitelist = [
    'opengl32sw.dll',
    'pyside6.abi3.dll',
    'pyside6qml.abi3.dll',

    'Qt6Concurrent.dll',
    'Qt6Core.dll',
    'Qt6Gui.dll',
    'Qt6Network.dll',

    'Qt6OpenGL.dll',
    'Qt6OpenGLWidgets.dll',

    'Qt6Pdf.dll',
    'Qt6Positioning.dll',
    'Qt6PositioningQuick.dll',
    'Qt6PrintSupport.dll',

    'Qt6Qml.dll',
    'Qt6QmlCore.dll',
    'Qt6QmlLocalStorage.dll',
    'Qt6QmlModels.dll',
    'Qt6QmlWorkerScript.dll',
    'Qt6QmlXmlListModel.dll',

    'Qt6Quick.dll',
    'Qt6QuickControls2.dll',
    'Qt6QuickControls2Impl.dll',

    'Qt6QuickDialogs2.dll',
    'Qt6QuickDialogs2QuickImpl.dll',
    'Qt6QuickDialogs2Utils.dll',

    'Qt6QuickLayouts.dll',
    'Qt6QuickParticles.dll',
    'Qt6QuickShapes.dll',
    'Qt6QuickTemplates2.dll',
    'Qt6QuickTest.dll',

    'Qt6ShaderTools.dll',
    'Qt6Sql.dll',
    'Qt6Svg.dll',
    'Qt6Test.dll',
    'Qt6Widgets.dll',

    'QtCore.pyd',
    'QtGui.pyd',
    'QtNetwork.pyd',
    'QtOpenGL.pyd',
    'QtOpenGLWidgets.pyd',
    'QtPrintSupport.pyd',
    'QtQml.pyd',
    'QtSvg.pyd',
    'QtWidgets.pyd',
]


def filter_output_files(lst):
    """
    Rebuilds file lists based on whitelists.
    DO NOT DISABLE THIS - it ensures only license-compatible modules are included.

    """
    to_keep = []
    for (dest, source, kind) in lst:
        if 'PySide6' in dest:
            fpath = Path(dest)
            parts = fpath.parts

            # For simplicity, check for main GPL modules first
            skip = False
            for entry in pyside_dir_blacklist:
                if entry in parts:
                    skip = True
                    break
            if skip:
                print(f"Excluding {fpath}")
                continue

            if 'translations' in parts:
                print(f"Excluding {fpath}")
                continue

            elif 'plugins' in parts:
                if 'platforminputcontexts' not in parts and 'qmltooling' not in parts:
                    to_keep.append((dest, source, kind))

            elif 'qml' in parts:
                # qml/ sub-directories
                for name in pyside_qml_subdir_whitelist:
                    if name in parts:
                        to_keep.append((dest, source, kind))

            else:
                # top-level DLLs and .pyd files
                if os.path.split(dest)[1] in qt_file_whitelist:
                    to_keep.append((dest, source, kind))
                else:
                    print(f"Excluding {fpath}")

        else:
            to_keep.append((dest, source, kind))

    return to_keep


block_cipher = None


res = Analysis(
        ['../HelprGui/main.py'],
        pathex=[
            '../HelprGui',
            '../../src'
        ],
        datas=[
            ('../HelprGui/ui_files/', 'ui_files/'),
            ('../HelprGui/assets/', 'assets/'),
        ],
        binaries=[],
        hiddenimports=[],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False,
)

if do_filtering:
    # empty PySide6 dir
    cwd = Path(os.getcwd())  # repo/
    pyside_dir = cwd.joinpath('dist/HELPR/PySide6')
    if pyside_dir.exists():
        shutil.rmtree(pyside_dir.as_posix())

    # filter based on above whitelists
    res.binaries = filter_output_files(res.binaries)
    res.datas = filter_output_files(res.datas)


pyz = PYZ(res.pure, res.zipped_data, cipher=block_cipher)

exe = EXE(
        pyz,
        res.scripts,
        [],
        exclude_binaries=True,
        name='HELPR',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        # console=True,
        console=False,
        icon="icon.ico",
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
)
coll = COLLECT(
        exe,
        res.binaries,
        res.zipfiles,
        res.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='HELPR',
)

# Spot-check that filtering was applied
assert pyside_dir.joinpath('Qt6Core.dll').exists()
assert pyside_dir.joinpath('qml/QtQuick/Layouts').exists()

assert not pyside_dir.joinpath('Qt6Charts.dll').exists()
assert not pyside_dir.joinpath('Qt6QuickTimeline.dll').exists()

assert not pyside_dir.joinpath('qml/QtQuick/Timeline').exists()
assert not pyside_dir.joinpath('QtCharts').exists()

assert do_filtering

