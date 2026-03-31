# -*- mode: python ; coding: utf-8 -*-

"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
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
except ImportError or ModuleNotFoundError:
    pass

try:
    import pytest
    print("ERROR - successful pytest import indicates development environment is active. Halting build.")
    sys.exit(0)
except ImportError or ModuleNotFoundError:
    pass

"""
Creates code bundle for macOS distribution.

    cd build/mac/
    pyinstaller build_mac.spec --noconfirm

This script also excludes license-incompatible modules according to:
https://doc.qt.io/qt-6/qtmodules.html#gpl-licensed-addons

"""

# Activates filtering to exclude incompatible Qt directories and files.
do_filtering = True
version_str = "2.1.0"
appname = "HELPR"

build_dir = Path(os.getcwd())
repo_dir = build_dir.parent.parent.parent
app_dir = repo_dir.joinpath('gui/src/helprgui')
lib_dir = repo_dir.joinpath('src')
dist_dir = build_dir.joinpath(f'dist/{appname}')
internal_dir = dist_dir.joinpath('_internal')
pyside_dir = internal_dir.joinpath('PySide6')

print(f"Repo dir exists {repo_dir.exists()}: {repo_dir}")
print(f"App dir exists {app_dir.exists()}: {app_dir}")
print(f"Lib dir exists {lib_dir.exists()}: {lib_dir}")
print(f"Build dir exists {build_dir.exists()}: {build_dir}")


# GPL v3-only modules (MUST exclude - incompatible with HELPR's BSD license)
# See: https://doc.qt.io/qt-6/licensing.html and individual module pages
gpl_only_blacklist = [
    'QtCharts',
    'QtChartsQml',
    'QtCoAP',
    'DataVisualization',
    'QtDataVisualization',
    'QtDataVisualizationQml',
    'QtGraphs',
    'QtGrpc',
    'QtHttpServer',
    'Lottie',
    'MQTT',
    'NetworkAuthorization',
    'QtQuick3D',
    'QtQuick3DUtils',
    'QtQuick3DEffects',
    'QtQuick3DHelpers',
    'QtQuick3DRuntimeRender',
    'QtQuick3DAssetImport',
    'QtQuick3DAssetUtils',
    'QtQuick3DParticles',
    'QtQuick3DParticleEffects',
    'QtQuick3DPhysics',
    'Timeline',
    'QtQuickTimeline',
    'VirtualKeyboard',
    'QtVirtualKeyboard',
    'Wayland',
    'Qt5Compat',
]

# Additional modules excluded by project policy (not needed, reduces size/attack surface)
additional_blacklist = [
    'Scene3D',

    'QtRemoteObjects',
    'QtRemoteObjectsQml',
    'QtSensors',
    'QtSensorsQuick',
    'QtWebChannel',
    'QtWebSockets',
    'QtWebEngineCore',
    'QtWebEngineQuick',
    'QtWebEngineQuickDelegatesQml',

    'QtMultimedia',
    'QtMultimediaQuick',
    'Qt3DCore',
    'Qt3DLogic',
    'Qt3DRender',
    'Qt3DInput',
    'Qt3DAnimation',
    'Qt3DQuick',
    'Qt3DQuickRender',
    'Qt3DQuickExtras',
    'Qt3DQuickAnimation',
    'Qt3DQuickInput',
    'Qt3DQuickScene2D',
    'Qt3DExtras',
    'QtSpatialAudio',
    'QtScxml',
    'QtScxmlQml',
    'QtStateMachine',
    'QtStateMachineQml',
    'QtOpenGLWidgets',

    'QtLabsAnimation',
    'QtLabsSharedImage',
    'QtLabsWavefrontMesh',
    # QtLabsFolderListModel is required by QtQuickDialogs2QuickImpl (file dialogs)
    'QtLabsSettings',
    'QtLabsQmlModels',
]

pyside_dir_blacklist = gpl_only_blacklist + additional_blacklist

# Misc. dirs not caught by above, that should be removed
dirs_to_delete = [
    pyside_dir.joinpath('Qt/qml/Qt/labs/animation'),
    pyside_dir.joinpath('Qt/qml/Qt/labs/platform'),
    pyside_dir.joinpath('Qt/qml/Qt/labs/sharedimage'),
    pyside_dir.joinpath('Qt/qml/Qt/labs/wavefrontmesh'),
]


def filter_output_files(lst):
    """
    Excludes GPL-licensed Qt modules from the build.
    DO NOT DISABLE THIS - it ensures only license-compatible modules are included.

    Uses a blacklist approach: keep everything except known GPL-incompatible modules.
    """
    to_keep = []
    for (dest, source, kind) in lst:
        if 'DS_Store' in source:
            print("Skipping DS_Store file")
            continue

        fpath = Path(dest)
        parts = fpath.parts

        # Check against GPL module blacklist
        skip = False
        for entry in pyside_dir_blacklist:
            if entry in parts:
                skip = True
                break
        if skip:
            print(f"Excluding (GPL): {fpath}")
            continue

        # Exclude translations (not needed, reduces size)
        if 'PySide6' in dest and 'translations' in parts:
            print(f"Excluding (translations): {fpath}")
            continue

        # Exclude specific plugin dirs that aren't needed
        if 'PySide6' in dest and 'plugins' in parts:
            if 'platforminputcontexts' in parts or 'qmltooling' in parts:
                print(f"Excluding (plugin): {fpath}")
                continue

        to_keep.append((dest, source, kind))

    return to_keep


def post_build_cleanup():
    """Remove GPL-licensed modules that may have been pulled in by binary dependency analysis."""
    print('== POST-BUILD CLEANUP ==')

    # Delete specific directories
    for dirpath in dirs_to_delete:
        print(dirpath.as_posix())
        if dirpath.exists():
            try:
                shutil.rmtree(dirpath)
                print(f"Deleted {dirpath.as_posix()}")
            except OSError as e:
                print(f"Could not remove dir: {dirpath} - {e.strerror}")

    # Scan entire dist tree and remove anything matching blacklisted entries.
    def matches_blacklist(fpath):
        for entry in pyside_dir_blacklist:
            if entry in fpath.parts:
                return True
            stem = fpath.stem
            if entry in stem:
                return True
        return False

    for fpath in sorted(dist_dir.rglob('*'), reverse=True):
        if matches_blacklist(fpath) and fpath.exists():
            if fpath.is_dir():
                shutil.rmtree(fpath)
                print(f"Deleted dir: {fpath}")
            else:
                fpath.unlink()
                print(f"Deleted file: {fpath}")


res = Analysis(
    [app_dir.joinpath('main.py')],
    pathex=[
        app_dir,
        lib_dir,
    ],
    datas=[
        (app_dir.joinpath('ui'), 'ui/'),
        (app_dir.joinpath('ui/resources'), 'ui/resources/'),
        (app_dir.joinpath('hygu/ui'), 'hygu/ui/'),
        (app_dir.joinpath('hygu/resources'), 'hygu/resources/'),
        (app_dir.joinpath('assets'), 'assets/'),
        (lib_dir.joinpath('helpr/data'), 'data/'),
    ],
    binaries=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

if do_filtering:
    # empty PySide6 dir
    if dist_dir.exists():
        shutil.rmtree(dist_dir.as_posix())
    if pyside_dir.exists():
        shutil.rmtree(pyside_dir.as_posix())

    # filter based on above blacklists
    res.binaries = filter_output_files(res.binaries)
    res.datas = filter_output_files(res.datas)


pyz = PYZ(res.pure)

exe = EXE(
        pyz,
        res.scripts,
        [],
        exclude_binaries=True,
        name=f'{appname}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=f"{appname.lower()}.icns",
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity="Developer ID Application",
        entitlements_file="entitlements.plist",
)

coll = COLLECT(
        exe,
        res.binaries,
        res.zipfiles,
        res.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name=f'{appname}',
)

app = BUNDLE(
        coll,
        name=f'{appname}.app',
        icon="icon.icns",
        bundle_identifier=f"com.SandiaNationalLaboratories.{appname}",
        version=version_str,
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': f'{appname}',
                    'CFBundleTypeRole': 'Editor',
                    'CFBundleTypeIconFile': 'Icon.icns',
                    'LSItemContentTypes': ['public.hpr'],
                    'LSHandlerRank': 'Owner'
                }
            ]
        },
)

if do_filtering:
    post_build_cleanup()

# Spot-check that filtering was applied
assert pyside_dir.joinpath('Qt/qml/Qt').exists()
assert pyside_dir.joinpath('Qt/qml/QtCore').exists()
assert pyside_dir.joinpath('Qt/qml/QtQuick').exists()

assert not pyside_dir.joinpath('Qt/qml/QtQuick3D').exists()
assert not pyside_dir.joinpath('Qt/qml/QtCharts').exists()
assert not pyside_dir.joinpath('Qt/qml/QtQuick/Timeline').exists()

for item in pyside_dir_blacklist:
    fpath = pyside_dir.joinpath(item)
    assert not fpath.exists()

assert do_filtering

print('\a')  # terminal bell
print(f'== BUILD COMPLETE: {appname} {version_str} ==')
