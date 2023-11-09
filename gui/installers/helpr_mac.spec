# -*- mode: python ; coding: utf-8 -*-

"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""

import os
import sys
import shutil
from pathlib import Path

# Ensure dev environment is not active, as it contains many modules that must not be included in build.
try:
    import jupyter
    print("ERROR - successful Jupyter import indicates development environment is active. Halting build.")
    sys.exit(0)
except ImportError as err:
    pass

"""
Creates code bundle for macOS HELPR distribution.

This script also excludes license-incompatible modules according to:
https://doc.qt.io/qt-6/qtmodules.html#gpl-licensed-addons

"""

# Activates filtering to exclude incompatible Qt directories and files.
# Note (Cianan): can also delete the excluded modules from the PySide source dir?
do_filtering = True

cwd = Path(os.getcwd())  # repo/
dist_dir = cwd.joinpath('dist/HELPR')
pyside_dir = cwd.joinpath('dist/HELPR/PySide6')

# Final step verifies that these dirs don't exist in output
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

    'QtDataVisualization',
    'QtRemoteObjects',
    'QtSensors',
    'QtWebChannel',
    'QtWebSockets',
]

# items within PySide6 directory that must be included
pyside_whitelist = [
    'PySide6/QtCore.abi3.so',
    'PySide6/QtGui.abi3.so',
    'PySide6/QtNetwork.abi3.so',
    'PySide6/QtPrintSupport.abi3.so',
    'PySide6/QtQml.abi3.so',
    'PySide6/QtQuick.abi3.so',
    'PySide6/QtSvg.abi3.so',
    'PySide6/QtWidgets.abi3.so',

    'PySide6/Qt/qml/Qt/',
    'PySide6/Qt/qml/Qt5Compat/',
    'PySide6/Qt/qml/QtCore/',
    'PySide6/Qt/qml/QtQml/',
    'PySide6/Qt/qml/QtQuick/Controls/',
    'PySide6/Qt/qml/QtQuick/Dialogs/',
    'PySide6/Qt/qml/QtQuick/Effects/',
    'PySide6/Qt/qml/QtQuick/Layouts/',
    'PySide6/Qt/qml/QtQuick/LocalStorage/',
    'PySide6/Qt/qml/QtQuick/NativeStyle/',
    'PySide6/Qt/qml/QtQuick/Particles/',
    'PySide6/Qt/qml/QtQuick/Pdf/',
    'PySide6/Qt/qml/QtQuick/Scene2D/',
    'PySide6/Qt/qml/QtQuick/Shapes/',
    'PySide6/Qt/qml/QtQuick/Templates/',
    'PySide6/Qt/qml/QtQuick/tooling/',
    'PySide6/Qt/qml/QtQuick/Window/',
    'PySide6/Qt/qml/QtQuick/libqtquick2plugin.dylib',
    'PySide6/Qt/qml/QtQuick/plugins.qmltypes',
    'PySide6/Qt/qml/QtQuick/qmldir',
    # 'PySide6/Qt/qml/QtTest/',
]


# top-level items that must be included. Other top-level exe's beginning with 'Qt' are excluded.
toplevel_exe_whitelist = [
    'QtQuick',
    'QtGui',
    'QtCore',
    'QtConcurrent',
    'QtQml',
    'QtQmlModels',
    'QtWidgets',
    'QtSvg',
    'QtPositioning',
    'QtQuickControls2Impl',
    'QtQuickTemplates2',
    'QtQuickControls2',
    'QtQuickDialogs2QuickImpl',
    'QtPdf',
    'QtQuickTest',
    'QtTest',
    'QtPositioningQuick',
    'QtQuickDialogs2',
    'QtQuickLayouts',
    'QtQmlWorkerScript',
    'QtShaderTools',
    'QtSql',
    'QtQmlLocalStorage',
    'QtQmlCore',
    'QtQuickShapes',
    'QtPrintSupport',
    'QtQuickDialogs2Utils',

    'QtDBus',
    'QtNetwork',
    'QtOpenGL',
]


# top-level items that must be excluded
toplevel_qt_blacklist = [
    'QtMultimedia',
    'QtMultimediaQuick',
    'QtQuick3DRuntimeRender',
    'QtQuick3D',
    'QtQuick3DUtils',
    'QtQuick3DEffects',
    'Qt3DCore',
    'Qt3DLogic',
    'Qt3DRender',
    'Qt3DInput',
    'Qt3DAnimation',
    'QtRemoteObjectsQml',
    'QtRemoteObjects',
    'QtVirtualKeyboard',
    'QtLabsAnimation',
    'QtLabsSharedImage',
    'QtCharts',
    'QtOpenGLWidgets',
    'QtChartsQml',
    'QtWebEngineCore',
    'QtWebEngineQuick',
    'QtWebChannel',
    'QtDataVisualizationQml',
    'QtQuickTimeline',
    'Qt3DQuick',
    'Qt3DQuickRender',
    'QtSpatialAudio',
    'QtQuick3DHelpers',
    'Qt3DExtras',
    'Qt3DQuickExtras',
    'QtScxmlQml',
    'QtScxml',
    'QtQuick3DAssetImport',
    'QtQuick3DParticles',
    'QtWebEngineQuickDelegatesQml',
    'QtQuick3DAssetUtils',
    'QtLabsWavefrontMesh',
    'Qt3DQuickAnimation',
    'Qt3DQuickInput',
    'Qt3DQuickScene2D',
    'QtStateMachineQml',
    'QtStateMachine',
    'QtQmlXmlListModel',
    'QtQuickParticles',
    'QtQuick3DParticleEffects',
    'QtWebSockets',
    'QtSensors',
    'QtSensorsQuick',
    'QtLabsFolderListModel',
    'QtLabsSettings',
    'QtLabsQmlModels',
    'QtDataVisualization',
]


def filepath_whitelisted(filepath: str, whitelist: list):
    """ Checks if filepath is included in an item on whitelist. """
    for allowable in whitelist:
        if allowable in filepath or allowable == filepath:
            return True
    return False


def file_whitelisted(filepath: str, whitelist: list):
    """ Checks if file is included in an item on whitelist. """
    fp = Path(filepath)
    return fp.parts[0] in whitelist


def filter_output_files(lst):
    """
    Rebuilds file lists based on whitelists.
    DO NOT DISABLE THIS - it ensures only license-compatible modules are included.

    """
    print("Filtering output files...")
    to_keep = []
    for (dest, source, kind) in lst:
        if 'DS_Store' in source:
            print("Skipping DS_Store file")
            continue

        elif 'PySide6/Qt/plugins' in dest:
            allowables = ['generic', 'iconengines', 'imageformats', 'platforms', 'styles']
            if filepath_whitelisted(dest, allowables):
                to_keep.append((dest, source, kind))
                continue

        elif 'PySide6/Qt' in dest:  # includes Qt* files like PySide6/QtCore.abi3.so
            if filepath_whitelisted(dest, pyside_whitelist):
                to_keep.append((dest, source, kind))
                continue

        # filter top-level linux exe's.
        elif 'PySide6' not in dest and 'Qt' in dest:
            if file_whitelisted(dest, toplevel_exe_whitelist):
                to_keep.append((dest, source, kind))
                continue

        else:
            to_keep.append((dest, source, kind))

    print("Filtering complete!")
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

# Remove DS_Store files

if do_filtering:
    # empty PySide6 dir
    if dist_dir.exists():
        shutil.rmtree(dist_dir.as_posix())

    if pyside_dir.exists():
        shutil.rmtree(pyside_dir.as_posix())

    # filter based on above whitelists
    res.binaries = filter_output_files(res.binaries)
    res.datas = filter_output_files(res.datas)

pyz = PYZ(res.pure, res.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          res.scripts,
          [],
          exclude_binaries=True,
          name='HELPR',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon="helpr.icns",
          disable_windowed_traceback=False,
          # argv_emulation=False,
          target_arch=None,
          codesign_identity="Developer ID Application",
          entitlements_file="entitlements.plist")

coll = COLLECT(exe,
               res.binaries,
               res.zipfiles,
               res.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='HELPR')

app = BUNDLE(coll,
             name='HELPR.app',
             icon="icon.icns",  # Mac requires icns file
             bundle_identifier="com.SandiaNationalLaboratories.HELPR",
             version='1.0.0',
             info_plist={
                 'NSPrincipalClass': 'NSApplication',
                 'NSAppleScriptEnabled': False,
                 'CFBundleDocumentTypes': [
                     {
                         'CFBundleTypeName': 'HELPR',
                         'CFBundleTypeRole': 'Editor',
                         'CFBundleTypeIconFile': 'Icon.icns',
                         # 'LSItemContentTypes': ['com.example.myformat'],
                         'LSItemContentTypes': ['public.hpr'],
                         'LSHandlerRank': 'Owner'
                     }
                 ]
             },
             )

# Spot-check that filtering was applied
assert pyside_dir.joinpath('Qt/qml/Qt').exists()
assert pyside_dir.joinpath('Qt/qml/QtCore').exists()
assert pyside_dir.joinpath('Qt/qml/QtQuick').exists()
assert not pyside_dir.joinpath('Qt/qml/QtQuick3D').exists()

for item in toplevel_qt_blacklist:
    fpath = dist_dir.joinpath(item)
    assert not fpath.exists()

pyside_qml_dir = pyside_dir.joinpath('qt', 'qml')
for item in pyside_dir_blacklist:
    fpath = pyside_qml_dir.joinpath(item)
    assert not fpath.exists()

assert do_filtering
